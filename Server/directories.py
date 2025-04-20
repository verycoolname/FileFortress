from pymongo import MongoClient
from utils import check_if_exists, list_directories
import json
import traceback
import inspect

url = "mongodb+srv://barak:barak123@cluster0.qyjxf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
cluster = MongoClient(url)
db = cluster["Project1"]
usercollection = db["UsersInfo"]
dircollection = db["DirNames"]


def post_login(client_socket, username):
    try:
        while True:
            cmd = client_socket.recv(1024).decode('utf-8')
            print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Received command from {username}: {cmd}")

            if not cmd:
                print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Client connection closed")
                break

            if cmd == "1":
                choose_dir(client_socket, username)
            elif cmd == "4":
                create_directory(client_socket, username)
            elif cmd == "6":
                handle_users(client_socket, username)
            elif cmd == "exit" or cmd == "logout":
                print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Client requested exit/logout")
                break
            elif cmd == "BACK_TO_MENU":
                print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending 'OK' for back to menu")
                client_socket.send("OK".encode('utf-8'))
            else:
                print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Unknown command received: {cmd}")
                print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending 'Invalid command' to client")
                client_socket.send("Invalid command".encode('utf-8'))

    except Exception as e:
        print(f"Error in post_login for {username}: {e}")
        print(traceback.format_exc())
    finally:
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Closing client socket")
        client_socket.close()


def choose_dir(client_socket, username):
    try:
        list_directories(client_socket, username)
        cmd = client_socket.recv(1024).decode('utf-8')
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Received directory selection command: {cmd}")

        if cmd in ["BACK_TO_MENU", "CANCEL"]:
            print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Client chose to cancel or return to menu")
            return

        if cmd == "SELECT_DIR":
            selected_dir = client_socket.recv(1024).decode('utf-8')
            print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Received selected directory: {selected_dir}")
            directories = dircollection.find({"Users": username}, {"DirName": 1, "_id": 0})
            dirnames = [dir["DirName"] for dir in directories]

            if selected_dir in dirnames:
                print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending 'Entered successfully' to client")
                client_socket.send("Entered successfully".encode('utf-8'))
                dirowner = dircollection.find_one({"DirName": selected_dir}).get("Owner")
                from files import handle_dirs
                handle_dirs(client_socket, selected_dir, username, dirowner)
            else:
                error_msg = f"You aren't allowed in {selected_dir} dir"
                print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending error message: {error_msg}")
                client_socket.send(error_msg.encode('utf-8'))
        else:
            print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending 'Invalid directory selection' to client")
            client_socket.send("Invalid directory selection".encode('utf-8'))

    except Exception as e:
        print(f"Error in choose_dir: {e}")
        print(traceback.format_exc())
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending 'Error selecting directory' to client")
        client_socket.send("Error selecting directory".encode('utf-8'))


def handle_users(client_socket, username):
    try:
        dirnames = [item["DirName"] for item in dircollection.find({"Owner": username})]
        dirnames_json = json.dumps(dirnames)
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending directory list: {dirnames_json}")
        client_socket.sendall(dirnames_json.encode('utf-8'))

        cmd = client_socket.recv(1024).decode('utf-8')
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Received user management command: {cmd}")
        while cmd!= "BACK_TO_MENU":
            if cmd in ["2", "3", "SHOW_USERS"]:
                wanteddir = client_socket.recv(1024).decode('utf-8').lower()
                print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Received directory name: {wanteddir}")

                if cmd == "2" or cmd == "3":
                    name = client_socket.recv(1024).decode('utf-8').lower()
                    print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Received username: {name}")
                    if cmd == "2":
                        response = add_user(wanteddir, name)
                    elif cmd == "3":
                        response = remove_user(wanteddir, name)
                    print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending response: {response}")
                    client_socket.send(response.encode('utf-8'))
                elif cmd == "SHOW_USERS":
                    show_directory_users(client_socket, username, wanteddir)
                    return  # Exit after SHOW_USERS, as response is handled internally
                else:
                    print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending 'Invalid command' to client")
                    client_socket.send("Invalid command".encode('utf-8'))
            cmd = client_socket.recv(1024).decode('utf-8')
        if cmd in ["stop", "5", ""]:
            print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Client requested stop or empty command")
            return


    except Exception as e:
        print(f"Error in handle_users: {e}")
        print(traceback.format_exc())
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending 'Error processing user management' to client")
        client_socket.send("Error processing user management".encode('utf-8'))


def show_directory_users(client_socket, username,wanteddir):
    try:
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): show_directory_users called for user: {username}")
        dir_info = dircollection.find_one({"DirName": wanteddir})
        if not dir_info:
            error_msg = json.dumps(["Directory not found"])
            print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Directory not found. Sending: {error_msg}")
            client_socket.sendall(error_msg.encode('utf-8'))
            return

        dir_owner = dir_info.get("Owner")
        if dir_owner != username:
            error_msg = json.dumps(["Permission denied"])
            print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Permission denied. Sending: {error_msg}")
            client_socket.sendall(error_msg.encode('utf-8'))
            return

        users_list = dir_info.get("Users", [])
        if not users_list:
            users_list = ["No users in this directory"]
        response = json.dumps(users_list)
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending users list: {response}")
        client_socket.sendall(response.encode('utf-8'))
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Response sent successfully")

        # Ensure data is flushed
        client_socket.sendall(b'')  # Send empty bytes to flush the buffer
    except Exception as e:
        error_msg = json.dumps(["Error: " + str(e)])
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Exception: {str(e)}")
        client_socket.sendall(error_msg.encode('utf-8'))


def add_user(wanteddir, name):
    try:
        check_if_in_diralready = dircollection.find_one({"DirName": wanteddir, "Users": {"$elemMatch": {"$eq": name}}})
        user_exist = usercollection.find_one({"Username": name})
        print(user_exist)
        if not user_exist:
            return "User doesn't exist"
        elif check_if_in_diralready:
            return "User is already in the dir"
        dircollection.update_one({"DirName": wanteddir}, {"$push": {"Users": name}})
        return "User was added to the dir"
    except Exception as e:
        print(f"Error adding user: {e}")
        return "Error adding user to directory"


def create_directory(client_socket, username):
    name = client_socket.recv(1024).decode('utf-8').lower()
    print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Received directory name to create: {name}")
    answer = check_if_exists(name)
    if answer:
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending 'dir name is already in use' to client")
        client_socket.send("dir name is already in use".encode('utf-8'))
    else:
        users_list = [username]
        dircollection.insert_one({"DirName": name, "Owner": username, "Users": users_list})
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending 'New dir is created' to client")
        client_socket.send("New dir is created".encode('utf-8'))
        print(f"DEBUG (Line {inspect.currentframe().f_lineno}): Sending 'OK' to confirm creation")
        client_socket.send("OK".encode('utf-8'))


def remove_user(wanteddir, name):
    try:
        check_if_in_diralready = dircollection.find_one({"DirName": wanteddir, "Users": {"$elemMatch": {"$eq": name}}})
        if check_if_in_diralready:
            dircollection.update_one({"DirName": wanteddir}, {"$pull": {"Users": name}})
            return "User was removed from the dir"
        return "User isn't in the dir"
    except Exception as e:
        print(f"Error removing user: {e}")