import time

#from pywinauto import Application

# Example usage
window_titles = ["File 1 - Not Defteri","File 2 - Not Defteri","File 3 - Not Defteri","File 4 - Not Defteri",]  # Replace with the titles of the text files
input_texts = ["Input 1", "Input 2", "Input 3", "Input 4"]  # Replace with the input texts

# for title, text in zip(window_titles, input_texts):
#     app = Application().connect(title=title)
#     app.window(title=title).type_keys(text)

# app = Application().connect(title="*File 1 - Not Defteri")
# while True:
#     app.window(title="*File 1 - Not Defteri").type_keys("1")
#     time.sleep(1)

import win32gui
import win32con
import win32api
from time import sleep
import win32gui, win32ui, win32con, win32api


def main():
    window_name = "World of Warcraft"
    hwnd = win32gui.FindWindow(None, window_name)
    #list_window_names()
    print(get_inner_windows(hwnd))
    #hwnd = get_inner_windows(hwnd)["Edit"]
    win = win32ui.CreateWindowFromHandle(hwnd)

    #win.SendMessage(win32con.WM_CHAR, ord('A'), 0)
    #win.SendMessage(win32con.WM_CHAR, ord('B'), 0)
    #win.SendMessage(win32con.WM_KEYDOWN, 0x1E, 0)
    #sleep(0.5)
    #win.SendMessage(win32con.WM_KEYUP, 0x1E, 0)
    ascii_value = ord("1")
    hex_representation = hex(ascii_value)
    print(type(hex_representation))
    print(type(0x31))
    he=int(hex_representation,16)
    while True:
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, he, 0)
        time.sleep(1)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, he, 0)
        #win32api.PostMessage(hwnd, win32con.WM_CHAR, ord('1'), 0)
        #sleep(2)
    # win32api.SendMessage(hwnd, win32con.WM_KEYUP, 0x41, 0)


def list_window_names():
    def winEnumHandler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            print(hex(hwnd), '"' + win32gui.GetWindowText(hwnd) + '"')
    win32gui.EnumWindows(winEnumHandler, None)


def get_inner_windows(whndl):
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            hwnds[win32gui.GetClassName(hwnd)] = hwnd
        return True
    hwnds = {}
    win32gui.EnumChildWindows(whndl, callback, hwnds)
    return hwnds

main()


