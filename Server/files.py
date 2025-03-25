import json
from pymongo import MongoClient
from utils import get_unique_filename, file_exists_in_db
from encryption import encrypt_data, decrypt_data
from utils import list_directories
from bson import ObjectId
import gridfs
from pathlib import Path
import time


url = "mongodb+srv://barak:barak123@cluster0.qyjxf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
cluster = MongoClient(url)
db = cluster["Project1"]
dircollection = db["DirNames"]
files_collection = db["UserFiles.files"]
fs = gridfs.GridFS(db, collection="UserFiles")

def handle_dirs(client_socket, dirname, username, dirowner):
    while True:
        cmd = client_socket.recv(1024).decode('utf-8')
        if cmd == "1":
            upload_file(client_socket, dirname, username)
        elif cmd == "2":
            download_file(client_socket, username,dirname)
        elif cmd == "3":
            delete_files(client_socket, dirname, username, dirowner)
        elif cmd == "4":
            # Import here to avoid circular import
            from directories import post_login
            post_login(client_socket, username)


def upload_file(client_socket, dirname, username):
    """
    Server-side file upload handler with basic error handling.
    """
    try:
        # Receive filename
        file_name = client_socket.recv(1024).decode('utf-8').strip()
        file_size = int(client_socket.recv(1024).decode())

        file_name = get_unique_filename(file_name)
        bytes_received = 0

        # Create temporary file
        temp_path = Path(f"temp_{username}_{int(time.time())}")
        # Receive file data
        with open(temp_path, 'wb') as file:
            while bytes_received < file_size:
                chunk = client_socket.recv(4096)
                bytes_received += len(chunk)
                file.write(chunk)

        # Store in filesystem
        with open(temp_path, "rb") as f:
            encrypted_data = encrypt_data(f.read())
            fs.put(encrypted_data,
                   FileName=file_name,
                   Uploader=username,
                   DirName=dirname)


        # Cleanup
        temp_path.unlink()
        client_socket.send("File was uploaded successfully".encode("utf-8"))
        return
    except Exception as e:
        client_socket.send(f"The was an error while uploading the file: {e}".encode("utf-8"))
        return




def download_file(client_socket, username,dirname):
    """Improved file download handler with directory listing and decryption."""
    try:


        # Check if the directory exists in the user's list
        if not dircollection.find_one({"DirName": dirname, "Users": username}):
            client_socket.send("ERROR: Directory not found or not accessible.".encode('utf-8'))
            return

        # Get the list of files in the selected directory
        files = files_collection.find(
            {"DirName": dirname},
            {"FileName": 1}
        )

        filenames = {}
        for file in files:
            filenames[file["FileName"]] = str(file["_id"])
            print(filenames)

        if not filenames:
            client_socket.send("ERROR: No files available in this directory.".encode('utf-8'))
            return

        # Send available files as JSON
        json_str = json.dumps(filenames)
        client_socket.sendall(json_str.encode('utf-8'))

        # Receive the filename to be downloaded
        wantedfile = client_socket.recv(1024).decode('utf-8')

        if wantedfile == "CANCEL":
            return

        if wantedfile not in filenames:
            client_socket.send("ERROR: File not found.".encode('utf-8'))
            return

        # Wait for client to be ready for file size
        ready_msg = client_socket.recv(1024).decode('utf-8')

        if ready_msg == "CANCEL_SAVE":
            return

        if ready_msg != "READY_FOR_SIZE":
            return

        # Get and decrypt file data
        file_data = fs.get(ObjectId(filenames[wantedfile])).read()
        decrypted_data = decrypt_data(file_data)
        file_size = len(decrypted_data)

        # Send file size with newline delimiter
        client_socket.sendall(f"{str(file_size)}\n".encode())

        # Wait for client to be ready for data
        ready_for_data = client_socket.recv(1024).decode('utf-8')

        if ready_for_data != "READY_FOR_DATA":
            return

        # Send decrypted file data
        total_sent = 0
        while total_sent < file_size:
            chunk_size = min(1024, file_size - total_sent)
            chunk = decrypted_data[total_sent:total_sent + chunk_size]
            bytes_sent = client_socket.send(chunk)

            if bytes_sent == 0:
                raise RuntimeError("Socket connection broken")

            total_sent += bytes_sent

        # Wait for download completion acknowledgment
        client_socket.recv(1024).decode('utf-8')  # To handle completion acknowledgment

        # Send final confirmation
        client_socket.send("File was downloaded successfully".encode("utf-8"))
        return

    except Exception as e:
        print(f"Download file error: {e}")
        try:
            client_socket.send(f"Server error: {str(e)}".encode('utf-8'))
        except:
            pass

def delete_files(client_socket, dirname, username, dirowner):
    try:
        files = files_collection.find(
            {"DirName": dirname},  # Replace "dirname" with your actual directory name
            {"_id": 0, "FileName": 1}  # Exclude 'length' and 'chunkSize'
        )
        filenames = []
        for file in files:
            filenames.append(file["FileName"])  # Assuming 'file' is the correct key; adjust as needed
        client_socket.sendall(json.dumps(filenames).encode('utf-8'))
        wantedfile = client_socket.recv(1024).decode('utf-8')
        file_info = files_collection.find_one({"DirName": dirname, "FileName": wantedfile})
        if file_info and (username == dirowner or username == file_info["Uploader"]):
            files_collection.delete_one({"DirName": dirname, "FileName": wantedfile})
            client_socket.sendall("File deleted successfully".encode('utf-8'))
        else:
            client_socket.sendall("Permission denied or file not found".encode('utf-8'))


    except Exception as e:
        print(e)