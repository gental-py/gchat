from threading import Thread
import socket
import os 

def cls():
    os.system("cls || clear")

# Connection informations.
HOST = "127.0.0.1"
PORT = 8080
ADDRESS = (HOST, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDRESS)


# Important informations.
class Important:
    disconnect_connection_index = None
    clients_list = []


# Messages.
class Messages:
    HEADER = 2048
    FORMAT = "utf-8"

    class FromServer:
        message_received = "<server:message_received;"
        unknown_command = "<server:unknown_command;"
        user_message = "<server:user_message|"
        connected = "<server:connected;"

    class ToServer:
        text_message = ">client:text_message|" 
        disconnect = ">client:disconnect"
        set_username = ">client:username|"
        silent_set_username = ">client:silent_username|"


    def SendMessageToAllClients(message):
        for client in Important.clients_list:
            client["connection"].send(f"{Messages.FromServer.user_message}{message}".encode())

# Client object.
class Client:
    def __init__(self, connection, address, username="guest"):
        self.connection = connection
        self.address    = address
        self.username   = username
        self.listIndex  = len(Important.clients_list)

        Important.clients_list.append({"obj": self, "username": username, "address": address, "connection": connection})
        try:
            self.connection.send(Messages.FromServer.connected.encode())
        except ConnectionResetError:
            print(f"ERR │ {self.username}@{self.address}: ConnectionResetError")

    def handle(self):
        while True:

            try:
                message = self.connection.recv(Messages.HEADER).decode(Messages.FORMAT)
            except:
                print(f"[-] │ {self.username} disconnected due an error.")
                Client.kick(self)
                break

            if message: 
                self.connection.send(Messages.FromServer.message_received.encode())
                  
                # Disconnect.
                if message.startswith(Messages.ToServer.disconnect):
                    print(f"[-] │ {self.username} disconnected.")
                    Client.kick(self)
                    break

                # Normal text message.
                elif message.startswith(Messages.ToServer.text_message):
                    print(f"    │ {self.username}: {message.removeprefix(Messages.ToServer.text_message)}")
                    Messages.SendMessageToAllClients(str(message.removeprefix(Messages.ToServer.text_message)+"@"+self.username))

                # Set username.
                elif message.startswith(Messages.ToServer.set_username) or message.startswith(Messages.ToServer.silent_set_username):
                    new_username = message.replace(Messages.ToServer.set_username, "")

                    if message.startswith(Messages.ToServer.set_username):
                        print(f"[r] │ {self.username} changed name to {new_username}")
                    self.username = new_username

                # Unknown message.
                else:
                    self.connection.send(Messages.FromServer.unknown_command.encode())

    def kick(self):
        self.connection.close()
        Important.disconnect_connection_index = self.listIndex


# Delete disconnected clients.
def ConnectionDeleter():
    while True:
        if Important.disconnect_connection_index is not None:

            try:
                del Important.clients_list[Important.disconnect_connection_index]["obj"]
                Important.clients_list.pop(Important.disconnect_connection_index)
                Important.disconnect_connection_index = None
            except:
                pass

# === Main connection === #
def StartConnection():
    server.listen()

    while True:
        conn, addr = server.accept()
        client_object = Client(conn, addr)
        print(f"[+] │ New connection: {addr[0]}:{addr[1]} | {len(Important.clients_list)}")
        Thread(target=client_object.handle, daemon=True).start()
        Thread(target=ConnectionDeleter, daemon=True).start()



cls()
print("+++ │ Server started.")
print(f"[-] │ Server listening on: {HOST}:{PORT}\n    │")
StartConnection()
