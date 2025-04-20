import tkinter as tk
from tkinter import Label, Entry, Button, Listbox, Scrollbar, messagebox
import json
import time
import socket
import inspect


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
        self.dir_listbox.delete(0, tk.END)

        try:
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending '1' to fetch directories")
            self.client_socket.send("1".encode('utf-8'))
            dir_data = self.client_socket.recv(4096).decode('utf-8')
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Received directory data: {dir_data}")
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
        try:
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Preparing to return to main menu")

            # Check if a command is already in progress to prevent multiple sends
            if hasattr(self, '_returning_to_menu') and self._returning_to_menu:
                print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Already returning to menu")
                return

            self._returning_to_menu = True

            try:
                print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending 'BACK_TO_MENU' to server")
                self.client_socket.send("BACK_TO_MENU".encode('utf-8'))

                # Use a very short timeout to prevent long blocking
                self.client_socket.settimeout(2)

                try:
                    response = self.client_socket.recv(1024).decode('utf-8')
                    print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Received response: {response}")

                    if response == "OK":
                        self.create_main_menu()
                    else:
                        print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Unexpected response, falling back to main menu")
                        self.create_main_menu()

                except socket.timeout:
                    print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Timeout waiting for server response, falling back to main menu")
                    self.create_main_menu()

            except Exception as e:
                print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Error sending 'BACK_TO_MENU': {str(e)}")
                self.create_main_menu()

            finally:
                # Remove the timeout setting
                self.client_socket.settimeout(None)
                # Reset the flag
                self._returning_to_menu = False

        except Exception as e:
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Unexpected error in return_to_main_menu: {str(e)}")
            self.create_main_menu()

    def handle_directory_selection(self):
        from files import FileGUI
        selection = self.dir_listbox.curselection()
        if not selection:
            self.dir_output_label.config(text="Please select a directory", fg="red")
            return

        selected_dir = self.dir_listbox.get(selection[0])
        try:
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending 'SELECT_DIR' to server")
            self.client_socket.send("SELECT_DIR".encode('utf-8'))
            time.sleep(0.1)
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending selected directory: {selected_dir}")
            self.client_socket.send(selected_dir.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Received response: {response}")

            if "successfully" in response.lower():
                self.dir_output_label.config(text="Directory selected successfully", fg="green")
                self.frame.after(1500, lambda: FileGUI(self.frame, self.client_socket,
                                                       self.create_main_menu).create_directory_operations_page(
                    selected_dir))
            else:
                self.dir_output_label.config(text=response, fg="red")
                self.frame.after(1600, self.create_main_menu)
        except Exception as e:
            self.dir_output_label.config(text=f"Error: {str(e)}", fg="red")
            self.frame.after(1600, self.create_main_menu)

    def create_directory_page(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        Label(self.frame, text="Create New Directory", font=("Arial", 24, "bold"), bg="white").grid(row=0, column=0,
                                                                                                    columnspan=2,
                                                                                                    pady=(0, 30))
        Label(self.frame, text="Directory Name:", font=("Arial", 16), bg="white").grid(row=1, column=0, sticky="w")
        self.dir_entry = Entry(self.frame, font=("Arial", 16), width=30, bd=1, relief="solid")
        self.dir_entry.grid(row=2, column=0, pady=(0, 15), padx=5)
        Button(self.frame, text="Create", font=("Arial", 16, "bold"), bg="#17a2b8", fg="white", width=10, height=1,
               bd=0, command=self.handle_create_directory).grid(row=2, column=1, pady=(0, 15), padx=5)
        self.dir_output_label = Label(self.frame, text="", font=("Arial", 14), fg="black", bg="white")
        self.dir_output_label.grid(row=3, column=0, columnspan=2, pady=(5, 15))
        Button(self.frame, text="Back to Menu", font=("Arial", 16, "bold"), bg="#6c757d", fg="white", width=40,
               height=2, bd=0, command=self.return_to_main_menu).grid(row=4, column=0, columnspan=2, pady=(15, 0))

    def handle_create_directory(self):
        dir_name = self.dir_entry.get().strip()
        if not dir_name:
            self.dir_output_label.config(text="Please enter a directory name", fg="red")
            return
        try:
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending '4' to create directory")
            self.client_socket.send("4".encode('utf-8'))
            time.sleep(0.1)
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending directory name: {dir_name}")
            self.client_socket.send(dir_name.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Received response: {response}")
            self.dir_output_label.config(text=response, fg="green" if "created" in response else "red")
            if "created" in response:
                self.dir_entry.delete(0, tk.END)
                # Wait for OK to confirm completion
                completion = self.client_socket.recv(1024).decode('utf-8')
                print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Received completion signal: {completion}")
                if completion != "OK":
                    self.dir_output_label.config(text="Error completing directory creation", fg="red")
        except Exception as e:
            self.dir_output_label.config(text=f"Error: {str(e)}", fg="red")

    def create_user_management_page(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        Label(self.frame, text="User Management", font=("Arial", 24, "bold"), bg="white").grid(row=0, column=0,
                                                                                               columnspan=2,
                                                                                               pady=(0, 30))
        list_frame = tk.Frame(self.frame, bg="white")
        list_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.dir_listbox = tk.Listbox(list_frame, font=("Arial", 14), width=40, height=5, bd=1, relief="solid",
                                      yscrollcommand=scrollbar.set)
        self.dir_listbox.pack(side=tk.LEFT)
        scrollbar.config(command=self.dir_listbox.yview)
        Label(self.frame, text="Username", font=("Arial", 16), bg="white").grid(row=2, column=0, sticky="w")
        self.username_entry = Entry(self.frame, font=("Arial", 16), width=40, bd=1, relief="solid")
        self.username_entry.grid(row=3, column=0, columnspan=2, pady=(0, 15))
        self.user_output_label = Label(self.frame, text="", font=("Arial", 14), fg="black", bg="white")
        self.user_output_label.grid(row=4, column=0, columnspan=2, pady=(5, 15))

        # Create a frame for the first row of buttons
        button_frame1 = tk.Frame(self.frame, bg="white")
        button_frame1.grid(row=5, column=0, columnspan=2, pady=(15, 0))

        # First row of buttons
        Button(button_frame1, text="Add User", font=("Arial", 16, "bold"), bg="#28a745", fg="white", width=13, height=2,
               bd=0, command=self.handle_add_user).pack(side=tk.LEFT, padx=5)
        Button(button_frame1, text="Remove User", font=("Arial", 16, "bold"), bg="#dc3545", fg="white", width=13,
               height=2, bd=0, command=self.handle_remove_user).pack(side=tk.LEFT, padx=5)
        Button(button_frame1, text="Show Users", font=("Arial", 16, "bold"), bg="#17a2b8", fg="white", width=13,
               height=2, bd=0, command=self.handle_show_users).pack(side=tk.LEFT, padx=5)

        # Back to Menu button
        Button(self.frame, text="Back to Menu", font=("Arial", 16, "bold"), bg="#6c757d", fg="white", width=40,
               height=2, bd=0, command=self.return_to_main_menu).grid(row=6, column=0, columnspan=2, pady=(15, 0))

        try:
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending '6' to fetch directories for user management")
            self.client_socket.send("6".encode('utf-8'))
            dir_data = self.client_socket.recv(4096).decode('utf-8')
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Received directory data: {dir_data}")
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
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending '2' to add user")
            self.client_socket.send("2".encode('utf-8'))
            time.sleep(0.1)
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending selected directory: {selected_dir}")
            self.client_socket.send(selected_dir.encode('utf-8'))
            time.sleep(0.1)
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending username: {username}")
            self.client_socket.send(username.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Received response: {response}")
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
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending '3' to remove user")
            self.client_socket.send("3".encode('utf-8'))
            time.sleep(0.1)
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending selected directory: {selected_dir}")
            self.client_socket.send(selected_dir.encode('utf-8'))
            time.sleep(0.1)
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending username: {username}")
            self.client_socket.send(username.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Received response: {response}")
            self.user_output_label.config(text=response, fg="green" if "removed" in response else "red")
            self.username_entry.delete(0, 'end')
        except Exception as e:
            self.user_output_label.config(text=f"Error: {str(e)}", fg="red")

    def handle_show_users(self):
        if not self.dir_listbox.curselection():
            self.user_output_label.config(text="Please select a directory", fg="red")
            return

        selected_dir = self.dir_listbox.get(self.dir_listbox.curselection()[0])
        try:
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending 'SHOW_USERS' to server")
            self.client_socket.send("SHOW_USERS".encode('utf-8'))
            time.sleep(0.1)  # Small delay for server processing
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Sending directory name: {selected_dir}")
            self.client_socket.send(selected_dir.encode('utf-8'))

            self.user_output_label.config(text="Loading users...", fg="black")
            self.client_socket.settimeout(5.0)
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Waiting for server response...")
            users_data = self.client_socket.recv(4096).decode('utf-8')
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Received raw response: {users_data}")

            try:
                users_list = json.loads(users_data)
                print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Parsed users list: {users_list}")
                if len(users_list) == 1 and (
                        "not found" in users_list[0].lower() or
                        "denied" in users_list[0].lower() or
                        "error" in users_list[0].lower()
                ):
                    self.user_output_label.config(text=users_list[0], fg="red")
                else:
                    # Display users in the main window instead of opening a new one
                    self.display_users_page(selected_dir, users_list)
            except json.JSONDecodeError as e:
                print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: JSON decode error: {str(e)}")
                self.user_output_label.config(
                    text=f"Invalid response format: {users_data[:50]}...",
                    fg="red"
                )
        except socket.timeout:
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Socket timeout occurred")
            self.user_output_label.config(text="Server took too long to respond", fg="red")
        except Exception as e:
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Unexpected error: {str(e)}")
            self.user_output_label.config(text=f"Error: {str(e)}", fg="red")
        finally:
            self.client_socket.settimeout(None)
            print(f"DEBUG [Line {inspect.currentframe().f_lineno}]: Timeout reset")

    def display_users_page(self, directory_name, users_list):
        # Clear the current frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Create header
        Label(self.frame, text=f"Users in '{directory_name}'",
              font=("Arial", 24, "bold"), bg="white").grid(
            row=0, column=0, columnspan=2, pady=(0, 30))

        # Create users list with scrollbar
        list_frame = tk.Frame(self.frame, bg="white")
        list_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        users_listbox = tk.Listbox(
            list_frame, font=("Arial", 14), width=40, height=10,
            bd=1, relief="solid", yscrollcommand=scrollbar.set
        )
        users_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=users_listbox.yview)

        # Populate list
        if users_list and len(users_list) > 0:
            for user in users_list:
                users_listbox.insert(tk.END, user)
        else:
            users_listbox.insert(tk.END, "No users found")

        # Add status label
        status_text = f"Total Users: {len(users_list)}" if users_list else "No users found"
        Label(self.frame, text=status_text, font=("Arial", 14),
              fg="black", bg="white").grid(
            row=2, column=0, columnspan=2, pady=(5, 15))

        # Add back button that returns to the user management page
        Button(self.frame, text="Back to User Management",
               font=("Arial", 16, "bold"), bg="#6c757d", fg="white",
               width=40, height=2, bd=0,
               command=lambda: self.create_user_management_page()).grid(
            row=3, column=0, columnspan=2, pady=(15, 0))