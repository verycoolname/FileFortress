from pymongo import MongoClient
from utils import check_if_exists, list_directories
import json
import traceback

url = "mongodb+srv://barak:barak123@cluster0.qyjxf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
cluster = MongoClient(url)
db = cluster["Project1"]
dircollection = db["DirNames"]


def post_login(client_socket, username):
    """
    Handle post-login operations with improved error handling and flexibility.
    """
    try:
        while True:
            cmd = client_socket.recv(1024).decode('utf-8')

            if not cmd:
                # Connection closed
                break

            if cmd == "1":
                choose_dir(client_socket, username)
            elif cmd == "4":
                create_directory(client_socket, username)
            elif cmd == "6":
                handle_users(client_socket, username)
            elif cmd == "exit" or cmd == "logout":
                break
            else:
                print(f"Unknown command received: {cmd}")
                client_socket.send("Invalid command".encode('utf-8'))

    except Exception as e:
        print(f"Error in post_login for {username}: {e}")
        print(traceback.format_exc())
    finally:
        client_socket.close()


def choose_dir(client_socket, username):
    """
    Improved directory selection with better error handling.
    """
    try:
        # List available directories
        list_directories(client_socket, username)

        # Wait for specific directory selection command
        cmd = client_socket.recv(1024).decode('utf-8')

        # Handle cancellation or back to menu
        if cmd in ["BACK_TO_MENU", "CANCEL"]:
            return

        # Only proceed if the command is to select a directory
        if cmd == "SELECT_DIR":
            # Wait for directory selection
            selected_dir = client_socket.recv(1024).decode('utf-8')

            # Verify user's access to the directory
            directories = dircollection.find({"Users": username}, {"DirName": 1, "_id": 0})
            dirnames = [dir["DirName"] for dir in directories]

            if selected_dir in dirnames:
                client_socket.send("Entered successfully".encode('utf-8'))
                dirowner = dircollection.find_one({"DirName": selected_dir}).get("Owner")

                # Import here to avoid circular import
                from files import handle_dirs
                handle_dirs(client_socket, selected_dir, username, dirowner)
            else:
                error_msg = f"You aren't allowed in {selected_dir} dir"
                client_socket.send(error_msg.encode('utf-8'))
        else:
            client_socket.send("Invalid directory selection".encode('utf-8'))

    except Exception as e:
        print(f"Error in choose_dir: {e}")
        print(traceback.format_exc())
        client_socket.send("Error selecting directory".encode('utf-8'))


def handle_users(client_socket, username):
    """
    Improved user management with better error handling and single-pass logic.
    """
    try:
        # Get directories owned by the user
        dirnames = []
        dirname1 = dircollection.find({"Owner": username})
        for item in dirname1:
            dirnames.append(item["DirName"])

        # Send directory list
        client_socket.sendall(json.dumps(dirnames).encode('utf-8'))

        # Process user management commands
        cmd = client_socket.recv(1024).decode('utf-8')

        # Exit conditions
        if cmd in ["stop", "5", ""]:
            return

        if cmd in ["2", "3"]:
            # Receive directory name
            wanteddir = client_socket.recv(1024).decode('utf-8').lower()

            # Receive username to add/remove
            name = client_socket.recv(1024).decode('utf-8').lower()

            # Perform add or remove operation
            if cmd == "2":
                response = add_user(wanteddir, name)
            else:
                response = remove_user(wanteddir, name)

            # Send response back to client
            client_socket.send(response.encode('utf-8'))
        else:
            client_socket.send("Invalid command".encode('utf-8'))

    except Exception as e:
        print(f"Error in handle_users: {e}")
        print(traceback.format_exc())
        client_socket.send("Error processing user management".encode('utf-8'))


def add_user(wanteddir, name):
    """
    Add a user to a directory with improved error handling.
    """
    try:
        check_if_in_diralready = dircollection.find_one(
            {"DirName": wanteddir, "Users": {"$elemMatch": {"$eq": name}}}
        )

        if check_if_in_diralready:
            return "User is already in the dir"

        dircollection.update_one(
            {"DirName": wanteddir},
            {"$push": {"Users": name}}
        )
        return "User was added to the dir"

    except Exception as e:
        print(f"Error adding user: {e}")
        return "Error adding user to directory"
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



def remove_user(wanteddir, name):
    """
    Remove a user from a directory with improved error handling.
    """
    try:
        check_if_in_diralready = dircollection.find_one(
            {"DirName": wanteddir, "Users": {"$elemMatch": {"$eq": name}}}
        )

        if check_if_in_diralready:
            dircollection.update_one(
                {"DirName": wanteddir},
                {"$pull": {"Users": name}}
            )
            return "User was removed from the dir"

        return "User isn't in the dir"

    except Exception as e:
        print(f"Error removing user: {e}")
        return "Error removing user from directory"