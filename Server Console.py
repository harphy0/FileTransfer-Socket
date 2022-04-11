import socket
import threading
import os
import json
from time import sleep
from pyautogui import alert
from datetime import datetime
from tkinter import *
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter import sys

path_configs = "Configs Server"
path_upload = "Uploads"

try:
    if not os.path.exists(path_upload):
        os.mkdir(path_upload)

    if not os.path.exists(path_configs):
        os.mkdir(path_configs)

    ConfigsText = {"ip": "0.0.0.0",
                   "port": 5000,
                   "name": "",
                   "welcome": "",
                   "pass": "",
                   "conections": 0,
                   "gui": True}

    Configs = open(f"{path_configs}\\configs.json", "x")
    Configs.close()

    with open(f"{path_configs}\\configs.json", "w") as f:
        json.dump(ConfigsText, f, indent=4)
        f.close()

    alert("Um Arquivo 'configs.json' Foi Criado. Configure o Servidor Primeiro", "Aviso")
    sys.exit()
except FileExistsError:
    try:
        with open(f"{path_configs}\\configs.json", "r") as f:
            d = json.load(f)
            Server = d["ip"]
            Port = d["port"]
            ServerName = d["name"]
            Welcome = d["welcome"]
            Password = d["pass"]
            Max_connections = d["conections"]
            is_gui = d["gui"]

            f.close()

        try:
            int(Port)
        except ValueError:
            print(f"[Erro] A Porta TCP ({Port}) Não é Valida")

        try:
            int(Max_connections)
        except ValueError:
            print("[Erro] 'conections' Deve Ser Um Número Inteiro")

        not_allowed_char = ["\\", "/", "@", ":", ";"]
        for y in Password:
            if y in not_allowed_char:
                alert(f"Senha Contém Um Caractere Proibido ({y})", "Erro")

        if Welcome == "":
            Welcome = "Bem-Vindo"
        elif len(Welcome) > 70:
            print(f"[AVISO] Mensagem De Bem-Vindo Muito Longa ({len(Welcome)}) Maximo De 70 Caracteres!")
            Welcome = "Bem-Vindo"

        if ServerName == "":
            ServerName = Server
        elif len(ServerName) > 70:
            print(f"[AVISO] Nome Do Servidor Muito Longo ({len(ServerName)}) Maximo De 70 Caracteres!")
            ServerName = Server

        if len(Password) > 49:
            print(f"[ERRO] Senha Deve Ter Menos De 50 Caracteres ({len(Password)}) Interrompendo Servidor!")
            sleep(5)
            sys.exit()

        if Password == "":
            Password = "None"
    except (KeyError, json.decoder.JSONDecodeError):
        alert("Uma Alteração Foi Encontrada No Arquivo. Reescrevendo 'configs.json'", "ERRO")

        ConfigsText = {"ip": "0.0.0.0",
                       "port": 5000,
                       "name": "",
                       "welcome": "",
                       "pass": "",
                       "conections": 0,
                       "gui": True}

        with open(f"{path_configs}\\configs.json", "w") as f:
            json.dump(ConfigsText, f, indent=4)
            f.close()

        sys.exit()


def log(text):
    with open(f"{path_configs}\\logServer.txt", "a") as l:
        date = datetime.now()
        logtext = f"[LOG | {date}] {text}\n"
        l.write(logtext)
        l.close()


def check_filelist():
    last_check = os.listdir(path_upload)

    while True:
        if os.listdir(path_upload) != last_check:
            print("[AVISO] A lista de arquivos dos clients foi atualizada")
            for con in cons:
                cons[con].send(f"filelist@{':'.join(os.listdir(path_upload))}".encode(str_format))

        last_check = os.listdir(path_upload)
        sleep(1)


log(f"Servidor Iniciando")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
header = 4096
str_format = "utf-8"
cons = {}
connections = 0

current_version = "5.0"


