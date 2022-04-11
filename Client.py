import os
import json
import socket
import threading
from tkinter import *
from tkinter import sys
from tkinter import scrolledtext
from tkinter import filedialog
from tkinter.ttk import Progressbar
from datetime import datetime
from pyautogui import alert
from playsound import playsound
from bs4 import BeautifulSoup
from urllib.request import urlopen

root = Tk()
root.geometry("800x400")
root.title("Client")
root.resizable(False, False)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
Header = 4096
Format = "utf-8"
file_bytes = None

path_downloads = "Downloads"
path_configs = "Configs Client"
path_notification = f"{path_configs}\\notification.mp3"

current_version = "5.0"

if not os.path.exists(path_downloads):
    os.mkdir(path_downloads)

if not os.path.exists(path_configs):
    os.mkdir(path_configs)

root.iconphoto(False, PhotoImage(file=f"{path_configs}\\icon.png"))

try:
    ConfigsText = {"ip": "0.0.0.0",
                   "port": 5000,
                   "pass": ""}

    Configs = open(f"{path_configs}\\default.json", "x")
    Configs.close()

    with open(f"{path_configs}\\default.json", "w") as f:
        json.dump(ConfigsText, f, indent=4)
        f.close()
except FileExistsError:
    try:
        with open(f"{path_configs}\\default.json", "r") as f:
            d = json.load(f)
            Server = d["ip"]
            Port = d["port"]
            Password = d["pass"]
            f.close()

        try:
            int(Port)
        except ValueError:
            alert(f"A Porta TCP ({Port}) Não é Valida", "Aviso")
            Port = ""

        if len(Password) > 49:
            alert(f"Senha Deve Ter Menos De 50 Caracteres ({len(Password)})", "Aviso")
            Password = ""

    except (KeyError, json.decoder.JSONDecodeError):
        alert("Uma Alteração Foi Encontrada No Arquivo. Reescrevendo 'default.json'", "Erro")

        ConfigsText = {"ip": "0.0.0.0",
                       "port": 5000,
                       "pass": ""}

        with open(f"{path_configs}\\default.json", "w") as f:
            json.dump(ConfigsText, f, indent=4)
            f.close()

        sys.exit()


def on_close():
    root.quit()


def get_current_date():
    get_hour = str(datetime.now().hour)
    get_min = str(datetime.now().minute)
    get_sec = str(datetime.now().second)
    time = [get_hour, get_min, get_sec]
    for x in range(len(time)):
        if len(time[x]) < 2:
            time[x] = f"0{time[x]}"

    return time


def log(text):
    with open(f"{path_configs}\\logClient.txt", "a") as l:
        date = datetime.now()
        logtext = f"[LOG | {date}] {text}\n"
        l.write(logtext)
        l.close()


def insert_text(text):
    scrolledLabelMsg.config(state=NORMAL)
    scrolledLabelMsg.insert(END, text)
    scrolledLabelMsg.see(END)
    scrolledLabelMsg.config(state=DISABLED)


def receive():
    global file_bytes
    try:
        while True:
            k = client.recv(Header).decode(Format)
            try:
                if k.startswith("msg@"):
                    log(f"[Recebeu]: {k}")

                    if root.wm_state() == "iconic":
                        playsound(path_notification)

                    insert_text(f"\n{k[4::]}")
                elif k.startswith("filelist@"):
                    filename = k[9::].split(":")
                    log(f"[Recebeu]: {filename}")

                    listbox_files.delete(0, END)
                    for x in filename:
                        listbox_files.insert(END, x)
                elif k.startswith("file@"):
                    filename, file_size = k[5::].split(":")

                    log(f"[Arquivo] Recebendo Arquivo ({filename})")
                    progress_value = 0

                    with open(f"{path_downloads}\\{filename}", "wb") as g:
                        file_bytes = bytes()

                        buttonDownload.config(state=DISABLED)
                        buttonSendFile.config(state=DISABLED)
                        buttonSendMsg.config(state=DISABLED)
                        inputMsg.config(state=DISABLED)

                        progress = 0
                        while True:
                            file_bytes = client.recv(Header)
                            try:
                                g.write(file_bytes)

                                progress += len(file_bytes)
                                progressbar["value"] = int(progress / int(file_size) * 100)

                                progress_value += len(file_bytes)
                                if progress_value >= int(file_size):
                                    progressbar["value"] = 0
                                    break
                            except UnicodeDecodeError:
                                log(f"[Unexpected Bytes] {file_bytes.decode(Format)}")

                        log(f"[Arquivo] Client Terminou Recebimento Do Arquivo ({filename})")
                        g.close()

                    buttonDownload.config(state=NORMAL)
                    buttonSendFile.config(state=NORMAL)
                    buttonSendMsg.config(state=NORMAL)
                    inputMsg.config(state=NORMAL)
            except UnicodeDecodeError:
                print(f"Unexpected bytes ({k})")
                log(f"Unexpected bytes ({k})")
    except (ConnectionRefusedError, ConnectionError, ConnectionResetError, ConnectionAbortedError):
        get_hour = str(datetime.now().hour)
        get_min = str(datetime.now().minute)
        get_sec = str(datetime.now().second)
        time = [get_hour, get_min, get_sec]
        for x in range(len(time)):
            if len(time[x]) < 2:
                time[x] = f"0{time[x]}"

        insert_text(f"\n[{time[0]}:{time[1]}:{time[2]}] Desconectado Do Servidor")
        alert("Desconectado Do Servidor", "Servidor")
        disconnect()
        root.title("Client")


