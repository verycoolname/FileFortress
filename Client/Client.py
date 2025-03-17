# client.py
import tkinter as tk  # Added this import
from tkinter import messagebox
import socket
from config import SERVER_HOST, SERVER_PORT
from auth import AuthGUI
from directories import DirectoryGUI

class FileShareClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("File Sharing System")
        self.root.geometry("800x450")
        self.root.configure(bg="white")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((SERVER_HOST, SERVER_PORT))
            print("Connected to server!")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
            self.root.destroy()
            return
        self.frame = tk.Frame(self.root, bg="white")
        self.frame.place(relx=0.5, rely=0.5, anchor="center")
        self.auth_gui = AuthGUI(self.frame, self.client_socket, self.create_main_menu)
        self.directory_gui = DirectoryGUI(self.frame, self.client_socket, self.create_main_menu)
        self.auth_gui.create_login_page()

    def create_main_menu(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        tk.Label(self.frame, text="File Sharing System", font=("Arial", 24, "bold"), bg="white").grid(row=0, column=0, columnspan=2, pady=(0, 30))
        tk.Button(self.frame, text="Choose Directory", font=("Arial", 16, "bold"), bg="#007bff", fg="white", width=40, height=2, bd=0, command=lambda: self.handle_main_menu("1")).grid(row=1, column=0, columnspan=2, pady=(15, 0))
        tk.Button(self.frame, text="Create Directory", font=("Arial", 16, "bold"), bg="#17a2b8", fg="white", width=40, height=2, bd=0, command=self.directory_gui.create_directory_page).grid(row=2, column=0, columnspan=2, pady=(15, 0))
        tk.Button(self.frame, text="Manage Users", font=("Arial", 16, "bold"), bg="#6610f2", fg="white", width=40, height=2, bd=0, command=self.directory_gui.create_user_management_page).grid(row=3, column=0, columnspan=2, pady=(15, 0))

    def handle_main_menu(self, cmd):
        if cmd == "1":
            self.directory_gui.create_choose_directory_page()
        elif cmd == "4":
            self.directory_gui.create_directory_page()
        elif cmd == "6":
            self.directory_gui.create_user_management_page()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = FileShareClient()
    client.run()