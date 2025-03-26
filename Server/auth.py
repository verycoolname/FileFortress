import time
from pymongo import MongoClient
from encryption import encrypt_email, hash_password, verify_password
from directories import post_login
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

url = "mongodb+srv://barak:barak123@cluster0.qyjxf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
cluster = MongoClient(url)
db = cluster["Project1"]
collection = db["UsersInfo"]
otp_storage = db["OTP"]

otp_storage.create_index("created_at", expireAfterSeconds=300)

def start_login(client_socket):
    """Handles the user login or signup process."""
    while True:
        cmd1 = client_socket.recv(1024).decode('utf-8')

        if cmd1 == "1":  # Sign up
            signup(client_socket)

        elif cmd1 == "2":  # Log in
            login(client_socket)

def signup(client_socket):
    # Enter Username
    username = client_socket.recv(1024).decode('utf-8').lower()
    time.sleep(0.1)
    # Enter Email
    email = client_socket.recv(1024).decode('utf-8').lower()
    time.sleep(0.1)
    # Enter Password
    password = client_socket.recv(1024).decode('utf-8').lower()
    time.sleep(0.1)
    encrypted_email = encrypt_email(email)
    hashed_password = hash_password(password)

    data1 = {"Username": username, "Email": encrypted_email, "Password": hashed_password}
    print(f"Signup attempt with data: {data1}")
    try:
        # Check if email or username already exists
        possible_email = collection.find_one({"Email": encrypted_email})
        possible_username = collection.find_one({"Username": username})

        if possible_email and possible_username:
            client_socket.send("Both Email and Username are already in use.".encode('utf-8'))
        elif possible_email:
            client_socket.send("Email already in use.".encode('utf-8'))
        elif possible_username:
            client_socket.send("Username already in use.".encode('utf-8'))
        else:
            collection.insert_one(data1)
            print(f"Successfully inserted user: {username}")
            client_socket.send("Signup successful!".encode('utf-8'))
    except Exception as e:
        print(f"Error during signup: {e}")
        client_socket.send("Error during signup.".encode('utf-8'))


def login(client_socket):
    # Enter Email
    email = client_socket.recv(1024).decode('utf-8').lower()
    print(email)
    # Enter password
    password = client_socket.recv(1024).decode('utf-8').lower()
    print(password)

    try:
        encrypted_email = encrypt_email(email)
        # Check for valid login credentials
        print(f"Attempting login with email: {email}")
        print(f"Encrypted email being searched: {encrypted_email}")
        user = collection.find_one({"Email": encrypted_email})

        if user and verify_password(password, user["Password"]):
            otp = str(random.randint(100000, 999999))  # 6-digit OTP
            store_otp(email, otp)
            if send_otp_email(email, otp):
                client_socket.send("Login successful. Enter OTP.".encode('utf-8'))
                # Wait for OTP from client
                for i in range(3):

                    client_otp = client_socket.recv(1024).decode('utf-8')
                    if verify_otp(email, client_otp):
                        client_socket.send("2FA successful. Welcome!".encode('utf-8'))
                        post_login(client_socket,collection.find_one({"Email": email})["Username"])
                        break
                        # Proceed with session
                    elif("login" in client_otp):
                        break
                    else:
                        client_socket.send("Invalid OTP. Login failed.".encode('utf-8'))

        else:
            if not user:
                print("No user found with this email")  # Debug print
            else:
                print("Password verification failed")  # Debug print
            client_socket.send("Invalid email or password.".encode('utf-8'))
    except Exception as e:
        print(f"Login error: {e}")
        client_socket.send("An error occurred during login.".encode('utf-8'))


def send_otp_email(email, otp):
    sender_email = "hbrytrzwt@gmail.com"  # Replace with your email
    sender_password = "mucm ajpe gkyt ktgg"  # Replace with your app-specific password
    subject = "Your 2FA OTP Code"
    body = f"Your one-time password (OTP) is: {otp}\nThis code is valid for 5 minutes."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"OTP sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send OTP: {str(e)}")
        return False

def store_otp(email, otp):
    # Store OTP in MongoDB with a creation timestamp
    otp_storage.insert_one({
        "email": email,
        "otp": otp,
        "created_at": datetime.utcnow()
    })
def verify_otp(email, client_otp):
    # Find the latest OTP for the email
    otp_doc = otp_storage.find_one({"email": email}, sort=[("created_at", -1)])
    if otp_doc and otp_doc["otp"] == client_otp:
        # OTP is valid; delete it to prevent reuse
        otp_storage.delete_one({"_id": otp_doc["_id"]})
        return True
    return False