class ServerGUI:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.title = ServerName
        self.connections = 0
        self.cons = {}

        self.scrolled_label = None
        self.listbox_connections = None
        self.label_connections = None
        self.button_send = None
        self.button_kick = None
        self.input_msg = None

        self.server_console = None

    def on_close(self):
        global is_gui

        close = messagebox.askokcancel("Fechar", "Você Quer Mesmo Fechar o Gui?")
        if close:
            is_gui = False
            threading.Thread(target=self.server_console.handle_server).start()
            sys.exit()

    def handle_server_gui(self):
        root = Tk()
        root.title(self.title)
        root.geometry(f"{self.width}x{self.height}")
        root.resizable(False, False)
        root.iconphoto(False, PhotoImage(file=f"{path_configs}\\icon.png"))

        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.scrolled_label = scrolledtext.ScrolledText(root, width=69, height=22, font=("Arial", 10), state=DISABLED)
        self.listbox_connections = Listbox(root, width=20, height=8)
        self.label_connections = Label(root, text=f"Conexões: {connections}", font=("Arial", 10))
        self.button_send = Button(root, text="Enviar", padx=40, pady=3, command=lambda: self.send_e())
        self.button_kick = Button(root, text="Kick", padx=10, command=lambda: self.kick_con())
        self.input_msg = Entry(root, width=80)

        self.input_msg.bind("<Return>", self.send_e)

        self.button_send.place(x=513, y=368)
        self.button_kick.place(x=513, y=162)
        self.input_msg.place(x=3, y=374)
        self.scrolled_label.place(x=3, y=3)
        self.listbox_connections.place(x=510, y=25)
        self.label_connections.place(x=533, y=3)

        self.insert_text(f"[Info] Ouvindo Host {Server}\n"
                         f"[Info] Porta TCP ({Port}) Sendo Usada")

        root.mainloop()

    def insert_text(self, text, *con):
        if not con:
            self.scrolled_label.config(state=NORMAL)
            self.scrolled_label.insert(END, text)
            self.scrolled_label.see(END)
            self.scrolled_label.config(state=DISABLED)
        else:
            self.label_connections.config(text=f"Conexões: {self.connections}")

            self.listbox_connections.delete(0, END)
            for x in cons:
                self.listbox_connections.insert(END, x)

    # noinspection PyUnusedLocal
    def send_e(self, *e):
        global connections
        inputs = self.input_msg.get()
        self.input_msg.delete(0, END)

        args = inputs.split(" ")

        commands = ["say", "kick", "cons", "update"]

        if args[0] not in commands:
            print(f"[Erro] '{args[0]}' Não é reconhecido como um comando")
            self.insert_text(f"\n[Erro] '{args[0]}' Não é reconhecido como um comando")

        elif inputs.startswith("say"):
            msg = inputs[4::]
            self.insert_text(f"\n[Server]: {msg}")

            for x in cons:
                cons[x].send(f"msg@[Server]: {msg}".encode(str_format))
        elif inputs.startswith("kick"):
            ip = args[1]

            try:
                for x in cons:
                    if cons[x] != cons[ip]:
                        cons[x].send(f"msg@[Server] {ip} Foi kickado".encode(str_format))
                    else:
                        cons[x].send(f"msg@[Server] Você foi kickado".encode(str_format))

                cons[ip].close()
                try:
                    del cons[ip]
                except KeyError:
                    pass
                finally:
                    connections = len(cons)
                    self.insert_text("", True)
            except (KeyError, OSError):
                print(f"[Erro] IP não reconhecido ({ip})")
                self.insert_text(f"\n[Erro] IP não reconhecido ({ip})")
        elif inputs.startswith("cons"):
            printlist = ["+-[IP]------------+\n"]
            for ip in cons:
                printlist.append(f"| {ip}\n")

            printlist.append("+------------------+")
            log("".join(printlist))

            self.insert_text("\n" + "".join(printlist))
        elif inputs.startswith("update"):
            self.server_console.send_filelist()

    def kick_con(self):
        global str_format
        global cons
        global connections

        ip = self.listbox_connections.get(ACTIVE)

        try:
            for x in cons:
                if cons[x] != cons[ip]:
                    cons[x].send(f"msg@[Server] {ip} Foi Kickado".encode(str_format))
                else:
                    cons[x].send(f"msg@[Server] Você Foi Kickado".encode(str_format))

            cons[ip].close()
            try:
                del cons[ip]
            except KeyError:
                pass
            finally:
                connections = len(cons)
                self.insert_text("", True)
        except (KeyError, OSError):
            print(f"[Erro] IP Não Reconhecido ({ip})")
            self.insert_text(f"\n[Erro] IP Não Reconhecido ({ip})")


