import ast
import socket
import chatlib
import random


SERVER_IP = "127.0.0.1"
SERVER_PORT = 5678


def build_and_send_message(conn, code, data):
    msg = chatlib.build_message(code, data)
    conn.send(msg.encode())


def recv_message_and_parse(conn):
    full_msg = conn.recv(1024).decode()
    cmd, data = chatlib.parse_message(full_msg)
    return cmd, data


def connect():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.connect(("127.0.0.1", 5678))
    return my_socket


def error_and_exit(error_msg):
    error_msg.quit()


def login(conn):
    while True:
        username = input("Please enter username: \n")
        password = input("Please enter your password: \n")
        data = username + chatlib.DATA_DELIMITER + password

        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"], data)
        answer = recv_message_and_parse(conn)
        if answer[0] == chatlib.PROTOCOL_SERVER["login_ok_msg"]:
            print("Logged in!")
            return username
        elif answer[0] == chatlib.PROTOCOL_SERVER["login_failed_msg"]:
            print(answer[1])


def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], "")
    print("Good Bye!")


def build_send_recv_parse(conn, msg_code, data):
    """
    Helper function that combine the send and receive data to and from the server.
    :param conn: The connected socket
    :param msg_code: Function to run on server
    :param data: The message we want to send
    :return: Response from the server
    """
    build_and_send_message(conn, msg_code, data)
    response = recv_message_and_parse(conn)
    return response


def get_my_score(conn, username):
    score = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_score"], username)
    if score == (None, None):
        print("Error !")
    else:
        print(f"Your score is: {int(score[1])} ")


def get_high_score(conn):
    """
    Printing a list of all users and there score when higher first
    :param conn: The connected socket
    :return: None
    """
    high_score = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_high_score"], "")
    result = high_score[1]
    x = list(ast.literal_eval(result))
    for i in x:
        print(i[0], ':', i[1])


def print_ans(answers):
    for i, ans in enumerate(answers):
        print(i + 1, "-", ans)
    print('\n To quit press ''9''')


def play_question(conn, username):
    """
    Getting the question from the server and process the response into list.
    If the user press the correct answer his score will increase by 5 points.
    :param conn: The connected socket.
    :param username: Updating the score by username
    :return: None
    """
    response = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_question"], "")
    questions_dict = eval(response[1])
    questions_list = list(questions_dict.values())

    while True:
        if len(questions_list) == 0:
            print("Sorry, No more question for you genius!")
            break

        current_question = random.choice(questions_list)
        print(current_question['question'])
        print_ans(current_question['answers'])
        user_ans = int(input("Choose your answer [1-4] "))
        if user_ans == 9:
            break

        if user_ans == int(current_question['correct']):
            print("Yes! another question..\n")
            questions_list.remove(current_question)
            build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_update_score"], username)
        else:
            print(f"Wrong! the answer is: {current_question['correct']}")


def get_logged_users(conn):
    users = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_users"], "")[1]
    result = list(ast.literal_eval(users))
    for i in result:
        print(f'Connected users are: {i}')


def main():
    """
    Main function, creating socket and connecting to server,
    and printing the menu options
    :return: None
    """

    my_socket = connect()
    username = login(my_socket)
    menu_options = ["Play a trivia question", "My score", "Score Table", "Logged users", "Quit"]

    while True:
        print("\nMAIN MENU:\n")
        for i, item in enumerate(menu_options):
            print(str(i+1) + "." + " " + item)
        print("\n")
        select = int(input("Please enter your choice: "))
        if select == 1:
            play_question(my_socket,username)
        if select == 2:
            get_my_score(my_socket, username)
        elif select == 3:
            get_high_score(my_socket)
        elif select == 4:
            get_logged_users(my_socket)
        elif select == 5:
            logout(my_socket)
            break


if __name__ == '__main__':
    main()
