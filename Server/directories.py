from pymongo import MongoClient
from utils import check_if_exists, list_directories

import json


url = "mongodb+srv://barak:barak123@cluster0.qyjxf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
cluster = MongoClient(url)
db = cluster["Project1"]
dircollection = db["DirNames"]

def post_login(client_socket, username):
    while True:
        cmd = client_socket.recv(1024).decode('utf-8')
        if cmd == "1":
            choose_dir(client_socket, username)
        elif cmd == "4":
            create_directory(client_socket, username)
        elif cmd == "6":
            handle_users(client_socket,username)


def choose_dir(client_socket, username):
    list_directories(client_socket, username)
    selected_dir = client_socket.recv(1024).decode('utf-8')

    # Add this check to handle cancellation
    if selected_dir == "BACK_TO_MENU" or selected_dir == "CANCEL":
        return  # Return to post_login loop

    directories = dircollection.find({"Users": username}, {"DirName": 1, "_id": 0})
    dirnames = [dir["DirName"] for dir in directories]

    if selected_dir in dirnames:
        client_socket.send("Entered successfully".encode('utf-8'))
        dirowner = dircollection.find_one({"DirName": selected_dir}).get("Owner")
        # Import handle_dirs here to avoid circular import
        from files import handle_dirs
        handle_dirs(client_socket, selected_dir, username, dirowner)
    else:
        # Send error message first, then let the client decide what to do
        client_socket.send(f"You aren't allowed in {selected_dir} dir".encode('utf-8'))
        # Wait for client response before returning to post_login
        response = client_socket.recv(1024).decode('utf-8')
        if response == "BACK_TO_MENU":
            post_login(client_socket, username)


def create_directory(client_socket, username):
    name = client_socket.recv(1024).decode('utf-8').lower()
    answer = check_if_exists(name)
    if (answer):
        client_socket.send("dir name is already in use".encode('utf-8'))
    else:
        users_list = []
        users_list.append(username)
        dircollection.insert_one({
            "DirName": name,
            "Owner": username,
            "Users": [username]
        })
        client_socket.send("New dir is created".encode('utf-8'))

def handle_users(client_socket, username):
    dirnames = []
    dirname1 = dircollection.find({"Owner": username})
    for item in dirname1:
        dirnames.append(item["DirName"])

    if dirnames:
        client_socket.sendall(json.dumps(dirnames).encode('utf-8'))
    else:
        client_socket.sendall(json.dumps([]).encode('utf-8'))

    while True:
        try:
            cmd = client_socket.recv(1024).decode('utf-8')
            print(f"User management received command: {cmd}")  # Debug log

            if cmd == "stop" or cmd == "5" or not cmd:
                if cmd == "5":
                    post_login(client_socket, username)
                return
            elif cmd == "2" or cmd == "3":
                print("Processing add user command")  # Debug log

                # Receive directory name
                wanteddir = client_socket.recv(1024).decode('utf-8').lower()
                print(f"Directory selected: {wanteddir}")  # Debug log

                # Receive username
                name = client_socket.recv(1024).decode('utf-8').lower()
                print(f"Username to add: {name}")  # Debug log
                if(cmd == "2"):
                    add_user(client_socket,wanteddir,name)
                else:
                    remove_user(client_socket,wanteddir, name)
        except Exception as e:
            print(f"Error in handle_users: {str(e)}")  # Debug log
            break

def add_user(client_socket, wanteddir,name):
    check_if_in_diralready = dircollection.find_one(
        {"DirName": wanteddir, "Users": {"$elemMatch": {"$eq": name}}}
    )
    if check_if_in_diralready:
        response = "User is already in the dir"
    else:
        dircollection.update_one(
            {"DirName": wanteddir},
            {"$push": {"Users": name}}
        )
        response = "User was added to the dir"

    print(f"Sending response: {response}")  # Debug log
    client_socket.send(response.encode('utf-8'))

def remove_user(client_socket,wanteddir,name):
    check_if_in_diralready = dircollection.find_one(
        {"DirName": wanteddir, "Users": {"$elemMatch": {"$eq": name}}}
    )

    if check_if_in_diralready:
        dircollection.update_one(
            {"DirName": wanteddir},
            {"$pull": {"Users": name}}
        )
        response = "User was removed from the dir"
    else:
        response = "User isn't in the dir"

    print(f"Sending response: {response}")  # Debug log
    client_socket.send(response.encode('utf-8'))