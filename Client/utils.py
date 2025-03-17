# utils.py
import tkinter as tk
from tkinter import Label, Button, Frame, Listbox, Scrollbar

def create_selection_dialog(options, title):
    dialog = tk.Toplevel()
    dialog.title(title)
    dialog.geometry("400x300")
    selected_index = None
    dialog_active = True

    def on_select(index):
        nonlocal selected_index, dialog_active
        selected_index = index
        dialog_active = False
        dialog.destroy()

    def on_cancel():
        nonlocal dialog_active
        dialog_active = False
        dialog.destroy()

    Label(dialog, text="Select a file:").pack(pady=10)
    list_frame = Frame(dialog)
    list_frame.pack(fill="both", expand=True, padx=10, pady=5)
    scrollbar = Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")
    listbox = Listbox(list_frame, width=50, height=10)
    listbox.pack(side="left", fill="both", expand=True)
    listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)
    for option in options:
        listbox.insert("end", option)
    button_frame = Frame(dialog)
    button_frame.pack(fill="x", pady=10)
    select_button = Button(button_frame, text="Select", command=lambda: on_select(listbox.curselection()[0]) if listbox.curselection() else None)
    select_button.pack(side="left", padx=10)
    cancel_button = Button(button_frame, text="Cancel", command=on_cancel)
    cancel_button.pack(side="right", padx=10)
    dialog.transient()
    dialog.grab_set()
    dialog.wait_window()
    return selected_index