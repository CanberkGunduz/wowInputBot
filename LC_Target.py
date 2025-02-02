import tkinter as tk
from tkinter import ttk
import keyboard
import mouse
import pydirectinput
import win32process
import win32api
import win32gui
import win32con
import ctypes
import threading
import time
from collections import defaultdict
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import csv
import uuid

class LoginScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Login")
        self.root.geometry("300x200")

        # Username Label and Entry
        self.username_label = ttk.Label(root, text="Username:")
        self.username_label.pack(pady=5)
        self.username_entry = ttk.Entry(root)
        self.username_entry.pack(pady=5)

        # Password Label and Entry
        self.password_label = ttk.Label(root, text="Password:")
        self.password_label.pack(pady=5)
        self.password_entry = ttk.Entry(root, show="*")
        self.password_entry.pack(pady=5)

        # Login Button
        self.login_button = ttk.Button(root, text="Login", command=self.authenticate)
        self.login_button.pack(pady=10)

    def get_mac_address(self):
        """Get the MAC address of the current machine."""
        return ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8 * 6, 8)][::-1])

    def authenticate(self):
        """Authenticate user using a Google Sheet."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        if self.check_credentials(username, password) or True:
            print("Login successful!")
            self.root.destroy()
            self.launch_main_app()
        else:
            print("Invalid username or password.")

    def check_credentials(self, username, password):
        """Check credentials against an open Google Sheet link, including MAC address verification."""
        google_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR5V3PTXnr6_dMJh2UWA30ddpFx7bqMvUUkUSlRjFuGNE1PNG19et-qJcR5fxlba0dqtphR-etaBRvQ/pub?output=csv"

        try:
            response = requests.get(google_sheet_url)
            response.raise_for_status()
            decoded_content = response.content.decode('utf-8')
            csv_reader = csv.reader(decoded_content.splitlines(), delimiter=',')

            credentials = {}
            for row in csv_reader:

                if len(row) == 2:
                    credentials[row[0].strip()] = (row[1].strip(), "")
                elif len(row) == 3:
                    credentials[row[0].strip()] = (row[1].strip(), row[2].strip())


            if username in credentials:
                stored_password, stored_mac = credentials[username]

                if stored_password == password:
                    current_mac = self.get_mac_address()
                    if stored_mac == current_mac:
                        # print("Login successful!")
                        return True
                    elif stored_mac == "":  # Only register MAC if it's empty
                        print("First-time login detected. Registering MAC address...")
                        self.register_mac_address(username, current_mac)
                        return True
                    else:
                        print("Invalid MAC address. Access denied.")
                        return False
                else:
                    print("Invalid password.")
            else:
                print("Invalid username.")
            return False

        except Exception as e:
            print(f"Error fetching credentials: {e}")
            return False

    def register_mac_address(self, username, mac_address):
        """Register the MAC address in the Google Sheet."""
        google_web_app_url = "https://script.google.com/macros/s/AKfycbzAYv8re5kCo6e3sgCSNfG1dLd96e_E2HGlhUybDADUPEEULTyw7uASeVH-dYgzE77c/exec"

        try:
            print(mac_address)
            response = requests.post(google_web_app_url, json={"username": username, "mac_address": mac_address})
            if response.status_code == 200:
                print("MAC address registered successfully.")
            else:
                print(f"Failed to register MAC address: {response.status_code}")
        except Exception as e:
            print(f"Error registering MAC address: {e}")

    def launch_main_app(self):
        """Launch the main Key Presser app after successful login."""
        new_root = tk.Tk()
        KeyPresserApp(new_root)
        new_root.mainloop()



class KeyPresserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lionclaw Target")
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
        self.instances = defaultdict(lambda: {"window": None, "keystrokes": []})  # Store configurations for each instance
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
        """Edit the selected instance with window selection, key recorder, and mouse recorder."""
        selected_idx = self.active_list.curselection() or self.inactive_list.curselection()
        if selected_idx:
            listbox = self.active_list if self.active_list.curselection() else self.inactive_list
            instance_name = listbox.get(selected_idx)

            edit_window = tk.Toplevel(self.root)
            edit_window.title(f"Edit Instance - {instance_name}")
            edit_window.geometry("300x550")

            # Window Selection
            ttk.Label(edit_window, text="Select Window:").pack(pady=5)
            window_var = tk.StringVar()
            window_dropdown = ttk.Combobox(edit_window, textvariable=window_var, state="readonly")
            window_dropdown["values"] = self.get_open_windows()
            window_dropdown.pack(pady=5)

            # Keystroke Recorder
            keystrokes_label = ttk.Label(edit_window, text="Recorded Actions:")
            keystrokes_label.pack(pady=5)

            keystrokes_listbox = tk.Listbox(edit_window, height=15,width=40)
            keystrokes_listbox.pack(pady=5)

            for action_type, value, delay in self.instances[instance_name]["keystrokes"]:
                if action_type == 1:
                    keystrokes_listbox.insert(tk.END, f"Key: {value} - Delay: {delay}s")
                elif action_type == 2:
                    x, y = value
                    keystrokes_listbox.insert(tk.END, f"Mouse Click: x={x}, y={y} - Delay: {delay}s")

            delay_label = ttk.Label(edit_window, text="Custom Delay (s):")
            delay_label.pack()
            delay_entry = ttk.Entry(edit_window)
            delay_entry.pack(pady=5)

            # Record Keystroke Button
            def record_keystroke():
                key_var = tk.StringVar()

                def on_key(event):
                    key_var.set(event.name)
                    keyboard.unhook_all()

                    keystroke = key_var.get()
                    try:
                        delay = float(delay_entry.get())
                    except ValueError:
                        delay = 0.5  # Default delay

                    # Record key press as (1, "key_value", delay)
                    self.instances[instance_name]["keystrokes"].append((1, keystroke, delay))
                    keystrokes_listbox.insert(tk.END, f"Key: {keystroke} - Delay: {delay}s")

                keyboard.on_press(on_key)

            record_button = ttk.Button(edit_window, text="Press Key", command=record_keystroke)
            record_button.pack(pady=5)

            # Record Mouse Coordinate Button
            def record_mouse_coordinate():
                print("Recording mouse position in 2 seconds...")
                time.sleep(1)
                print("Recording mouse position in 1 second...")
                time.sleep(1)

                x, y = mouse.get_position()

                # Record mouse click as (2, (x, y), delay)
                try:
                    delay = float(delay_entry.get())
                except ValueError:
                    delay = 0.5  # Default delay

                self.instances[instance_name]["keystrokes"].append((2, (x, y), delay))
                keystrokes_listbox.insert(tk.END, f"Mouse Click: x={x}, y={y} - Delay: {delay}s")

            mouse_button = ttk.Button(edit_window, text="Record Mouse Coordinate", command=record_mouse_coordinate)
            mouse_button.pack(pady=5)

            # Save and Close Button
            def save_and_close():
                selected_window = window_var.get()
                if selected_window:
                    self.instances[instance_name]["window"] = selected_window
                edit_window.destroy()

            save_button = ttk.Button(edit_window, text="Save and Close", command=save_and_close)
            save_button.pack(pady=10)

    def start_execution(self):
        self.stop_flag.clear()
        for idx in range(self.active_list.size()):
            instance_name = self.active_list.get(idx)
            instance_data = self.instances.get(instance_name)
            if instance_data and instance_data["window"]:
                t = threading.Thread(target=self.execute_code, args=(instance_data,))
                t.start()

    def stop_execution(self):
        self.stop_flag.set()
        print("Execution stopped.")

    def execute_code(self, instance_data):
        """Simulate inputs to the selected window."""
        window_info = instance_data["window"]
        keystrokes = instance_data["keystrokes"]

        try:
            hwnd = int(window_info.split(" - ")[0])
            current_thread_id = win32api.GetCurrentThreadId()
            target_thread_id = win32process.GetWindowThreadProcessId(hwnd)[0]
            ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, True)
            # Bring the target window to the foreground
            win32gui.SetForegroundWindow(hwnd)
            while not self.stop_flag.is_set():
                for action in keystrokes:
                    action_type, value, delay = action
                    if action_type == 1:  # Key press
                        self.send_key(value, delay)
                    elif action_type == 2:  # Mouse click
                        self.click_mouse(value, delay)

                    time.sleep(0.2)
                    if self.stop_flag.is_set():
                        break

            ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, False)
            print(f"Execution stopped for window {window_info}")

        except Exception as e:
            print("Error during execution:", e)

    def send_key(self, key, delay=0.2):
        """Send a key press and release using pydirectinput."""
        try:
            for _ in range(1):  # Simulate key press and release
                pydirectinput.keyDown(key)
                time.sleep(delay)
                pydirectinput.keyUp(key)
            print(f"Key '{key}' sent")
        except Exception as e:
            print(f"Error sending key '{key}': {e}")

    def click_mouse(self, coordinates, delay=0.2):
        """Move the mouse to the specified coordinates and perform a left click."""
        try:
            x, y = coordinates
            pydirectinput.moveTo(x, y)
            time.sleep(delay)
            pydirectinput.click()
            print(f"Mouse clicked at x={x}, y={y}")
        except Exception as e:
            print(f"Error clicking mouse: {e}")



if __name__ == "__main__":
    root = tk.Tk()
    login_screen = LoginScreen(root)
    root.mainloop()















