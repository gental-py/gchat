### SERVER SETTINGS ###
HOST = "127.0.0.1"
PORT = 8080

ADMINS_LIMIT = 0  # 0 = off
ADMIN_2FA = True
ADMIN_PASSWORD = b'$2b$12$SSNr7jlYSfN4CgiYoRakaeFF7yOa0kwpu4.e2irC8z4pfFjaoWPdO'  # "adminpls"

ENABLE_COLORS = True
WELCOME_MESSAGE = "Hi! (Deafult server's welcome message)"  # <username>, <host>, <port>

HANDSHAKER_ENABLED = True
HANDSHAKER_TIMEOUT = 360
HANDSHAKER_RESPOND_TIME = 1.5
### SERVER SETTINGS ###


# Import libaries.
import threading
import socket
import bcrypt 
import random
import time
import os

# Colors.
if ENABLE_COLORS:
    if not __import__("sys").stdout.isatty():
        for _ in dir():
            if isinstance(_, str) and _[0] != "_":
                locals()[_] = ""
    else:
        if __import__("platform").system() == "Windows":
            kernel32 = __import__("ctypes").windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            del kernel32

    end, red, gray, green, purple, orange, bold  = "\033[0m", "\033[1;31m", "\033[1;30m", "\033[1;32m", "\033[1;35m", "\033[1;33m", "\033[1;37m"
else:
    end, red, gray, green, purple, orange, bold = "", "", "", "", "", "", ""


# Connection informations.
ADDRESS = (HOST, int(PORT))
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.bind(ADDRESS)


# Important informations.
class Important:
    disconnect_connection_index = None
    clients_list = []
    threads_list = []
    admin_count  = 0 


# Clear screen function.
def cls(): os.system("cls || clear")


# Messages.
class Messages:
    HEADER = 2048
    FORMAT = "utf-8"

    class FromServer:
        message_received = "<server:message_received;"
        unknown_command = "<server:unknown_command;"
        user_message = "<server:user_message|"
        connected = "<server:connected;"
        handshake = "<server:handshake;"
        elevate_success = "<server:elevate_succes;"
        elevate_failed = "<server:elevate_failed;" 
        user_degrad = "<server:degrad;"
        welcome_message = "<server:welcome_msg|"

        # Errors.
        admins_limit_error = "<server:admins_limit_error;"
        permissions_error = "<server:permissions_error;"

    class ToServer:
        text_message = ">client:text_message|" 
        disconnect = ">client:disconnect"
        set_username = ">client:username|"
        silent_set_username = ">client:silent_username|"
        handshake = ">client:handshake;"
        elevate = ">client:elevate|"
        user_degrad = ">client:degrad;"
        code_2fa = ">client:2fa|"

        # Admin commands.
        ADMIN_server_address = ">client:server_address;"
        ADMIN_server_status = ">client:status;"
        ADMIN_initialize_hs = ">client:iniths;"


    def SendMessageToAllClients(message):
        for idx, client in enumerate(Important.clients_list):
            try:
                client["connection"].send(f"{Messages.FromServer.user_message}{message}".encode())
            except Exception as error:
                if "10054" not in str(error): print(f"{red}ERR {gray}│{end} {error}")


