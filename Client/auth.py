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

        Label(self.frame, text="Login", font=("Arial", 24, "bold"), bg="white").grid(row=0, column=0, columnspan=2,
                                                                                     pady=(0, 30))
        Label(self.frame, text="Email address", font=("Arial", 16), bg="white").grid(row=1, column=0, sticky="w")
        self.email_entry = Entry(self.frame, font=("Arial", 16), width=40, bd=1, relief="solid")
        self.email_entry.grid(row=2, column=0, columnspan=2, pady=(0, 15))
        Label(self.frame, text="Password", font=("Arial", 16), bg="white").grid(row=3, column=0, sticky="w")
        self.password_entry = Entry(self.frame, font=("Arial", 16), width=40, bd=1, relief="solid", show="*")
        self.password_entry.grid(row=4, column=0, columnspan=2, pady=(0, 15))
        self.output_label = Label(self.frame, text="", font=("Arial", 14), fg="red", bg="white")
        self.output_label.grid(row=5, column=0, columnspan=2, pady=(5, 15))
        Button(self.frame, text="Login", font=("Arial", 16, "bold"), bg="#007bff", fg="white", width=40, height=2, bd=0,
               command=self.handle_login).grid(row=6, column=0, columnspan=2, pady=(15, 0))
        Button(self.frame, text="Sign Up", font=("Arial", 16, "bold"), bg="#6c757d", fg="white", width=40, height=2,
               bd=0, command=self.create_signup_page).grid(row=7, column=0, columnspan=2, pady=(15, 0))

    def create_signup_page(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

        Label(self.frame, text="Sign Up", font=("Arial", 24, "bold"), bg="white").grid(row=0, column=0, columnspan=2,
                                                                                       pady=(0, 30))
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
        Button(self.frame, text="Sign Up", font=("Arial", 16, "bold"), bg="#28a745", fg="white", width=40, height=2,
               bd=0, command=self.handle_signup).grid(row=8, column=0, columnspan=2, pady=(15, 0))
        Button(self.frame, text="Back to Login", font=("Arial", 16, "bold"), bg="#6c757d", fg="white", width=40,
               height=2, bd=0, command=self.create_login_page).grid(row=9, column=0, columnspan=2, pady=(15, 0))

    def create_otp_verification_page(self, email):
        for widget in self.frame.winfo_children():
            widget.destroy()

        self.email = email
        self.attempts_remaining = 3

        Label(self.frame, text="Two-Factor Authentication", font=("Arial", 24, "bold"), bg="white").grid(
            row=0, column=0, columnspan=2, pady=(0, 30))

        Label(self.frame, text="A verification code has been sent to your email.",
              font=("Arial", 14), bg="white", wraplength=400).grid(
            row=1, column=0, columnspan=2, pady=(0, 20))

        Label(self.frame, text="Enter OTP Code", font=("Arial", 16), bg="white").grid(
            row=2, column=0, sticky="w")

        self.otp_entry = Entry(self.frame, font=("Arial", 20), width=15, bd=1, relief="solid",
                               justify="center")
        self.otp_entry.grid(row=3, column=0, columnspan=2, pady=(0, 15))

        self.attempts_label = Label(self.frame, text=f"Attempts remaining: {self.attempts_remaining}",
                                    font=("Arial", 14), fg="blue", bg="white")
        self.attempts_label.grid(row=4, column=0, columnspan=2, pady=(5, 15))

        self.status_label = Label(self.frame, text="", font=("Arial", 14), fg="red", bg="white")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=(5, 15))

        Button(self.frame, text="Verify", font=("Arial", 16, "bold"), bg="#28a745", fg="white",
               width=20, height=2, bd=0, command=self.verify_otp).grid(
            row=6, column=0, columnspan=2, pady=(15, 0))

        Button(self.frame, text="Back to Login", font=("Arial", 14),
               bg="#6c757d", fg="white", bd=0, command=lambda: [self.client_socket.send("return to login".encode('utf-8')), self.create_login_page()]).grid(
            row=7, column=0, columnspan=2, pady=(15, 0))

        Label(self.frame, text="The code will expire in 5 minutes.", font=("Arial", 12),
              fg="gray", bg="white").grid(row=8, column=0, columnspan=2, pady=(20, 0))

    def verify_otp(self):
        otp_code = self.otp_entry.get().strip()

        if not otp_code:
            self.status_label.config(text="Please enter the verification code", fg="red")
            return

        if not otp_code.isdigit() or len(otp_code) != 6:
            self.status_label.config(text="OTP must be a 6-digit number", fg="red")
            return

        try:
            # Send OTP to server for verification
            self.client_socket.send(otp_code.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')

            if "2FA successful" in response:
                self.client_socket.send("GET_USERNAME".encode('utf-8'))
                print("sending getg username")
                username = self.client_socket.recv(1024).decode('utf-8')
                print(username)
                self.status_label.config(text="Verification successful!", fg="green")
                # Wait a moment before proceeding to main app
                self.frame.after(1500, lambda: self.create_main_menu(username))
            else:
                self.attempts_remaining -= 1
                if self.attempts_remaining > 0:
                    self.attempts_label.config(text=f"Attempts remaining: {self.attempts_remaining}")
                    self.status_label.config(text="Invalid verification code. Please try again.", fg="red")
                else:
                    self.status_label.config(text="Too many failed attempts. Please login again.", fg="red")
                    # Disable verification button after too many attempts
                    self.frame.after(2000, self.create_login_page)
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")

    def handle_login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        try:
            self.client_socket.send("2".encode('utf-8'))
            self.client_socket.send(email.encode('utf-8'))
            time.sleep(0.1)
            self.client_socket.send(password.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')

            if "Login successful. Enter OTP." in response:
                # Show OTP verification page instead of going straight to main menu
                self.create_otp_verification_page(email)
            elif "Login successful" in response:
                # For backward compatibility if server doesn't require 2FA
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