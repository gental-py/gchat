# Import libaries.
from threading import Thread
import socket
import time
import os
import re


# Setup colors.
from modules.colors import *
colors_setup()


# Important switches.
class Important:
    _Username  = "guest"
    _Connected = False


# Minor functions.
def cls(): os.system("cls || clear")
def clearOneLine(line): print(f"\033[1A{' ' * (len(line)+5)}\033[A")
def OutputMesssage(message): print(message)


# Handle messages.
class Messages:
    HEADER = 2048
    FORMAT = "utf-8"
    _MessageReceived = False

    class FromServer:
        message_received = "<server:message_received;"
        unknown_command = "<server:unknown_command;"
        user_message = "<server:user_message|"
        connected = "<server:connected;"
        handshake = "<server:handshake;"

    class ToServer:
        text_message = ">client:text_message|" 
        disconnect = ">client:disconnect"
        set_username = ">client:username|"
        silent_set_username = ">client:silent_username|"
        handshake = ">client:handshake;"


    def SendMessage(msg):
        Socket.sendall(bytes(msg, Messages.FORMAT))


# Server listener.
def ServerMsgListener():
    global Socket
    while True:

        # Receive message from server.
        ServerMessage = Socket.recv(Messages.HEADER).decode(Messages.FORMAT)  

        # Commands Queue.
        _CommandsQueue = []
        _CommandsQueue = ServerMessage.split(";")
        _CommandsQueue = [x for x in _CommandsQueue if x]

        # Execute commands.
        # print(_CommandsQueue)
        if _CommandsQueue != []:
            for command in _CommandsQueue:

                # Server response.
                if command.startswith("<"):

                    # Connection confirmation.
                    if command == Messages.FromServer.connected.replace(";", ""):
                        Important._Connected = True

                    # Message received confirmation.
                    if command == Messages.FromServer.message_received:
                        Messages._MessageReceived = True

                    # Handshake auth process.
                    if command == Messages.FromServer.handshake.replace(";", ""):
                        Messages.SendMessage(Messages.ToServer.handshake)

                    # Another user message.
                    if command.startswith(Messages.FromServer.user_message):
                        content = command.replace(Messages.FromServer.user_message, "").split("@")
                        message = content[0]
                        username = content[1]
                        OutputMesssage(f"{purple}@{username}{bold}: {blue}{message}{end}")

                # Server text message.
                else:
                    OutputMesssage(command)


# Handle user input.
def HandleInput(user_input):

    # Commands.
    if user_input.startswith("/"):
        
        # Parse user input.
        user_input = CommandParse(user_input)

        # Disconnect user from server.
        if user_input[0] == "/disconnect":
            Messages.SendMessage(Messages.ToServer.disconnect)     
            print(f"{red}Disconnected.{end}")
            Important._Connected = False
        
        # Change username.
        if user_input[0] == "/setname":
            if len(user_input) != 2:
                print(f"{red}Error:{end} Command <setname> requires exactly 1 parameter.")
                return

            Messages.SendMessage(Messages.ToServer.set_username+user_input[1])
            print(f"{cyan}@{user_input[1]}{bold}: {green}New username set!{end}")
            Important._Username = user_input[1]


    # Text message.
    else:
        if not user_input.replace(" ","") == "":
            Messages.SendMessage(Messages.ToServer.text_message+user_input)


# Parse command.
def CommandParse(string):
    rv = []
    for match in re.finditer(r"('([^'\\]*(?:\\.[^'\\]*)*)'"
                             r'|"([^"\\]*(?:\\.[^"\\]*)*)"'
                             r'|\S+)\s*', string, re.S):
        arg = match.group().strip()
        if arg[:1] == arg[-1:] and arg[:1] in '"\'':
            arg = arg[1:-1].encode('ascii', 'backslashreplace') \
                .decode('unicode-escape')
        try:
            arg = type(string)(arg)
        except UnicodeError:
            pass
        rv.append(arg)

    return rv


# Connect client to server.
def Connect(host, port):
    try:
        Socket.connect((host, port))
        Thread(target=ServerMsgListener, daemon=True).start()
        time.sleep(0.3)

    except Exception as error:
        error = str(error)

        # Server unactive.
        if "10061" in error:
            error = "Server refused connection."  

        # Not socket.
        if "10038" in error:
            error = "Socket error."

        Menus.Main(error)
         

# === Main === #
PORT = 8080 
HOST = "127.0.0.1"
Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

class Menus:
    def Main(startmsg=""):
        global HOST, PORT, Socket
        output_host, output_port, message = "127.0.0.1", 8080, startmsg

        while True:

            cls()
            print(f"""
    {gray}╭────────• {bold}Gchat.{end}
    {gray}│
    {gray}├ {purple}Host{bold}: {red}{output_host}
    {gray}├ {purple}Port{bold}: {red}{output_port}
    {gray}│
    {gray}├ {red}{message}
    {gray}│""")

            user_action = input(f"    {gray}╰─ {blink}{bold}• {end}")
            user_action_parsed = CommandParse(user_action)

            if user_action_parsed[0] == "help":
                message = "Commands: connect, resock, help, host, port, exit"

            if user_action_parsed[0] == "resock":
                Socket.close()
                Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                message = "Recreated socket."

            if user_action_parsed[0] in ("connect", "conn", "c"):
                PORT = output_port
                HOST = output_host

                # Connect to server.
                Connect(HOST, PORT)
                Menus.Online()

            if user_action_parsed[0] == "exit":
                Socket.close()
                cls()
                exit()


    def Online():
        cls()
        if Important._Connected:
            print(f"{green}Connected to server.{end}")

            while Important._Connected:
                user_input = input("").replace("|", "")
                clearOneLine(user_input)
                HandleInput(user_input)
     
            else:
                Socket.close()    
                


Menus.Main()
    
