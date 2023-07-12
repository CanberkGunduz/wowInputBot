import tkinter as tk
import keyboard
import random
from time import sleep
import win32gui, win32ui, win32con, win32api
import threading
import os


class InstanceWindow:
    def __init__(self, instance_name):
        self.instance_name = instance_name
        self.key_inputs = []
        self.selected_window = ""
        self.root = tk.Toplevel(root)
        self.root.title(f"Window Selector - {instance_name}")
        self.root.geometry(f"+{-180 + int(instance_name[-1]) * 170}+350")
        # Dropdown Button
        self.dropdown = tk.StringVar(self.root)
        self.dropdown.set("Select a Window")
        self.dropdown_menu = tk.OptionMenu(self.root, self.dropdown, *self.get_open_windows())
        self.dropdown_menu.pack(pady=10)

        # Empty Square Space
        self.keystrokes_list = tk.Listbox(self.root, width=30, height=10)
        self.keystrokes_list.pack()

        # Add and Save Buttons (same row)
        self.add_save_frame = tk.Frame(self.root)
        self.add_save_frame.pack(pady=10)

        self.add_button = tk.Button(self.add_save_frame, text="Add", command=self.add_keystroke)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(self.add_save_frame, text="Save", command=self.save_to_file)
        self.save_button.pack(side=tk.LEFT, padx=5)

        # Start and Stop Buttons (same row)
        self.start_stop_frame = tk.Frame(self.root)
        self.start_stop_frame.pack(pady=10)

        self.start_button = tk.Button(self.start_stop_frame, text="Start", command=self.start_execution)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(self.start_stop_frame, text="Stop", command=self.stop_execution)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Load key inputs from file
        self.load_from_file()

        self.dropdown.trace("w", self.on_dropdown_change)  # Register callback function

    def get_open_windows(self):
        windows = []

        def callback(hwnd, windows):
            window_title = win32gui.GetWindowText(hwnd)
            if window_title.strip():  # Exclude empty window names
                window_id = hwnd
                windows.append((f"{window_id} - {window_title}"))

        win32gui.EnumWindows(callback, windows)
        return windows

    def get_inner_windows(self, whndl):
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                hwnds[win32gui.GetClassName(hwnd)] = hwnd
            return True

        hwnds = {}
        win32gui.EnumChildWindows(whndl, callback, hwnds)
        return hwnds

    def add_keystroke(self):
        if self.selected_window != "":
            self.record_window(self.selected_window)

    def record_window(self, window_name):
        record_window = tk.Toplevel(self.root)
        record_window.title("Record Keystrokes")
        record_window.geometry("300x250")

        keystroke_label = tk.Label(record_window, text="Press a key to record keystroke:")
        keystroke_label.pack(pady=10)

        keystroke_var = tk.StringVar()
        keystroke_entry = tk.Entry(record_window, textvariable=keystroke_var, state='disabled')
        keystroke_entry.pack(pady=5)

        float_frame = tk.Frame(record_window)
        float_frame.pack(pady=5)

        float_label = tk.Label(float_frame, text="Enter the delay range:")
        float_label.pack()

        float_var_1 = tk.DoubleVar()
        float_entry_1 = tk.Entry(float_frame, textvariable=float_var_1, width=8)
        float_entry_1.pack(side=tk.LEFT)

        minus_label = tk.Label(float_frame, text="-")
        minus_label.pack(side=tk.LEFT)

        float_var_2 = tk.DoubleVar()
        float_entry_2 = tk.Entry(float_frame, textvariable=float_var_2, width=8)
        float_entry_2.pack(side=tk.LEFT)

        def start_recording():
            keyboard.on_press(record_keystroke)
            record_button.config(state="disabled")

        def record_keystroke(event):
            keystroke_var.set(event.name)
            stop_recording()

        def stop_recording():
            keyboard.unhook_all()
            submit_button.config(state="normal")

        def submit_values():
            keystroke = keystroke_var.get()
            float_value_1 = float_var_1.get()
            float_value_2 = float_var_2.get()
            self.key_inputs.append((keystroke, float_value_1, float_value_2))
            self.keystrokes_list.insert(tk.END, f"Key: {keystroke} - Delay Range: {float_value_1} - {float_value_2}")
            record_window.destroy()

        record_button = tk.Button(record_window, text="Record", command=start_recording)
        record_button.pack(pady=10)

        submit_button = tk.Button(record_window, text="Submit", command=submit_values, state="disabled")
        submit_button.pack(pady=10)

    def execute_code(self):
        print("Execution started")
        print(self.selected_window)
        print(self.key_inputs)

        if self.selected_window:
            window_id = self.selected_window.split(" - ")[0]
            hwnd = int(window_id)
            win = win32ui.CreateWindowFromHandle(hwnd)
            #hwnd = self.get_inner_windows(hwnd)["Edit"]
            while True:
                for keystroke, float1, float2 in self.key_inputs:
                    if self.stop_flag.is_set():
                        print("Execution stopped")
                        return
                    adjusted_delay = random.uniform(float1, float2)

                    ascii_value = ord(keystroke)
                    hex_representation = int(hex(ascii_value),16)
                    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, hex_representation, 0)
                    sleep(random.randrange(1, 9) / 10)
                    win32api.PostMessage(hwnd, win32con.WM_KEYUP, hex_representation, 0)
                    #print("Slept for:",adjusted_delay)
                    sleep(adjusted_delay)


        print("Execution completed")

    def start_execution(self):
        self.stop_flag = threading.Event()
        t = threading.Thread(target=self.execute_code)
        t.start()

    def stop_execution(self):
        self.stop_flag.set()

    def save_to_file(self):
        filename = f"{self.instance_name}.txt"
        with open(filename, "w") as file:
            for keystroke, float_value_1, float_value_2 in self.key_inputs:
                file.write(f"Key: {keystroke} - Delay Range: {float_value_1} - {float_value_2}\n")
        print("Saved to file:", filename)

    def load_from_file(self):
        filename = f"{self.instance_name}.txt"
        if os.path.exists(filename):
            with open(filename, "r") as file:
                lines = file.readlines()
                for line in lines:
                    if "Key: " in line and " - Delay Range: " in line:
                        keystroke = line.split("Key: ")[1].split(" - Delay Range: ")[0].strip()
                        delay_range = line.split(" - Delay Range: ")[1].strip()
                        float_value_1, float_value_2 = map(float, delay_range.split(" - "))
                        self.key_inputs.append((keystroke, float_value_1, float_value_2))
                        self.keystrokes_list.insert(tk.END,
                                                    f"Key: {keystroke} - Delay Range: {float_value_1} - {float_value_2}")
            print("Loaded from file:", filename)
        else:
            print("File not found:", filename)

    def on_dropdown_change(self, *args):
        self.selected_window = self.dropdown.get()


def open_instance(instance_name):
    instance_window = InstanceWindow(instance_name)


root = tk.Tk()
root.title("Window Selector")
root.geometry("400x100+0+220")  # Set the window size

# Create instance buttons
instance_frame1 = tk.Frame(root)
instance_frame1.pack(pady=10)

instance_frame2 = tk.Frame(root)
instance_frame2.pack(pady=10)

instances_row1 = ["Instance 1", "Instance 2", "Instance 3", "Instance 4"]
instances_row2 = ["Instance 5", "Instance 6", "Instance 7", "Instance 8"]

for instance_name in instances_row1:
    instance_button = tk.Button(instance_frame1, text=instance_name,
                                command=lambda name=instance_name: open_instance(name))
    instance_button.pack(side=tk.LEFT, padx=10)

for instance_name in instances_row2:
    instance_button = tk.Button(instance_frame2, text=instance_name,
                                command=lambda name=instance_name: open_instance(name))
    instance_button.pack(side=tk.LEFT, padx=10)

root.mainloop()