# noinspection PyUnusedLocal
def connect(*e):
    global client
    server = inputIp.get()
    port = inputPort.get()
    if server != "" and port != "":
        try:
            try:
                addr = (server, int(port))
                client.connect(addr)
                client.send(current_version.encode(Format))

                is_compatible, server_version = client.recv(Header).decode(Format).split("@")
                if is_compatible == "-1":
                    insert_text(f"\n[ERRO] Versão Do Servidor Não é Compativel: {server_version}")

                if inputPass.get() is None or inputPass.get() == "":
                    client.send("None".encode(Format))
                else:
                    client.send(inputPass.get().encode(Format))

                try:
                    welcome_server_name = client.recv(Header).decode(Format)
                    if welcome_server_name.startswith("welcome@"):
                        welcome, server_name = welcome_server_name[8::].split(":")

                        alert(welcome, "Entrou")
                        log(f"Entrou No Servidor [{server}]")

                        inputIp.unbind("<Return>")
                        inputPass.unbind("<Return>")
                        inputPort.unbind("<Return>")

                        root.title("Client " + server_name)
                        labelIp.config(text=f"Host: {server}")
                        labelPort.config(text=f"Porta: {port}")

                        threading.Thread(target=receive).start()

                        time = get_current_date()
                        insert_text(f"\n[{time[0]}:{time[1]}:{time[2]}] Entrou No Servidor {server}")

                        buttonDisconnect.config(state=NORMAL)
                        buttonJoin.config(state=DISABLED)
                        buttonSendFile.config(state=NORMAL)
                        buttonDownload.config(state=NORMAL)
                except IndexError:
                    alert("Senha Não Corresponde Com o Servidor", "ERRO")
            except ValueError:
                alert("Porta Deve Ser Um Número")
        except (ConnectionRefusedError, OSError, TimeoutError):
            alert("Conexão Recusada ou Servidor Fechado", "Erro")
    else:
        alert("Forneça Um IP e Uma Porta Válida", "Erro")


# noinspection PyUnusedLocal
def send(*e):
    try:
        msg = inputMsg.get()
        if msg != "":
            log(f"[Eu] {msg}")
            if ".com" in msg:
                try:
                    if root.wm_state() == "iconic":
                        playsound("notification.mp3")

                    site = urlopen(msg)
                    bs = BeautifulSoup(site, features="html.parser")

                    insert_text("\n[Eu]: " + msg)
                    insert_text(f"\n{bs.find('title').text}")

                    client.send(f"msg@{msg}".encode(Format))
                    inputMsg.delete(0, END)
                except ValueError:
                    if root.wm_state() == "iconic":
                        playsound("notification.mp3")

                    insert_text("\n[Eu]: " + msg)
                    client.send(f"msg@{msg}".encode(Format))
                    inputMsg.delete(0, END)
            else:
                client.send(f"msg@{msg}".encode(Format))
                insert_text("\n[Eu]: " + msg)
                inputMsg.delete(0, END)
    except (NameError, OSError):
        alert("Conecte-se a Um Servidor Primeiro", "Erro")


