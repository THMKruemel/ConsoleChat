import socket
import mysql.connector
import threading
import json
import group_manager


class Server(group_manager.GroupManager):

    def __init__(self):

        db_password = input("Enter you db password to connect to the database: ")
        super().__init__(db_password)
        while True:
            port = input("Specify the port where the socket should run: ")
            try:
                self.port_to_int = int(port)
                if self.port_to_int < 65535:
                    break
            except ValueError as e:
                print(e)

        try:
            self.mydb = mysql.connector.connect(
                host="localhost",
                port=3308,
                user="root",
                passwd=f"{db_password}"
            )
        except mysql.connector.errors as e:
            print(e)

        self.mycursor = self.mydb.cursor(buffered=True)
        self.mycursor.execute("CREATE DATABASE IF NOT EXISTS consolechat")
        self.mycursor.execute("USE consolechat")
        self.mycursor.execute("CREATE TABLE IF NOT EXISTS Users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255), password VARCHAR(255), ip VARCHAR(255), port INT(255))")
        self.mycursor.execute("CREATE TABLE IF NOT EXISTS ChatHistory (id INT AUTO_INCREMENT PRIMARY KEY, receiver_id INT, sender_id INT, message VARCHAR(512))")
        self.mycursor.execute("CREATE TABLE IF NOT EXISTS GroupChats (group_id INT AUTO_INCREMENT PRIMARY KEY, group_name VARCHAR(255), admin_id INT)")
        self.mycursor.execute("CREATE TABLE IF NOT EXISTS GroupMembers (id INT AUTO_INCREMENT PRIMARY KEY, group_id INT, user_id INT)")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hostname = socket.gethostname()
        amount_clients = input("Specify how many clients can connect at the same time: ")
        print(self.hostname)
        try:
            print(socket.gethostbyname(self.hostname))
            self.server_address = ("192.168.66.58", self.port_to_int)
            self.server_socket.bind(self.server_address)
            self.server_socket.listen(int(amount_clients))
        except OSError as e:
            print(e)
        except ValueError as e:
            print(e)

        self.clients = {}
        self.client_id = {}

    def start_server(self):
        while True:
            client_socket, client_adress = self.server_socket.accept()
            print(f"Connection established from {client_adress}")
            self.clients[client_socket] = client_adress
            print(self.clients)

            handle_process = threading.Thread(target=self.handle_client, args=(client_socket, client_adress))
            handle_process.start()

    def handle_client(self, client_socket, client_adress):
        self.clients[client_socket] = client_adress
        print(self.clients)
        client_login = False

        while True:
            msg = client_socket.recv(1024)
            print(msg)

            print(f"Received message from {client_adress}: {msg.decode('utf-8')}")

            received_data = msg.decode('utf-8')
            if received_data.startswith("!signin"):
                signin_credentials = client_socket.recv(1024)
                if self.check_client_is_online(client_socket, signin_credentials):
                    signin_credentials_decoded = signin_credentials.decode("utf-8")
                    json_data = json.loads(signin_credentials_decoded)
                    print(json_data)
                    print("The received password is: ", json_data["password"])
                    print("The received username is: ", json_data["username"])
                    if self.check_login_credentials(json_data["username"], json_data["password"]):
                        try:
                            client_socket.send(bytes("!successful", "utf8"))
                        except BrokenPipeError:
                            print("Cannot send answer")
                        self.overwrite_client_adress(client_adress, json_data["username"])
                        client_id = self.get_user_id(json_data["username"])
                        lock = threading.Lock()
                        lock.acquire()
                        self.clients[client_id] = client_socket
                        self.client_id[client_socket] = client_id
                        lock.release()
                        client_login = True
                    else:
                        try:
                            client_socket.send(bytes("!login failed", "utf8"))
                        except BrokenPipeError:
                            print("Cannot send answer")
                else:
                    break

            if received_data.startswith("!register"):
                check_register_credentials = client_socket.recv(1024)
                if self.check_client_is_online(client_socket, check_register_credentials):
                    json_data = json.loads(check_register_credentials)
                    print(json_data)
                    if self.is_user_registered(json_data["username"]):
                        print("function is user registered reached")
                        try:
                            client_socket.send(bytes("!already taken", "utf8"))
                        except BrokenPipeError:
                            print("cannot send answer")
                    else:
                        self.register_in_db(json_data, client_adress)
                        try:
                            client_socket.send(bytes("!successful", "utf8"))
                        except BrokenPipeError:
                            print("Cannot send answer")
                        client_id = self.get_user_id(json_data["username"])
                        lock = threading.Lock()
                        lock.acquire()
                        self.clients[client_id] = client_socket
                        self.client_id[client_socket] = client_id
                        lock.release()
                        client_login = True
                else:
                    break

            print(received_data)
            if received_data.startswith("!chat") and client_login:
                message_partner = client_socket.recv(1024)
                if self.check_client_is_online(client_socket, message_partner):
                    if self.is_user_registered(message_partner):
                        try:
                            client_socket.send(bytes("!user exists", "utf8"))
                        except BrokenPipeError:
                            print("Cannot send answer")
                        chat_members = client_socket.recv(1024)

                        if self.check_client_is_online(client_socket, chat_members):

                            chat_members_decoded = chat_members.decode("utf-8")
                            chat_members_parts = chat_members_decoded.split("|")

                            target_username = chat_members_parts[0]
                            print(target_username)
                            username = chat_members_parts[1]
                            ids = self.get_chat_member_ids(target_username, username)
                            target_id = ids[0]
                            client_id = ids[1]
                            try:
                                client_socket.send(bytes(f"{target_id}|{client_id}", "utf8"))

                            except BrokenPipeError:
                                print("Cannot send answer")
                        else:
                            break
                    else:
                        try:
                            client_socket.send(bytes("!user doesnt exist", "utf8"))
                        except BrokenPipeError:
                            print("Cannot send answer")
                        continue
                else:
                    break

                print("keys: ", self.client_id.keys())
                print("Client socket: ", client_socket)
                print("Client socket in dict: ", client_socket)

                target_id = client_socket.recv(256)
                target_id_decoded = str(target_id.decode("utf-8")).strip("(),")
                print("target id:", target_id_decoded)
                chat_history = self.get_chat_history(self.client_id[client_socket], target_id_decoded)
                client_socket.send(bytes(str(chat_history), "utf8"))

                while True:
                    msg = client_socket.recv(512)
                    msg_decoded = msg.decode("utf-8")
                    parts = msg_decoded.split("|")
                    if msg_decoded == "!exit":
                        break
                    if self.check_client_is_online(client_socket, msg):
                        if len(parts) != 3:
                            client_socket.close()
                        receiver_id = int(parts[0].strip("()").rstrip(','))
                        client_id = int(parts[1].strip("()").rstrip(','))
                        message = parts[2]
                        self.insert_chat_message(receiver_id, client_id, message)

                continue

            if received_data.startswith("!create_group") and client_login:
                print("machen")
                group_name = client_socket.recv(512)
                group_name_decoded = group_name.decode("utf-8")
                print(group_name_decoded, "in funktion")
                admin_id = client_socket.recv(512)
                admin_id_decoded = admin_id.decode("utf-8")
                print(admin_id_decoded)
                # das print wird nicht mehr ausgeführt
                if group_manager.GroupManager.create_group(self, group_name_decoded, admin_id_decoded):
                    client_socket.send(bytes("Group was created", "utf8"))
                    print("weiter")
                else:
                    print("else")
                    client_socket.send(bytes("An error occurred please try again later", "utf8"))

            if received_data.startswith("!leave_group") and client_login:
                pass
            if received_data.startswith("!add_user_to_group") and client_login:
                pass
            if received_data.startswith("!remove_user_from_group") and client_login:
                pass
            if received_data.startswith("!get_group_members") and client_login:
                pass
            if received_data.startswith("!get_user_groups") and client_login:
                pass
            # have to be overworked
            if received_data.startswith("!send") and client_login:
                pass
            if received_data.startswith("!delete_group") and client_login:
                pass

            self.check_client_is_online(client_socket, received_data)

    def check_client_is_online(self, client_socket, msg):
        if not msg:
            client_id = self.client_id[client_socket]
            del self.clients[client_id]
            client_socket.close()
            return False
        else:
            return True

    def get_chat_history(self, client_id, other_client_id):
        lock = threading.Lock()
        lock.acquire()
        self.mycursor.execute(
            "SELECT receiver_id, sender_id, message FROM ChatHistory WHERE (receiver_id = %s AND sender_id = %s) OR (receiver_id = %s AND sender_id = %s) ORDER BY id DESC LIMIT 15",
            (client_id, other_client_id, other_client_id, client_id))
        chat_history = self.mycursor.fetchall()
        lock.release()
        print(chat_history)
        return chat_history

    def overwrite_client_adress(self, client_adress, username):
        lock = threading.Lock()
        lock.acquire()
        self.mycursor.execute("UPDATE Users SET ip = %s, port = %s WHERE username = %s", (client_adress[0], client_adress[1], username))
        self.mydb.commit()
        lock.release()

    def check_login_credentials(self, username, password):
        lock = threading.Lock()
        lock.acquire()
        while True:
            try:
                self.mycursor.execute("SELECT * FROM Users WHERE username = %s AND password = %s", (username, password))
                result = self.mycursor.fetchone()
                lock.release()
                return result is not None
            except mysql.connector.errors.OperationalError:
                continue

    def is_user_registered(self, username):
        lock = threading.Lock()
        lock.acquire()
        self.mycursor.execute("SELECT username FROM Users WHERE username = %s", (username,))
        result = self.mycursor.fetchone()
        lock.release()
        return result is not None

    def register_in_db(self, user_credentials, client_adress):
        print(user_credentials["password"])
        lock = threading.Lock()
        lock.acquire()
        self.mycursor.execute("INSERT INTO Users (username, password, ip, port) VALUES (%s, %s, %s, %s)",
                              (user_credentials["username"], user_credentials["password"], client_adress[0], client_adress[1]))
        self.mydb.commit()
        lock.release()

    def get_chat_member_ids(self, target_username, username):
        print(target_username)
        lock = threading.Lock()
        lock.acquire()
        self.mycursor.execute("SELECT id FROM Users WHERE username = %s", (target_username,))
        receiver_user_id = self.mycursor.fetchone()
        print(receiver_user_id)
        self.mycursor.execute("SELECT id FROM Users WHERE username = %s", (username,))
        sender_id = self.mycursor.fetchone()
        lock.release()
        print(receiver_user_id)
        ids = [receiver_user_id, sender_id]
        return ids

    def get_user_id(self, username):
        lock = threading.Lock()
        lock.acquire()
        self.mycursor.execute("SELECT id FROM Users WHERE username = %s", (username,))
        identifier = self.mycursor.fetchone()
        lock.release()
        identifier = str(identifier).strip("(), ")
        print("client id is:", identifier)
        return identifier

    def send_message_to_target(self, receiver_id, sender_id, message):
        print("receiver id: ", receiver_id)
        print("keys", self.clients.keys())
        try:
            username = self.get_username(sender_id)
            receiver = self.clients[str(receiver_id)]
            print(receiver)
            receiver.send(bytes(f"{username}:{message}", "utf8"))
        except KeyError as e:
            print(e)

    def get_username(self, sender_id):
        lock = threading.Lock()
        lock.acquire()
        self.mycursor.execute("SELECT username FROM Users WHERE id = %s", (sender_id,))
        lock.release()
        username = self.mycursor.fetchone()
        striped_username = str(username).strip("(),' ")
        return striped_username

    def insert_chat_message(self, receiver_id, sender_id, message):
        lock = threading.Lock()
        lock.acquire()
        print(message)
        self.mycursor.execute("INSERT INTO ChatHistory (sender_id, receiver_id, message) VALUES (%s, %s, %s)",
                              (sender_id, receiver_id, message))
        self.mydb.commit()
        lock.release()
        self.send_message_to_target(receiver_id, sender_id, message)


if __name__ == "__main__":
    server = Server()
    server.start_server()
    while True:
        commands = input("Type stop to stop the server")
        if commands == "stop":
            quit()
