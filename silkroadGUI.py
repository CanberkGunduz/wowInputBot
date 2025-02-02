import tkinter as tk
from tkinter import ttk

import keyboard
import win32gui
import win32api
import win32ui
import win32con
import random
import threading
import time
from collections import defaultdict


class KeyPresserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Key Presser")
        self.root.geometry("520x280")

        # Active and Inactive fields
        self.active_label = ttk.Label(root, text="Active")
        self.active_label.place(x=30, y=10)
        self.active_list = tk.Listbox(root, selectmode=tk.SINGLE, height=10)
        self.active_list.place(x=30, y=30, width=180, height=150)

        self.inactive_label = ttk.Label(root, text="Inactive")
        self.inactive_label.place(x=280, y=10)
        self.inactive_list = tk.Listbox(root, selectmode=tk.SINGLE, height=10)
        self.inactive_list.place(x=280, y=30, width=180, height=150)

        # Buttons to move instances
        self.button_left = ttk.Button(root, text="<", command=self.move_to_active)
        self.button_left.place(x=220, y=80, width=30)

        self.button_right = ttk.Button(root, text=">", command=self.move_to_inactive)
        self.button_right.place(x=220, y=120, width=30)

        # Add, Remove, Edit buttons with horizontal spacing
        self.add_button = ttk.Button(root, text="Add", command=self.add_instance)
        self.add_button.place(x=280, y=190, width=60)

        self.remove_button = ttk.Button(root, text="Remove", command=self.remove_instance)
        self.remove_button.place(x=350, y=190, width=60)

        self.edit_button = ttk.Button(root, text="Edit", command=self.edit_instance, width=15)
        self.edit_button.place(x=280, y=220, width=130)

        # Start and Stop Buttons with spacing
        self.start_button = ttk.Button(root, text="Start", command=self.start_execution)
        self.start_button.place(x=30, y=190, width=60)

        self.stop_button = ttk.Button(root, text="Stop", command=self.stop_execution)
        self.stop_button.place(x=100, y=190, width=60)

        # Instance Management
        self.instance_counter = 1  # Start counter at 1
        self.instances = defaultdict(list)  # Store configurations for each instance
        self.stop_flag = threading.Event()

    def get_open_windows(self):
        """Fetch open windows and their handles."""
        windows = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_text.strip():
                    windows.append(f"{hwnd} - {window_text}")

        win32gui.EnumWindows(callback, None)
        return windows

    def add_instance(self):
        """Add a new empty instance."""
        new_instance = f"Instance {self.instance_counter}"
        self.instance_counter += 1
        self.inactive_list.insert(tk.END, new_instance)

    def remove_instance(self):
        """Remove selected instance from Inactive or Active list."""
        selected = self.inactive_list.curselection()
        if selected:
            instance = self.inactive_list.get(selected)
            self.inactive_list.delete(selected)
            self.instances.pop(instance, None)
        else:
            selected = self.active_list.curselection()
            if selected:
                instance = self.active_list.get(selected)
                self.active_list.delete(selected)
                self.instances.pop(instance, None)

    def move_to_active(self):
        """Move selected window from Inactive to Active."""
        selected = self.inactive_list.curselection()
        if selected:
            value = self.inactive_list.get(selected)
            self.inactive_list.delete(selected)
            self.active_list.insert(tk.END, value)

    def move_to_inactive(self):
        """Move selected window from Active to Inactive."""
        selected = self.active_list.curselection()
        if selected:
            value = self.active_list.get(selected)
            self.active_list.delete(selected)
            self.inactive_list.insert(tk.END, value)

    def edit_instance(self):
        """Edit the selected instance with window selection and key recorder."""
        selected_idx = self.active_list.curselection() or self.inactive_list.curselection()
        if selected_idx:
            listbox = self.active_list if self.active_list.curselection() else self.inactive_list
            instance_name = listbox.get(selected_idx)

            edit_window = tk.Toplevel(self.root)
            edit_window.title(f"Edit Instance - {instance_name}")
            edit_window.geometry("300x400")

            # Window Selection
            ttk.Label(edit_window, text="Select Window:").pack(pady=5)
            window_var = tk.StringVar()
            window_dropdown = ttk.Combobox(edit_window, textvariable=window_var, state="readonly")
            window_dropdown["values"] = self.get_open_windows()
            window_dropdown.pack(pady=5)

            # Keystroke Recorder
            keystrokes_label = ttk.Label(edit_window, text="Recorded Keystrokes:")
            keystrokes_label.pack(pady=5)

            keystrokes_listbox = tk.Listbox(edit_window, height=10)
            keystrokes_listbox.pack(pady=5)

            delay_label = ttk.Label(edit_window, text="Custom Delay (s):")
            delay_label.pack()
            delay_entry = ttk.Entry(edit_window)
            delay_entry.pack(pady=5)

            def record_keystroke():
                """Record a single keystroke and allow manual delay input."""
                key_var = tk.StringVar()

                def on_key(event):
                    key_var.set(event.name)
                    keyboard.unhook_all()

                    keystroke = key_var.get()
                    try:
                        delay = float(delay_entry.get())
                    except ValueError:
                        delay = 0.5  # Default delay
                    if instance_name not in self.instances:
                        self.instances[instance_name] = {"window": "", "keystrokes": []}
                    self.instances[instance_name]["keystrokes"].append((keystroke, delay))
                    keystrokes_listbox.insert(tk.END, f"{keystroke} - Delay: {delay}s")

                keyboard.on_press(on_key)

            record_button = ttk.Button(edit_window, text="Press Key", command=record_keystroke)
            record_button.pack(pady=5)

            def save_and_close():
                """Save recorded keystrokes, delays, and the selected window."""
                selected_window = window_var.get()  # Fetch the selected window
                if selected_window:
                    new_name = selected_window.split(" - ", 1)[-1].strip()  # Extract window name
                    listbox.delete(selected_idx)
                    listbox.insert(selected_idx, new_name)
                    # Save the selected window as a string, and keep the keystrokes separate
                    self.instances[new_name] = {
                        "window": selected_window,
                        "keystrokes": self.instances.pop(instance_name)[
                            "keystrokes"] if instance_name in self.instances else [],
                    }
                edit_window.destroy()

            save_button = ttk.Button(edit_window, text="Save and Close", command=save_and_close)
            save_button.pack(pady=10)

    def start_execution(self):
        """Start keystroke simulation."""
        self.stop_flag.clear()
        for idx in range(self.active_list.size()):
            instance_name = self.active_list.get(idx)
            instance_data = self.instances.get(instance_name, {})
            selected_window = instance_data.get("window")  # Fetch the selected window
            keys = instance_data.get("keystrokes", [])  # Fetch the recorded keystrokes
            print("window", selected_window)
            if selected_window:
                t = threading.Thread(target=self.execute_code, args=(selected_window, keys))
                t.start()

    def execute_code(self, selected_window, key_inputs):
        """Simulate key presses on the selected window."""
        print("Execution started")
        print(selected_window)
        print(key_inputs)

        if isinstance(selected_window, str):  # Ensure it's a string
            try:
                window_id = selected_window.split(" - ")[0]
                hwnd = int(window_id)  # Convert the ID to an integer
                print(hwnd)
            except (ValueError, IndexError):
                print(f"Invalid window ID: {selected_window}")
                return

            while True:
                for keystroke, delay in key_inputs:
                    if self.stop_flag.is_set():
                        print("Execution stopped")
                        return
                    adjusted_delay = random.uniform(delay * 0.9, delay * 1.1)
                    ascii_value = ord(keystroke)
                    print("pressing:",keystroke,ascii_value)
                    win32api.SendMessage(hwnd, win32con.WM_KEYDOWN, ascii_value, 0)
                    time.sleep(adjusted_delay)
                    win32api.SendMessage(hwnd, win32con.WM_KEYUP, ascii_value, 0)

    def stop_execution(self):
        """Stop keystroke execution."""
        self.stop_flag.set()
        print("Execution stopped.")

    # def execute_code(self, selected_window, key_inputs):
    #     """Simulate key presses on the selected window."""
    #     print("Execution started")
    #     print(selected_window)
    #     # print(key_inputs)
    #
    #     if isinstance(selected_window, str):  # Ensure it's a string
    #         try:
    #             window_id = selected_window.split(" - ")[0]
    #             hwnd = int(window_id)  # Convert the ID to an integer
    #         except (ValueError, IndexError):
    #             print(f"Invalid window ID: {selected_window}")
    #             return
    #
    #         while True:
    #             for keystroke, delay in key_inputs:
    #                 if self.stop_flag.is_set():
    #                     print("Execution stopped")
    #                     return
    #                 adjusted_delay = random.uniform(delay * 0.9, delay * 1.1)
    #                 ascii_value = ord(keystroke)
    #                 win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, ascii_value, 0)
    #                 time.sleep(adjusted_delay)
    #                 win32api.PostMessage(hwnd, win32con.WM_KEYUP, ascii_value, 0)


if __name__ == "__main__":
    root = tk.Tk()
    app = KeyPresserApp(root)
    root.mainloop()
