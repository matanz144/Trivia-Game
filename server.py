import socket
import chatlib
import select
import json


questions = {}
logged_users = {}
messages_to_send = []

with open("./users.json", "r") as outfile:
    users = json.loads(outfile.read())

with open("./questions.json", "r") as outfile:
    questions = json.loads(outfile.read())


ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"


def build_and_send_message(conn, code, data):
    msg = chatlib.build_message(code, data)
    t = (conn, msg)
    messages_to_send.append(t)
    print("[SERVER] ", msg)


def recv_message_and_parse(conn):
    full_msg = conn.recv(1024).decode()
    cmd, data = chatlib.parse_message(full_msg)
    return cmd, data


def setup_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    sock.listen()
    return sock


def send_error(conn, error_msg):
    build_and_send_message(conn, chatlib.ERROR_RETURN, error_msg)


def handle_logged_message(conn):
    global logged_users
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["get_users_msg"], str(list(logged_users.keys())))


def update_score(conn, username):
    users[username]['score'] += 5
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["get_update_score_msg"], str(users[username]["score"]))


def handle_highscore_message(conn):

    global users
    new_dict = {k: v for k, v in sorted(users.items(), key=lambda item: item[1]['score'], reverse=True)}
    ordered_score = [(k, v['score']) for k, v in new_dict.items()]
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["get_high_score_msg"], str(ordered_score))


def handle_getscore_message(conn, username):
    global users
    if username in users:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["get_score_msg"], str(users[username]["score"]))
    else:
        print("Can't get score")


def print_client_sockets(client_sockets):
    for c in client_sockets:
        print("\t", c.getpeername())


def handle_logout_message(conn):
    """
    Closing the connected socket
    :param conn: Socket to close
    :return: None
    """
    global logged_users
    temp_dict = {k: v for k,v in logged_users.items() if v != conn}
    logged_users = temp_dict
    print("LOGOUT")
    conn.close()


def handle_login_message(conn, data):
    """
     Gets socket and message data of login message. Checks  user and pass exists and match.
     If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    :param conn: Connected socket
    :param data: user data
    :return: None
    """
    global users
    global logged_users
    user_name = data.split("#")[0]
    password = data.split("#")[1]
    if user_name in logged_users.keys():
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_failed_msg"], "User already logged in")
    elif user_name in users.keys():
        if password == users[user_name]["password"]:
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_ok_msg"], "")
            logged_users[user_name] = conn
        else:
            print(user_name, password, "Error password")
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_failed_msg"], "Password doesn't match")
    else:
        print(user_name, password, "Error username")
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_failed_msg"], "Username doesnt exist")


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Recieves: socket, message code and data
    Returns: None
    """

    global logged_users
    if cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:
        handle_login_message(conn, data)
    elif cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
        handle_logout_message(conn)
    elif cmd == chatlib.PROTOCOL_CLIENT["get_score"]:
        handle_getscore_message(conn, data)
    elif cmd == chatlib.PROTOCOL_CLIENT["get_high_score"]:
        handle_highscore_message(conn)
    elif cmd == chatlib.PROTOCOL_CLIENT["get_question"]:
        data = questions
        build_and_send_message(conn, cmd, str(data))
    elif cmd == chatlib.PROTOCOL_CLIENT["get_users"]:
        handle_logged_message(conn)
    elif cmd == chatlib.PROTOCOL_CLIENT["get_update_score"]:
        update_score(conn, data)
    else:
        send_error(conn, "The cmd is invalid")


def main():
    global users
    global questions
    global messages_to_send
    print("Welcome to Trivia Server!")
    print("Setting up Server...")
    conn = setup_socket()
    print("Server up and running!")
    print("Listening for clients...")
    client_sockets = []
    while True:
        ready_to_read, ready_to_write, in_error = select.select([conn] + client_sockets, [], [])
        for current_socket in ready_to_read:
            if current_socket is conn:
                (client_socket, client_address) = current_socket.accept()
                print("New client joined!", client_address)
                client_sockets.append(client_socket)
                print_client_sockets(client_sockets)
                cmd, data = recv_message_and_parse(client_socket)
                handle_client_message(client_socket, cmd, data)
            else:
                print("New data from client")
                client_socket = current_socket
                cmd, data = recv_message_and_parse(client_socket)
                if cmd is not None and data is not None:
                    handle_client_message(current_socket, cmd, data)
                if cmd == chatlib.PROTOCOL_CLIENT["logout_msg"] or cmd is None:
                    print("Connection closed")
                    client_sockets.remove(current_socket)
                    print_client_sockets(client_sockets)

        for message in messages_to_send:
            # message -> (conn , msg)
            message[0].send(message[1].encode())
        messages_to_send = []

if __name__ == '__main__':
    main()