# Client object.
class Client:
    def __init__(self, connection, address, username="guest"):
        self.address     = address
        self.username    = username
        self.is_admin    = False 
        self.listIndex   = len(Important.clients_list)
        self.connection  = connection
        self.hsk_respond = False
        self.code_2fa    = ""

        Important.clients_list.append({"obj": self, "username": username, "address": address, "connection": connection})
        try:
            self.connection.send(Messages.FromServer.connected.encode())
            self.connection.send(str(Messages.FromServer.welcome_message+f"{WELCOME_MESSAGE.replace('<username>', self.username).replace('<host>', self.address[0]).replace('<port>', str(self.address[1]))}").encode())

        except ConnectionResetError:
            print(f"{red}ERR {gray}│{end} {bold}{self.username}@{self.address}{end}: {red}ConnectionResetError{end}")
            Client.kick()
            Important.disconnect_connection_index = self.listIndex

    def _refreshIndex(self):
        self.listIndex = Important.clients_list.index({"obj": self, "username": self.username, "address": self.address, "connection": self.connection})

    def handle(self):
        while True:

            try:
                message = self.connection.recv(Messages.HEADER).decode(Messages.FORMAT)

            except Exception as error:
                Client.kick(self)
                return

            if message: 
                try:
                    self.connection.send(Messages.FromServer.message_received.encode())
                except ConnectionResetError:
                    print(f"{red}ERR{end} {gray}│{end} {bold}{self.username}: {red}ConnectionResetError{end}")
                    Client.kick(self)
                    return
                  
                _CommandsQueue = []
                _CommandsQueue = message.split(";")
                _CommandsQueue = [x for x in _CommandsQueue if x]

                if _CommandsQueue != []:

                    for message in _CommandsQueue:

                        # Automatically set username
                        if message.startswith(Messages.ToServer.silent_set_username):
                            new_username = message.split("|")[1]
                            self.username = new_username
                            Important.clients_list[self.listIndex]["username"] = new_username

                        # == USER COMMANDS ==

                        # Disconnect.
                        elif message.startswith(Messages.ToServer.disconnect):
                            if self.is_admin: Important.admin_count -= 1
                            print(f"[{red}-{end}] {gray}│{end} {bold}{self.username} {red}disconnected.{end}")
                            Client.kick(self)
                            break

                        # Normal text message.
                        elif Messages.ToServer.text_message in message:
                            print(f"    {gray}│{end} {f'{red}${end}' if self.is_admin else f'{green}@{end}'}{self.username}: {bold}{message.replace(Messages.ToServer.text_message, '')}{end}")
                            Messages.SendMessageToAllClients(str(message.replace(Messages.ToServer.text_message, "")+f"{'$' if self.is_admin else '@'}"+self.username))

                        # Set username.
                        elif message.startswith(Messages.ToServer.set_username):
                            new_username  = message.replace(Messages.ToServer.set_username, "")
                            Important.clients_list[self.listIndex]["username"] = new_username
                            print(f"[{orange}r{end}] {gray}│{end} {bold}{self.username}{end} changed name to {bold}{new_username}{end}")
                            self.username = new_username

                        # Admin elevation.
                        elif message.startswith(Messages.ToServer.elevate):
                            if ADMINS_LIMIT != 0 and Important.admin_count >= ADMINS_LIMIT:
                                print(f"{purple}ADM {gray}│{end} {bold}{self.username} {red}Cannot become admin becouse of admins limit has been reached.{end}")
                                self.connection.send(Messages.FromServer.admins_limit_error.encode())

                            password = message.split("|")[1]
                            Client.elevation_request(self, password)

                        # Admin degradation.
                        elif message.startswith(Messages.ToServer.user_degrad.replace(";", "")):
                            self.is_admin = False
                            Important.admin_count -= 1
                            print(f"{purple}ADM {gray}│{end} {bold}{self.username}'s{end} {red}admin permissions has been removed.{end}")

                        # Handshake.
                        elif message.startswith(Messages.ToServer.handshake.replace(";", "")):
                            self.hsk_respond = True


                        # == ADMIN COMMANDS ==

                        # Give server address.
                        elif message.startswith(Messages.ToServer.ADMIN_server_address.replace(";", "")):
                            if not self.is_admin:
                                self.connection.send(Messages.FromServer.permissions_error.encode())
                                continue

                            self.connection.send(f"Server address: {HOST}:{PORT}".encode())

                        # Objects status.
                        elif message.startswith(Messages.ToServer.ADMIN_server_status.replace(";", "")):
                            if not self.is_admin:
                                self.connection.send(Messages.FromServer.permissions_error.encode())
                                continue

                            # Get informations.
                            threads_count = threading.active_count()-1
                            threads_list_count = len(Important.threads_list)
                            clients_list_count = len(Important.clients_list)
                            admins_count = Important.admin_count
                            th_list = threading.enumerate()

                            # Send informations.
                            self.connection.send(f"--- Status ---\nActive threads: {threads_count}\nThreads on list: {threads_list_count}\nThreads list: {th_list}\nClients on list: {clients_list_count}\nAdmins count: {admins_count}\n--- Settings ---\nAdmins limit: {ADMINS_LIMIT}\nAdmin 2FA: {ADMIN_2FA}\nEnable colors: {ENABLE_COLORS}\nWelcome message: {WELCOME_MESSAGE}\nHandshaker enbaled: {HANDSHAKER_ENABLED}\nHandshaker timeout: {HANDSHAKER_TIMEOUT} seconds\nHandshaker respond time: {HANDSHAKER_RESPOND_TIME} seconds".encode())

                        # Manual handshake initalization.
                        elif message == Messages.ToServer.ADMIN_initialize_hs.replace(";", ""):
                            if not self.is_admin:
                                self.connection.send(Messages.FromServer.permissions_error.encode())
                                continue

                            HandshakeAuth.manualInit(self.username)

                        # Unknown message.
                        else:
                            self.connection.send(str(Messages.FromServer.unknown_command).encode())

    def kick(self):
        if self.is_admin: Important.admin_count -= 1
        self.connection.close()
        Important.disconnect_connection_index = self.listIndex

    def handshake(self):
        try:
            self.connection.send(Messages.FromServer.handshake.encode())
        except ConnectionResetError:
            print(f"{green}HSK {gray}│{end} {bold}{self.username}@{self.address}: {red}ConnectionResetError{end}")

        time.sleep(HANDSHAKER_RESPOND_TIME)
        if not self.hsk_respond:
            print(f"{green}HSK {gray}│{end} {bold}{self.username}@{self.address}: {red}Did not respond.{end}")
            Client.kick(self)

    def elevation_request(self, password):
        def _generate2FAcode():
            c = ""
            for _ in range(4): c += str(random.randint(0,9))
            return c

        if bcrypt.checkpw(password.encode(), ADMIN_PASSWORD):
            if not ADMIN_2FA:
                print(f"{purple}ADM {gray}│{end} {bold}{self.username} {green}elevated to admin.{end}")
                self.is_admin = True
                Important.admin_count += 1
                self.connection.send(Messages.FromServer.elevate_success.encode())

            else:
                code = _generate2FAcode()
                print(f"{purple}2FA {gray}│{end} {bold}{self.username}'s code: {red}{code}{end}")
                self.connection.send("You have to write /2facode <code>. <code> is shown at the server's console.".encode())

                codeWrote, rounds = False, 0
                while not codeWrote:
                    try:
                        reader = self.connection.recv(Messages.HEADER).decode(Messages.FORMAT)

                    except Exception as error:
                        Client.kick(self)
                        return

                    if reader.startswith(Messages.ToServer.code_2fa): self.code_2fa = reader.split("|")[1]

                    time.sleep(1)
                    if self.code_2fa != "":  codeWrote = True
                    if rounds == 20:
                        print(f"{purple}2FA {gray}│{end} {bold}{self.username} {red}Did not respond with 2fa code for 20 seconds.{end}")
                        return
                    rounds += 1

                if self.code_2fa == code:
                    print(f"{purple}ADM {gray}│{end} {bold}{self.username} {green}elevated to admin.{end}")
                    self.is_admin = True
                    Important.admin_count += 1
                    self.connection.send(Messages.FromServer.elevate_success.encode())
                    self.code_2fa = ""

                else:
                    print(f"{purple}2FA {gray}│{end} {bold}{self.username} {red}Respond with incorrect 2fa code.{end}")
                    self.connection.send(Messages.FromServer.elevate_failed.encode())
                    self.code_2fa = ""
                    return   
        
        else:
            print(f"{purple}ADM {gray}│{end} {bold}{self.username} {red}unsuccessfully tried to elevate to admin.{end}")
            self.connection.send(Messages.FromServer.elevate_failed.encode())