def send_file():
    global file_bytes

    file = filedialog.askopenfilename(initialdir="C:\\")
    file_bytes = bytes()

    if file != "":
        buttonDownload.config(state=DISABLED)
        buttonSendMsg.config(state=DISABLED)
        buttonSendFile.config(state=DISABLED)
        inputMsg.config(state=DISABLED)

        file_size = os.stat(file).st_size
        filename = file.split("/")[len(file.split("/")) - 1]

        progress = 0

        # manda o nome e o tamanho do arquivo para o server
        client.send(f"file@{filename}:{file_size}".encode(Format))
        log(f"[Arquivo] Sinal De Envio Foi Mandado")

        with open(file, "rb") as g:
            try:
                while True:
                    file_bytes = g.read(Header)
                    client.send(file_bytes)

                    progress += len(file_bytes)
                    progressbar["value"] = int(progress / file_size * 100)

                    # se nao tiver mais nada para mandar ele quebra o while
                    if not file_bytes:
                        progressbar["value"] = 0
                        insert_text(f"\n[Arquivo] Arquivo ({filename}) Foi Mandado")
                        log(f"[Arquivo] Arquivo ({filename}) Foi Mandado")
                        break
            except (ConnectionRefusedError, ConnectionError, ConnectionResetError, ConnectionAbortedError):
                alert("A Conexão Foi Abortada", "ERRO")
                log("A Conexão Foi Abortada")
                progressbar["value"] = 0
                disconnect()

                buttonSendMsg.config(state=NORMAL)
                buttonSendFile.config(state=DISABLED)
                buttonDownload.config(state=DISABLED)
                inputMsg.config(state=NORMAL)

            g.close()

        file_bytes = None

        buttonSendMsg.config(state=NORMAL)
        buttonSendFile.config(state=NORMAL)
        buttonDownload.config(state=NORMAL)
        inputMsg.config(state=NORMAL)


def file_request():
    try:
        client.send(f"filerequest@{listbox_files.get(ACTIVE)}".encode(Format))
    except NameError:
        alert("Conecte-se a Um Servidor Primeiro", "Erro")


def disconnect():
    client.close()
    labelIp.config(text="Host:")
    labelPort.config(text="Porta:")
    root.title("Client")

    listbox_files.delete(0, END)
    progressbar["value"] = 0

    buttonDisconnect.config(state=DISABLED)
    buttonJoin.config(state=NORMAL)
    buttonSendFile.config(state=DISABLED)
    buttonDownload.config(state=DISABLED)

    inputIp.bind("<Return>", connect)
    inputPass.bind("<Return>", connect)
    inputPort.bind("<Return>", connect)


root.protocol("WM_DELETE_WINDOW", on_close)

labelIp = Label(root, text="Host:", font=("Arial", 10))
labelPort = Label(root, text="Porta:", font=("Arial", 10))
#
scrolledLabelMsg = scrolledtext.ScrolledText(root, width=69, height=22, font=("Arial", 10), state=DISABLED)
#
listbox_files = Listbox(root, width=23, height=7)
#
inputIp = Entry(root, width=20)
inputPort = Entry(root, width=20)
inputPass = Entry(root, width=20)
inputMsg = Entry(root, width=81)
#
buttonJoin = Button(root, text="Entrar", padx=43, pady=5, command=lambda: threading.Thread(target=connect).start())
buttonSendMsg = Button(root, text="Enviar", padx=25, pady=3, command=lambda: threading.Thread(target=send).start())
buttonSendFile = Button(root, text="Enviar Arquivo", padx=20, pady=3, command=lambda: threading.Thread(target=send_file).start(), state=DISABLED)
buttonDisconnect = Button(root, text="Desconectar", padx=26, pady=4, command=lambda: threading.Thread(target=disconnect).start(), state=DISABLED)
buttonDownload = Button(root, text="Baixar", padx=51, pady=5, command=file_request)
#
progressbar = Progressbar(root, orient=HORIZONTAL, length=126, mode="determinate")
#

scrolledLabelMsg.configure(state=NORMAL)
scrolledLabelMsg.insert(END, f"#__popServer_V{current_version}__")
scrolledLabelMsg.configure(state=DISABLED)

inputIp.insert(0, Server)
inputPort.insert(0, Port)
inputPass.insert(0, Password)
inputMsg.insert(0, "Mensagem")

inputMsg.bind("<Return>", send)
inputIp.bind("<Return>", connect)
inputPass.bind("<Return>", connect)
inputPort.bind("<Return>", connect)

# -----
labelIp.place(x=510, y=5)
labelPort.place(x=510, y=25)
# labelCons.place(x=698, y=170)
# -----
scrolledLabelMsg.place(x=3, y=3)
# -----
listbox_files.place(x=650, y=3)
# -----
inputIp.place(x=510, y=50)
inputPort.place(x=510, y=75)
inputPass.place(x=510, y=100)
inputMsg.place(x=3, y=372)
# -----
buttonJoin.place(x=510, y=125)
buttonSendMsg.place(x=510, y=367)
buttonSendFile.place(x=510, y=240)
buttonDisconnect.place(x=510, y=165)
buttonDownload.place(x=650, y=125)
# -----
progressbar.place(x=510, y=280)
# -----

root.mainloop()
# Made by: blackness (Muriel), ViniciusSirSpy (Vinicius)
# Feito por: blackness (Muriel), ViniciusSirSpy (Vinicius)