class ServerConsole:
    def __init__(self, server, ip, port):
        self.server = server
        self.ip = ip
        self.port = port
        self.password = Password
        self.server_name = ServerName
        self.welcome = Welcome
        self.max_connections = Max_connections

        self.server_gui = None

    def start(self):
        global header
        global str_format
        global cons
        global connections

        try:
            try:
                self.server.bind((self.ip, int(self.port)))
            except OSError:
                print(f"Endereco IP ({self.ip}) Invalido")
                sys.exit()
        except ValueError:
            print("[ERRO] A Porta Utilizada Não é Valida")
            return None

        log("Servidor Está Iniciando...")
        log(f"Ouvindo Host {self.ip}")
        log(f"Porta TCP ({self.port}) Sendo Usada")

        self.server.listen(self.max_connections)

        # ------------------INIT PRINT
        print("+-----------------------------\n"
              f"| Ouvindo Host {self.ip}\n"
              f"| Porta TCP ({self.port}) Sendo Usada\n"
              "+-----------------------------\n"
              f"| Nome Do Servidor: {self.server_name}\n"
              f"| Mensagem De Bem-Vindo: {self.welcome}")

        if Password != "None":
            print(f"| Senha Do Servidor: {self.password}")
        else:
            print("| Nenhuma Senha Sendo Utilizada!")

        print("+-----------------------------\n")
        # -------------------END PRINT
        #
        # -------------------INITIATE THREADS
        if is_gui:
            threading.Thread(target=self.server_gui.handle_server_gui).start()
        else:
            threading.Thread(target=self.handle_server).start()

        threading.Thread(target=check_filelist).start()
        # -----------------------------------

        while True:
            con, addr = self.server.accept()

            client_version = con.recv(header).decode(str_format)
            if client_version != current_version:
                con.send(f"-1@{current_version}".encode(str_format))
                con.close()
            else:
                con.send(f"1@{current_version}".encode(str_format))

                if self.password != "None":
                    try:
                        con_pass = con.recv(header).decode(format)
                        if con_pass != self.password:
                            print(f"[AVISO] ({addr[0]}) Tentou Entrar No Servidor Com Uma Senha Não Valida")
                            log(f"{addr[0]} Tentou Entrar No Servidor Com Uma Senha Não Valida")
                            con.close()

                        elif con_pass == self.password:
                            threading.Thread(target=self.handle_client, args=(con, addr)).start()

                            cons[addr[0]] = con

                            con.send(f"welcome@{self.welcome}:{self.welcome}".encode(str_format))

                            if len(cons) > 1:
                                for x in cons:
                                    if cons[x] != con:
                                        cons[x].send(f"msg@[Server]: {addr[0]} Acabou De Entrar".encode(str_format))

                            connections = len(cons)
                    except (ConnectionRefusedError, ConnectionError, ConnectionResetError, ConnectionAbortedError):
                        con.close()
                        print("Uma Conexão Foi Tentada Mas o Client Abortou")
                        log("Uma Conexão Foi Tentada Mas o Client Abortou")
                elif self.password == "None":
                    con.recv(header)  # recv "None" password

                    threading.Thread(target=self.handle_client, args=(con, addr)).start()  # Start handle_client function

                    cons[addr[0]] = con
                    con.send(f"welcome@{self.welcome}:{self.welcome}".encode(str_format))

                    if len(cons) > 1:
                        for x in cons:
                            if cons[x] != con:
                                cons[x].send(f"msg@[Server]: {addr[0]} Acabou De Entrar".encode(str_format))

                    connections = len(cons)

    def handle_client(self, con, addr):
        global header
        global str_format
        global cons
        global connections

        ip = addr[0]

        print(f"[{ip}]: Conectado")
        print(f"Conexões: {connections}")

        log(f"[{ip}]: Conectado")
        log(f"Conexões: {connections}")

        self.send_filelist()  # Sends list of files in files_upload

        if is_gui:
            self.server_gui.insert_text(f"\n[{ip}]: Conectado")
            self.server_gui.insert_text(str(ip), True)

        while True:
            try:
                try:
                    msg = con.recv(header).decode(str_format)
                except UnicodeDecodeError as e:
                    print(e)

                if msg.startswith("file@"):
                    filename, file_size = msg[5::].split(":")

                    print(f"[Envio De Arquivo Confirmado] Por: {ip}\n"
                          f"                              File Size: {file_size} bytes\n"
                          f"                              Filename: {filename}")  # Information about the file being sent

                    log(f"[Envio De Arquivo Confirmado] Por: {ip}")
                    log(f"File Size: {file_size} bytes")
                    log(f"Filename: {filename}")

                    progress_value = 0

                    #  Begins to receive the file
                    with open(f"{path_upload}\\{filename}", "wb") as g:
                        try:
                            while True:
                                file_bytes = con.recv(header)
                                g.write(file_bytes)

                                progress_value += len(file_bytes)
                                if progress_value >= int(file_size):
                                    break
                        except UnicodeDecodeError as e:
                            print(f"[Erro] {e}")
                            break

                        log(f"Servidor Terminou Recebimento Do Arquivo ({filename})")
                        print(f"[Info] Servidor Terminou Recebimento Do Arquivo ({filename})")
                        print("[Info] Atualizando Lista De Arquivos Dos Clientes...")

                        g.close()
                    self.send_filelist()

                    for x in cons:
                        if cons[x] != con:
                            cons[x].send(f"msg@[Server] ({ip}) Enviou Um Arquivo Para o Servidor".encode(str_format))
                elif msg.startswith("msg@"):
                    print(f"[{ip}]: {msg[4::]}")
                    if is_gui:
                        self.server_gui.insert_text(f"\n[{ip}]: {msg[4::]}")

                    for x in cons:
                        if cons[x] != con:
                            cons[x].send(f"[{ip}]: {msg[4::]}".encode(str_format))
                elif msg.startswith("filerequest@"):
                    filename = msg[12::]
                    print(f"[Arquivo] Pedido De Arquivo ({filename}) Para: {ip}")
                    log(f"[Arquivo] Pedido De Arquivo ({filename}) Para: {ip}")

                    with open(f"{path_upload}\\{filename}", "rb") as file:
                        # manda o nome e o tamanho do arquivo pro client
                        file_size = os.stat(f"{path_upload}\\{filename}").st_size
                        con.send(f"file@{filename}:{file_size}".encode(str_format))

                        while True:
                            file_bytes = file.read(header)
                            con.send(file_bytes)

                            # se nao tiver mais nada para mandar ele quebra o while
                            if not file_bytes:
                                print(f"[Arquivo] Arquivo ({filename}) Foi Mandado")
                                log(f"[Arquivo] Arquivo ({filename}) Foi Mandado")
                                break

            except (ConnectionRefusedError, ConnectionError, ConnectionResetError, ConnectionAbortedError):
                print(f"[{ip}]: Desconectou-Se")
                log(f"[{ip}]: Desconectou-Se")

                if is_gui:
                    self.server_gui.insert_text(f"\n[{ip}]: Desconectou-Se")

                if len(cons) > 1:
                    for x in cons:
                        if cons[x] != con:
                            cons[x].send(f"msg@[{x}]: Desconectou-Se".encode(str_format))

                con.close()

                try:
                    del cons[ip]
                except KeyError:
                    pass
                finally:
                    connections = len(cons)
                    print(f"Conexões: {connections}")
                    log(f"Conexões: {connections}")

                    if is_gui:
                        self.server_gui.insert_text("", True)
                    break

    def handle_server(self):
        global header
        global str_format
        global cons
        global connections

        while True:
            inputs = input("[Server]: ")
            args = inputs.split(" ")
            log(inputs)

            commands = ["say", "kick", "cons", "update"]

            if args[0] not in commands:
                print(f"[ERRO] '{args[0]}' Não é reconhecido como um comando")
                log(f"'{args[0]}' Não é reconhecido como um comando")

            elif inputs.startswith("say"):
                msg = inputs[4:len(inputs)]
                for x in cons:
                    cons[x].send(f"[Server]: {msg.encode(str_format)}".encode(str_format))
            elif inputs.startswith("kick"):
                ip = args[1]

                try:
                    for x in cons:
                        if cons[x] != cons[ip]:
                            cons[x].send(f"[Server] {ip} Foi kickado".encode(str_format))
                        else:
                            cons[x].send(f"[Server] Você foi kickado".encode(str_format))

                    cons[ip].close()
                    try:
                        del cons[ip]
                    except KeyError:
                        pass
                except (KeyError, OSError):
                    print(f"[Erro] IP não reconhecido ({ip})")
                    log(f"IP não reconhecido ({ip})")
            elif inputs.startswith("cons"):
                printlist = ["+-[IP]------------+\n"]
                for ip in cons:
                    printlist.append(f"| {ip}\n")

                printlist.append("+-----------------+")
                print("".join(printlist))
                log("".join(printlist))
            elif inputs.startswith("update"):
                self.send_filelist()

    @staticmethod
    def send_filelist():
        global str_format
        global cons

        for con in cons:
            cons[con].send(f"filelist@{':'.join(os.listdir(path_upload))}".encode(str_format))

        print("[AVISO] A lista de arquivos dos clients foi atualizada")


server_gui = ServerGUI(650, 400)
server_console = ServerConsole(server_socket, Server, Port)

##############################################
server_console.server_gui = server_gui      ##
server_gui.server_console = server_console  ##
##############################################

server_console.start()

# Made by: blackness (Muriel), ViniciusSirSpy (Vinicius)
# Feito por: blackness (Muriel), ViniciusSirSpy (Vinicius)