# Refresh self.listIndex in all clients.
def RefreshAllIndexes():
    for client in Important.clients_list:  client["obj"]._refreshIndex()


# Delete disconnected clients.
def ConnectionDeleter():
    while True:
        if Important.disconnect_connection_index is not None:

            try:

                # Delete client object
                del Important.clients_list[Important.disconnect_connection_index]["obj"]
                Important.clients_list.pop(Important.disconnect_connection_index)
                Important.disconnect_connection_index = None


                # Refresh indexes for all clients objects.
                RefreshAllIndexes()
            except:
                pass
            

# Handshake.
class HandshakeAuth:
    def autoInit():
        while True:
            time.sleep(HANDSHAKER_TIMEOUT)
            HandshakeAuth.Handshaker()

    def manualInit(name="unknown"):
        print(f"{green}HSK {gray}│{end} Handshake process has been initialized by administrator: {name}.")
        HandshakeAuth.Handshaker()

    def Handshaker():
        if Important.clients_list == []:
            return

        print(f"{green}HSK {gray}│{end} Handshake process started in all clients.")
        for idx, client in enumerate(Important.clients_list):
            try:
                client["obj"].handshake()

            except Exception as error:
                print(f"{green}HSK {gray}│{end} {bold}@{client['username']}:{end}{red} Cannot send handshake to client: {end}{error}")
                client['obj'].kick()
                del Important.clients_list[idx]["obj"]
                Important.clients_list.pop(idx)


   

# === Main connection === #
def StartConnection():
    SERVER.listen()
    if HANDSHAKER_ENABLED: threading.Thread(target=HandshakeAuth.autoInit, daemon=True).start()
    threading.Thread(target=ConnectionDeleter, daemon=True).start()

    while True:
        conn, addr = SERVER.accept()
        client_object = Client(conn, addr)
        ClientHandler = threading.Thread(target=client_object.handle, daemon=True)
        ClientHandler.start()
        print(f"[{green}+{end}] {gray}│{end} <{bold}{addr[0]}:{addr[1]}{end}> {green}Connected to server.{end} | {purple}{len(Important.clients_list)}{end}")



cls()
print(f"{green}+++ {gray}│{end} {green}Server started.{end}")
print(f"[{green}*{end}] {gray}│{end} Server listening on: {bold}{HOST}{end}:{bold}{PORT}\n    {gray}│{end}")
StartConnection()
