# files.py
import tkinter as tk
from tkinter import Label, Button, filedialog, messagebox, Toplevel, ttk
import json
import os

class FileGUI:
    def __init__(self, frame, client_socket, create_main_menu_callback):
        self.frame = frame
        self.client_socket = client_socket
        self.create_main_menu = create_main_menu_callback

    def create_directory_operations_page(self, dirname):
        for widget in self.frame.winfo_children():
            widget.destroy()
        Label(self.frame, text=f"Directory: {dirname}", font=("Arial", 24, "bold"), bg="white").grid(row=0, column=0, columnspan=2, pady=(0, 30))
        Button(self.frame, text="Upload File", font=("Arial", 16, "bold"), bg="#28a745", fg="white", width=40, height=2, bd=0, command=lambda: self.handle_dir_operation("1")).grid(row=1, column=0, columnspan=2, pady=(15, 0))
        Button(self.frame, text="Download File", font=("Arial", 16, "bold"), bg="#007bff", fg="white", width=40, height=2, bd=0, command=lambda: self.handle_dir_operation("2")).grid(row=2, column=0, columnspan=2, pady=(15, 0))
        Button(self.frame, text="Delete File", font=("Arial", 16, "bold"), bg="#dc3545", fg="white", width=40, height=2, bd=0, command=lambda: self.handle_dir_operation("3")).grid(row=3, column=0, columnspan=2, pady=(15, 0))
        Button(self.frame, text="Back to Main Menu", font=("Arial", 16, "bold"), bg="#6c757d", fg="white", width=40, height=2, bd=0, command=lambda: [self.client_socket.send("4".encode('utf-8')), self.create_main_menu()]).grid(row=4, column=0, columnspan=2, pady=(15, 0))

    def handle_dir_operation(self, operation):
        try:
            self.client_socket.send(operation.encode('utf-8'))
            if operation == "1":
                self.handle_upload_file()
            elif operation == "2":
                self.handle_download_file()
            elif operation == "3":
                self.handle_delete_file()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def handle_upload_file(self):
        file_path = filedialog.askopenfilename(title="Select a file to upload")
        if not file_path:
            return

        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            # Send filename and size as UTF-8 encoded strings
            self.client_socket.send(file_name.encode('utf-8'))
            self.client_socket.send(str(file_size).encode('utf-8'))

            # Wait for server's "READY" signal
            ready_signal = self.client_socket.recv(1024).decode('utf-8')
            if ready_signal != "READY":
                raise ConnectionError("Server not ready for file data")

            # Create progress window
            progress = Toplevel()
            progress.title("Uploading...")
            progress.geometry("300x100")
            Label(progress, text=f"Uploading {file_name}...").pack(pady=10)
            progress_bar = ttk.Progressbar(progress, orient="horizontal", length=250, mode="determinate")
            progress_bar.pack(pady=10)

            # Open file and start upload
            with open(file_path, 'rb') as file:
                bytes_sent = 0
                while bytes_sent < file_size:
                    chunk = file.read(4096)
                    if not chunk:
                        break
                    self.client_socket.send(chunk)
                    bytes_sent += len(chunk)

                    # Update progress bar
                    progress_bar["value"] = (bytes_sent / file_size) * 100
                    progress.update()

            # Close progress window
            progress.destroy()

            # Wait for server response
            response = self.client_socket.recv(1024).decode('utf-8')
            messagebox.showinfo("Upload Status", response)

        except Exception as e:
            # Ensure progress window is closed in case of error
            if 'progress' in locals():
                progress.destroy()
            messagebox.showerror("Upload Error", f"Failed to upload file: {str(e)}")

    def handle_download_file(self):
        from utils import create_selection_dialog
        import tkinter as tk
        import time
        import socket

        try:
            # Get list of available files
            response = self.client_socket.recv(4096).decode('utf-8')
            files_dict = json.loads(response)
            if not files_dict:
                messagebox.showinfo("Download", "No files available to download")
                return

            # Let user select a file
            file_options = list(files_dict.keys())
            selected_index = create_selection_dialog(file_options, "Select a file to download")

            if selected_index is None:
                self.client_socket.send("CANCEL".encode('utf-8'))
                return

            selected_file = file_options[selected_index]
            self.client_socket.send(selected_file.encode('utf-8'))

            # Get save location
            save_path = filedialog.asksaveasfilename(title="Save file as", initialfile=selected_file)

            if not save_path:
                self.client_socket.send("CANCEL_SAVE".encode('utf-8'))
                return

            # Tell server we're ready to receive the file size
            self.client_socket.send("READY_FOR_SIZE".encode('utf-8'))

            # Receive file size
            size_data = b""
            while True:
                byte = self.client_socket.recv(1)
                if byte == b'\n':
                    break
                size_data += byte
            file_size = int(size_data.decode('utf-8'))

            # Tell server we're ready for the file data
            self.client_socket.send("READY_FOR_DATA".encode('utf-8'))

            # Create progress window before starting download
            progress_window = tk.Toplevel(self.frame)
            progress_window.title("Downloading...")
            progress_window.geometry("300x120")
            progress_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Prevent closing

            # Center window
            progress_window.update_idletasks()
            width = progress_window.winfo_width()
            height = progress_window.winfo_height()
            x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
            y = (progress_window.winfo_screenheight() // 2) - (height // 2)
            progress_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

            label = tk.Label(progress_window, text=f"Downloading {selected_file}...")
            label.pack(pady=10)

            progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=250, mode="determinate")
            progress_bar.pack(pady=10)

            # Add percentage label
            percentage_label = tk.Label(progress_window, text="0%")
            percentage_label.pack()

            # Force initial display
            progress_window.update()

            try:
                # Keep socket in blocking mode but use larger buffer
                # Open file for writing
                with open(save_path, 'wb') as file:
                    bytes_received = 0
                    last_update_time = time.time()
                    update_interval = 0.05  # Update every 50ms for smoother progress

                    # Download the file in chunks
                    while bytes_received < file_size:
                        # Calculate next chunk size - use larger chunks for better performance
                        remaining = file_size - bytes_received
                        chunk_size = min(32768, remaining)  # Increased from 8192 to 32768

                        try:
                            # Receive chunk
                            chunk = self.client_socket.recv(chunk_size)

                            if not chunk:
                                break

                            # Write chunk to file
                            file.write(chunk)
                            bytes_received += len(chunk)

                            # Update UI more frequently for smoother progress
                            current_time = time.time()
                            if current_time - last_update_time >= update_interval or bytes_received >= file_size:
                                # Calculate percentage
                                percentage = min(100, int((bytes_received / file_size) * 100))

                                # Update progress bar and labels
                                progress_bar["value"] = percentage
                                label.config(text=f"Downloading {selected_file}...")
                                percentage_label.config(
                                    text=f"{percentage}% ({bytes_received:,} / {file_size:,} bytes)")

                                # Force GUI update
                                progress_window.update_idletasks()
                                last_update_time = current_time

                        except socket.error as e:
                            print(f"Socket error during download: {e}")
                            messagebox.showerror("Download Error", f"Connection error: {e}")
                            progress_window.destroy()
                            return

                    # Ensure we show 100% completion
                    progress_bar["value"] = 100
                    percentage_label.config(text=f"100% ({file_size:,} / {file_size:,} bytes)")
                    label.config(text=f"Download complete!")
                    progress_window.update()
                    time.sleep(0.5)  # Give user time to see completion

            except Exception as e:
                print(f"Error during file download: {e}")
                messagebox.showerror("Download Error", f"Failed to download file: {e}")
                progress_window.destroy()
                return

            # Close progress window
            progress_window.destroy()

            # Send download completion
            self.client_socket.send("DOWNLOAD_COMPLETE".encode('utf-8'))

            # Receive confirmation
            confirmation = self.client_socket.recv(1024).decode('utf-8')
            messagebox.showinfo("Download Complete", confirmation)

        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            messagebox.showerror("Download Error", f"Failed to download file: {str(e)}")
    def handle_delete_file(self):
        from utils import create_selection_dialog
        try:
            response = self.client_socket.recv(1024).decode('utf-8')
            files_list = json.loads(response)
            if not files_list:
                messagebox.showinfo("Delete", "No files available to delete")
                return
            selected_index = create_selection_dialog(files_list, "Select a file to delete")
            if selected_index is None:
                self.client_socket.send("CANCEL".encode('utf-8'))
                return
            file_selection = files_list[selected_index]
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {file_selection}?"):
                self.client_socket.send(file_selection.encode('utf-8'))
                confirmation = self.client_socket.recv(1024).decode('utf-8')
                messagebox.showinfo("Delete Status", confirmation)
            else:
                self.client_socket.send("CANCEL".encode('utf-8'))
        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete file: {str(e)}")