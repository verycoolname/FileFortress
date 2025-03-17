# auth.py
import tkinter as tk
from tkinter import Label, Entry, Button
import time
from config import SERVER_HOST, SERVER_PORT

class AuthGUI:
    def __init__(self, frame, client_socket, create_main_menu_callback):
        self.frame = frame
        self.client_socket = client_socket
        self.create_main_menu = create_main_menu_callback

    def create_login_page(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

        Label(self.frame, text="Login", font=("Arial", 24, "bold"), bg="white").grid(row=0, column=0, columnspan=2, pady=(0, 30))
        Label(self.frame, text="Email address", font=("Arial", 16), bg="white").grid(row=1, column=0, sticky="w")
        self.email_entry = Entry(self.frame, font=("Arial", 16), width=40, bd=1, relief="solid")
        self.email_entry.grid(row=2, column=0, columnspan=2, pady=(0, 15))
        Label(self.frame, text="Password", font=("Arial", 16), bg="white").grid(row=3, column=0, sticky="w")
        self.password_entry = Entry(self.frame, font=("Arial", 16), width=40, bd=1, relief="solid", show="*")
        self.password_entry.grid(row=4, column=0, columnspan=2, pady=(0, 15))
        self.output_label = Label(self.frame, text="", font=("Arial", 14), fg="red", bg="white")
        self.output_label.grid(row=5, column=0, columnspan=2, pady=(5, 15))
        Button(self.frame, text="Login", font=("Arial", 16, "bold"), bg="#007bff", fg="white", width=40, height=2, bd=0, command=self.handle_login).grid(row=6, column=0, columnspan=2, pady=(15, 0))
        Button(self.frame, text="Sign Up", font=("Arial", 16, "bold"), bg="#6c757d", fg="white", width=40, height=2, bd=0, command=self.create_signup_page).grid(row=7, column=0, columnspan=2, pady=(15, 0))

    def create_signup_page(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

        Label(self.frame, text="Sign Up", font=("Arial", 24, "bold"), bg="white").grid(row=0, column=0, columnspan=2, pady=(0, 30))
        Label(self.frame, text="Username", font=("Arial", 16), bg="white").grid(row=1, column=0, sticky="w")
        self.username_entry = Entry(self.frame, font=("Arial", 16), width=40, bd=1, relief="solid")
        self.username_entry.grid(row=2, column=0, columnspan=2, pady=(0, 15))
        Label(self.frame, text="Email address", font=("Arial", 16), bg="white").grid(row=3, column=0, sticky="w")
        self.email_entry = Entry(self.frame, font=("Arial", 16), width=40, bd=1, relief="solid")
        self.email_entry.grid(row=4, column=0, columnspan=2, pady=(0, 15))
        Label(self.frame, text="Password", font=("Arial", 16), bg="white").grid(row=5, column=0, sticky="w")
        self.password_entry = Entry(self.frame, font=("Arial", 16), width=40, bd=1, relief="solid", show="*")
        self.password_entry.grid(row=6, column=0, columnspan=2, pady=(0, 15))
        self.output_label = Label(self.frame, text="", font=("Arial", 14), fg="red", bg="white")
        self.output_label.grid(row=7, column=0, columnspan=2, pady=(5, 15))
        Button(self.frame, text="Sign Up", font=("Arial", 16, "bold"), bg="#28a745", fg="white", width=40, height=2, bd=0, command=self.handle_signup).grid(row=8, column=0, columnspan=2, pady=(15, 0))
        Button(self.frame, text="Back to Login", font=("Arial", 16, "bold"), bg="#6c757d", fg="white", width=40, height=2, bd=0, command=self.create_login_page).grid(row=9, column=0, columnspan=2, pady=(15, 0))

    def handle_login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        try:
            self.client_socket.send("2".encode('utf-8'))
            self.client_socket.send(email.encode('utf-8'))
            time.sleep(0.1)
            self.client_socket.send(password.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            if response == "Login successful.":
                self.create_main_menu()
            else:
                self.output_label.config(text=response, fg="red")
        except Exception as e:
            self.output_label.config(text=f"Error: {str(e)}", fg="red")

    def handle_signup(self):
        username = self.username_entry.get()
        email = self.email_entry.get()
        password = self.password_entry.get()
        if len(username) < 3:
            self.output_label.config(text="Username must be at least 3 characters long.", fg="red")
        elif "@" not in email or "." not in email:
            self.output_label.config(text="Invalid email format.", fg="red")
        elif len(password) < 6:
            self.output_label.config(text="Password must be at least 6 characters long.", fg="red")
        else:
            try:
                self.client_socket.send("1".encode('utf-8'))
                self.client_socket.send(username.encode('utf-8'))
                time.sleep(0.1)
                self.client_socket.send(email.encode('utf-8'))
                time.sleep(0.1)
                self.client_socket.send(password.encode('utf-8'))
                response = self.client_socket.recv(1024).decode('utf-8')
                self.output_label.config(text=response, fg="green" if "successful" in response else "red")
                if "successful" in response:
                    self.create_login_page()
            except Exception as e:
                self.output_label.config(text=f"Error: {str(e)}", fg="red")