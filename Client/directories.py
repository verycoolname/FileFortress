import tkinter as tk
from tkinter import Label, Entry, Button, Listbox, Scrollbar, messagebox
import json
import time

class DirectoryGUI:
    def __init__(self, frame, client_socket, create_main_menu_callback):
        self.frame = frame
        self.client_socket = client_socket
        self.create_main_menu = create_main_menu_callback

    def create_choose_directory_page(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        Label(self.frame, text="Choose Directory", font=("Arial", 24, "bold"), bg="white").grid(row=0, column=0,
                                                                                                columnspan=2,
                                                                                                pady=(0, 30))
        list_frame = tk.Frame(self.frame, bg="white")
        list_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.dir_listbox = tk.Listbox(list_frame, font=("Arial", 14), width=40, height=8, bd=1, relief="solid",
                                      yscrollcommand=scrollbar.set)
        self.dir_listbox.pack(side=tk.LEFT)
        scrollbar.config(command=self.dir_listbox.yview)

        # Clear the listbox first
        self.dir_listbox.delete(0, tk.END)

        try:
            # Send the command to get directories
            self.client_socket.send("1".encode('utf-8'))
            dir_data = self.client_socket.recv(4096).decode('utf-8')
            directories = json.loads(dir_data)
            for directory in directories:
                self.dir_listbox.insert(tk.END, directory)
        except Exception as e:
            tk.messagebox.showerror("Error", f"Could not fetch directories: {str(e)}")

        self.dir_output_label = Label(self.frame, text="", font=("Arial", 14), fg="black", bg="white")
        self.dir_output_label.grid(row=2, column=0, columnspan=2, pady=(5, 15))
        Button(self.frame, text="Select Directory", font=("Arial", 16, "bold"), bg="#007bff", fg="white", width=40,
               height=2, bd=0, command=self.handle_directory_selection).grid(row=3, column=0, columnspan=2,
                                                                             pady=(15, 0))
        Button(self.frame, text="Back to Menu", font=("Arial", 16, "bold"), bg="#6c757d", fg="white", width=40,
               height=2, bd=0, command=self.return_to_main_menu).grid(row=4, column=0, columnspan=2, pady=(15, 0))

    def return_to_main_menu(self):
        """Return to the main menu, ensuring server state is reset."""
        try:
            # Send a cancellation message to the server
            self.client_socket.send("BACK_TO_MENU".encode('utf-8'))
            time.sleep(0.2)  # Give server time to process
            self.create_main_menu()
        except Exception as e:
            # Still try to return to main menu even if there was an error
            self.create_main_menu()

    def handle_directory_selection(self):
        from files import FileGUI  # Avoid circular import
        selection = self.dir_listbox.curselection()
        if not selection:
            self.dir_output_label.config(text="Please select a directory", fg="red")
            return
        selected_dir = self.dir_listbox.get(selection[0])
        try:
            self.client_socket.send(selected_dir.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            self.dir_output_label.config(text=response, fg="green" if "successfully" in response.lower() else "red")
            if "successfully" in response.lower():
                self.frame.after(1500, lambda: FileGUI(self.frame, self.client_socket, self.create_main_menu).create_directory_operations_page(selected_dir))
            else:
                # Send a proper command to reset server state
                self.client_socket.send("4".encode('utf-8'))
                time.sleep(0.1)  # Wait a moment for the server to process
                self.frame.after(1600, self.create_main_menu)
        except Exception as e:
            self.dir_output_label.config(text=f"Error: {str(e)}", fg="red")
            try:
                # Try to reset server state in case of an error
                self.client_socket.send("4".encode('utf-8'))
            except:
                pass
            self.frame.after(1600, self.create_main_menu)

    def create_directory_page(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        Label(self.frame, text="Create New Directory", font=("Arial", 24, "bold"), bg="white").grid(row=0, column=0, columnspan=2, pady=(0, 30))
        Label(self.frame, text="Directory Name:", font=("Arial", 16), bg="white").grid(row=1, column=0, sticky="w")
        self.dir_entry = Entry(self.frame, font=("Arial", 16), width=30, bd=1, relief="solid")
        self.dir_entry.grid(row=2, column=0, pady=(0, 15), padx=5)
        Button(self.frame, text="Create", font=("Arial", 16, "bold"), bg="#17a2b8", fg="white", width=10, height=1, bd=0, command=self.handle_create_directory).grid(row=2, column=1, pady=(0, 15), padx=5)
        self.dir_output_label = Label(self.frame, text="", font=("Arial", 14), fg="black", bg="white")
        self.dir_output_label.grid(row=3, column=0, columnspan=2, pady=(5, 15))
        Button(self.frame, text="Back to Menu", font=("Arial", 16, "bold"), bg="#6c757d", fg="white", width=40, height=2, bd=0, command=self.return_to_main_menu).grid(row=4, column=0, columnspan=2, pady=(15, 0))

    def handle_create_directory(self):
        dir_name = self.dir_entry.get().strip()
        if not dir_name:
            self.dir_output_label.config(text="Please enter a directory name", fg="red")
            return
        try:
            self.client_socket.send("4".encode('utf-8'))
            time.sleep(0.1)
            self.client_socket.send(dir_name.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            self.dir_output_label.config(text=response, fg="green" if "created" in response else "red")
            if "created" in response:
                self.dir_entry.delete(0, tk.END)
        except Exception as e:
            self.dir_output_label.config(text=f"Error: {str(e)}", fg="red")

    def create_user_management_page(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        Label(self.frame, text="User Management", font=("Arial", 24, "bold"), bg="white").grid(row=0, column=0, columnspan=2, pady=(0, 30))
        list_frame = tk.Frame(self.frame, bg="white")
        list_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.dir_listbox = tk.Listbox(list_frame, font=("Arial", 14), width=40, height=5, bd=1, relief="solid", yscrollcommand=scrollbar.set)
        self.dir_listbox.pack(side=tk.LEFT)
        scrollbar.config(command=self.dir_listbox.yview)
        Label(self.frame, text="Username", font=("Arial", 16), bg="white").grid(row=2, column=0, sticky="w")
        self.username_entry = Entry(self.frame, font=("Arial", 16), width=40, bd=1, relief="solid")
        self.username_entry.grid(row=3, column=0, columnspan=2, pady=(0, 15))
        self.user_output_label = Label(self.frame, text="", font=("Arial", 14), fg="black", bg="white")
        self.user_output_label.grid(row=4, column=0, columnspan=2, pady=(5, 15))
        Button(self.frame, text="Add User", font=("Arial", 16, "bold"), bg="#28a745", fg="white", width=19, height=2, bd=0, command=self.handle_add_user).grid(row=5, column=0, pady=(15, 0))
        Button(self.frame, text="Remove User", font=("Arial", 16, "bold"), bg="#dc3545", fg="white", width=19, height=2, bd=0, command=self.handle_remove_user).grid(row=5, column=1, pady=(15, 0))
        Button(self.frame, text="Back to Menu", font=("Arial", 16, "bold"), bg="#6c757d", fg="white", width=40, height=2, bd=0, command=self.return_to_main_menu).grid(row=6, column=0, columnspan=2, pady=(15, 0))
        try:
            self.client_socket.send("6".encode('utf-8'))
            dir_data = self.client_socket.recv(4096).decode('utf-8')
            directories = json.loads(dir_data)
            for directory in directories:
                self.dir_listbox.insert(tk.END, directory)
        except Exception as e:
            self.user_output_label.config(text=f"Error loading directories: {str(e)}", fg="red")

    def handle_add_user(self):
        if not self.dir_listbox.curselection():
            self.user_output_label.config(text="Please select a directory", fg="red")
            return
        selected_dir = self.dir_listbox.get(self.dir_listbox.curselection()[0])
        username = self.username_entry.get().strip().lower()
        if not username:
            self.user_output_label.config(text="Please enter a username", fg="red")
            return
        try:
            self.client_socket.send("2".encode('utf-8'))
            time.sleep(0.1)
            self.client_socket.send(selected_dir.encode('utf-8'))
            time.sleep(0.1)
            self.client_socket.send(username.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            self.user_output_label.config(text=response, fg="green" if "added" in response else "red")
            self.username_entry.delete(0, 'end')
        except Exception as e:
            self.user_output_label.config(text=f"Error: {str(e)}", fg="red")

    def handle_remove_user(self):
        if not self.dir_listbox.curselection():
            self.user_output_label.config(text="Please select a directory", fg="red")
            return
        selected_dir = self.dir_listbox.get(self.dir_listbox.curselection()[0])
        username = self.username_entry.get().strip().lower()
        if not username:
            self.user_output_label.config(text="Please enter a username", fg="red")
            return
        try:
            self.client_socket.send("3".encode('utf-8'))
            time.sleep(0.1)
            self.client_socket.send(selected_dir.encode('utf-8'))
            time.sleep(0.1)
            self.client_socket.send(username.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            self.user_output_label.config(text=response, fg="green" if "removed" in response else "red")
            self.username_entry.delete(0, 'end')
        except Exception as e:
            self.user_output_label.config(text=f"Error: {str(e)}", fg="red")