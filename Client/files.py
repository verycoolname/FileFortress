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

            # Send file name and size
            self.client_socket.send(file_name.encode('utf-8'))
            self.client_socket.send(str(file_size).encode('utf-8'))

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

        try:
            response = self.client_socket.recv(4096).decode('utf-8')
            files_dict = json.loads(response)
            if not files_dict:
                messagebox.showinfo("Download", "No files available to download")
                return

            file_options = list(files_dict.keys())
            selected_index = create_selection_dialog(file_options, "Select a file to download")

            if selected_index is None:
                self.client_socket.send("CANCEL".encode('utf-8'))
                return

            selected_file = file_options[selected_index]
            self.client_socket.send(selected_file.encode('utf-8'))

            save_path = filedialog.asksaveasfilename(title="Save file as", initialfile=selected_file)

            if not save_path:
                self.client_socket.send("CANCEL_SAVE".encode('utf-8'))
                return

            self.client_socket.send("READY_FOR_SIZE".encode('utf-8'))

            # Receive file size
            size_data = b""
            while True:
                byte = self.client_socket.recv(1)
                if byte == b'\n':
                    break
                size_data += byte
            file_size = int(size_data.decode('utf-8'))

            # Acknowledge readiness for data
            self.client_socket.send("READY_FOR_DATA".encode('utf-8'))

            # Create progress window with a different approach
            progress_window = tk.Toplevel(self.frame)
            progress_window.title("Downloading...")
            progress_window.geometry("300x100")
            progress_window.grab_set()  # Make the window modal

            label = tk.Label(progress_window, text=f"Downloading {selected_file}...")
            label.pack(pady=10)

            progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=250, mode="determinate")
            progress_bar.pack(pady=10)

            # Use a method to update progress that works with Tkinter's event loop
            def update_progress(current, total):
                percentage = int((current / total) * 100)
                progress_bar['value'] = percentage
                progress_window.update_idletasks()  # Force GUI update

            # Download the file
            with open(save_path, 'wb') as file:
                bytes_received = 0
                while bytes_received < file_size:
                    chunk_size = min(4096, file_size - bytes_received)
                    chunk = self.client_socket.recv(chunk_size)

                    if not chunk:
                        break

                    file.write(chunk)
                    bytes_received += len(chunk)

                    # Update progress periodically to avoid overwhelming the GUI
                    if bytes_received % 4096 == 0 or bytes_received >= file_size:
                        update_progress(bytes_received, file_size)

            # Close progress window
            progress_window.destroy()

            # Send download completion
            self.client_socket.send("DOWNLOAD_COMPLETE".encode('utf-8'))

            # Receive confirmation
            confirmation = self.client_socket.recv(1024).decode('utf-8')
            messagebox.showinfo("Download Complete", confirmation)

        except Exception as e:
            # Ensure progress window is closed in case of error
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