from pymongo import MongoClient
import json

url = "mongodb+srv://barak:barak123@cluster0.qyjxf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
cluster = MongoClient(url)
db = cluster["Project1"]
usercollection = db["UsersInfo"]
files_collection = db["UserFiles.files"]
dircollection = db["DirNames"]


def list_directories(client_socket, username):
    try:
        # Find directories for the user
        directories = list(dircollection.find({"Users": username}, {"DirName": 1, "_id": 0}))
        dirnames = [dir["DirName"] for dir in directories]

        # Ensure something is always returned
        if not dirnames:
            dirnames = ["No directories available"]

        # Safe JSON conversion
        dir_json = json.dumps(dirnames)

        # Ensure complete transmission
        client_socket.sendall(dir_json.encode('utf-8'))

    except Exception as e:
        print(f"Error listing directories for {username}: {e}")
        error_message = json.dumps(["No directories available"])
        client_socket.sendall(error_message.encode('utf-8'))

def check_if_exists(name):
    possible_dir = dircollection.find_one({"DirName": name})
    return possible_dir is not None

def file_exists_in_db(filename):
    file = files_collection.find_one({"FileName": filename})
    return file is not None

def get_unique_filename(filename):
    if not file_exists_in_db(filename):
        return filename

    base_name, extension = filename.rsplit('.', 1)
    counter = 1
    while True:
        new_filename = f"{base_name}({counter}).{extension}"
        if not file_exists_in_db(new_filename):
            return new_filename
        counter += 1