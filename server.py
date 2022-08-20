### SERVER SETTINGS ###
HOST = "127.0.0.1"
PORT = 8080
ADMIN_PASSWORD = b'$2b$12$SSNr7jlYSfN4CgiYoRakaeFF7yOa0kwpu4.e2irC8z4pfFjaoWPdO'  # "adminpls"

HANDSHAKER_ENABLED = True
HANDSHAKER_TIMEOUT = 360
HANDSHAKER_RESPOND_TIME = 1.5
### SERVER SETTINGS ###


# Import libaries.
from threading import Thread
import socket
import bcrypt 
import time
import os


# Connection informations.
ADDRESS = (HOST, int(PORT))
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.bind(ADDRESS)


# Important informations.
class Important:
    disconnect_connection_index = None
    clients_list = []
    threads_list = []


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

    class ToServer:
        text_message = ">client:text_message|" 
        disconnect = ">client:disconnect"
        set_username = ">client:username|"
        silent_set_username = ">client:silent_username|"
        handshake = ">client:handshake;"
        elevate = ">client:elevate|"
        user_degrad = "<server:degrad;"


    def SendMessageToAllClients(message):
        for idx, client in enumerate(Important.clients_list):
            try:
                client["connection"].send(f"{Messages.FromServer.user_message}{message}".encode())
            except Exception as error:
                if "10054" not in str(error): print(f"ERR │ {error}")


# Client object.
class Client:
    def __init__(self, connection, address, username="guest"):
        self.address     = address
        self.username    = username
        self.is_admin    = False 
        self.listIndex   = len(Important.clients_list)
        self.connection  = connection
        self.hsk_respond = False

        Important.clients_list.append({"obj": self, "username": username, "address": address, "connection": connection})
        try:
            self.connection.send(Messages.FromServer.connected.encode())
        except ConnectionResetError:
            print(f"ERR │ {self.username}@{self.address}: ConnectionResetError")
            Client.kick()
            Important.disconnect_connection_index = self.listIndex

    def _refreshIndex(self):
        self.listIndex = Important.clients_list.index({"obj": self, "username": self.username, "address": self.address, "connection": self.connection})

    def handle(self):
        while True:

            try:
                message = self.connection.recv(Messages.HEADER).decode(Messages.FORMAT)
            except:
                print(f"[-] │ {self.username} disconnected due an error.")
                Client.kick(self)
                return

            if message: 
                try:
                    self.connection.send(Messages.FromServer.message_received.encode())
                except ConnectionResetError:
                    print(f"ERR │ {self.username} <ConnectionResetError>.")
                    Client.kick(self)
                    return
                  
                _CommandsQueue = []
                _CommandsQueue = message.split(";")
                _CommandsQueue = [x for x in _CommandsQueue if x]

                if _CommandsQueue != []:

                    for message in _CommandsQueue:
                        if message.startswith(Messages.ToServer.silent_set_username):
                            new_username = message.split("|")[1]
                            self.username = new_username

                        # Disconnect.
                        if message.startswith(Messages.ToServer.disconnect):
                            print(f"[-] │ {self.username} disconnected.")
                            Client.kick(self)
                            break

                        # Normal text message.
                        elif Messages.ToServer.text_message in message:
                            print(f"    │ {'$' if self.is_admin else '@'}{self.username}: {message.replace(Messages.ToServer.text_message, '')}")
                            Messages.SendMessageToAllClients(str(message.replace(Messages.ToServer.text_message, "")+f"{'$' if self.is_admin else '@'}"+self.username))

                        # Set username.
                        elif message.startswith(Messages.ToServer.set_username):
                            new_username = message.replace(Messages.ToServer.set_username, "")

                            print(f"[r] │ {self.username} changed name to {new_username}")
                            self.username = new_username

                        # Admin elevation.
                        elif message.startswith(Messages.ToServer.elevate):
                            password = message.split("|")[1]
                            Client.elevation_request(self, password)

                        # Admin degradation.
                        elif message.startswith(Messages.ToServer.user_degrad.replace(";", "")):
                            self.is_admin = False
                            print(f"ADM │ {self.username}'s admin permissions has been removed.")

                        # Handshake.
                        elif message.startswith(Messages.ToServer.handshake.replace(";", "")):
                            self.hsk_respond = True

                        # Unknown message.
                        else:
                            self.connection.send(Messages.FromServer.unknown_command.encode())

    def kick(self):
        self.connection.close()
        Important.disconnect_connection_index = self.listIndex

    def handshake(self):
        try:
            self.connection.send(Messages.FromServer.handshake.encode())
        except ConnectionResetError:
            print(f"HSK │ {self.username}@{self.address}: ConnectionResetError")

        time.sleep(HANDSHAKER_RESPOND_TIME)
        if not self.hsk_respond:
            print(f"HSK │ {self.username}@{self.address}: Did not respond.")
            Client.kick(self)

    def elevation_request(self, password):
        if bcrypt.checkpw(password.encode(), ADMIN_PASSWORD):
            print(f"ADM │ {self.username} elevated to admin.")
            self.is_admin = True
            self.connection.send(Messages.FromServer.elevate_success.encode())
        
        else:
            print(f"ADM │ {self.username} unsuccessfully tried to elevate to admin.")
            self.connection.send(Messages.FromServer.elevate_failed.encode())

# Refresh self.listIndex in all clients.
def RefreshAllIndexes():
    for client in Important.clients_list:
        client["obj"]._refreshIndex()


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
def Handshaker():
    while True:
        time.sleep(HANDSHAKER_TIMEOUT)

        if Important.clients_list == []:
            continue

        print(f"HSK │ Handshake process started in all clients.")
        for idx, client in enumerate(Important.clients_list):
            try:
                client["obj"].handshake()

            except Exception as error:
                print(f"HSK │ @{client['username']}: Cannot send handshake to client.: {error}")
                client['obj'].kick()
                del Important.clients_list[idx]["obj"]
                Important.clients_list.pop(idx)


   

# === Main connection === #
def StartConnection():
    SERVER.listen()
    if HANDSHAKER_ENABLED: Thread(target=Handshaker, daemon=True).start()

    while True:
        conn, addr = SERVER.accept()
        client_object = Client(conn, addr)
        ClientHandler = Thread(target=client_object.handle, daemon=True)
        ClientHandler.start()
        Thread(target=ConnectionDeleter, daemon=True).start()
        print(f"[+] │ <{addr[0]}:{addr[1]}> Connected to server. | {len(Important.clients_list)}")



cls()
print("+++ │ Server started.")
print(f"[-] │ Server listening on: {HOST}:{PORT}\n    │")
StartConnection()
