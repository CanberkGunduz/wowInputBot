from time import sleep
import win32gui, win32ui, win32con, win32api

#keybd_event can also be used
def main():
    window_name = "*File 2 - Not Defteri"
    hwnd = win32gui.FindWindow(None, window_name)
    print(get_inner_windows(hwnd))
    hwnd = get_inner_windows(hwnd)["Edit"]
    win = win32ui.CreateWindowFromHandle(hwnd)
    #win.SendMessage(win32con.WM_CHAR, ord('A'), 0)
    #win.SendMessage(win32con.WM_CHAR, ord('B'), 0)
    #win.SendMessage(win32con.WM_KEYDOWN, 0x1E, 0)
    #sleep(0.5)
    #win.SendMessage(win32con.WM_KEYUP, 0x1E, 0)
    while True:
        win32api.PostMessage(hwnd, win32con.WM_CHAR, ord('B'), 0)
        sleep(1.5)
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


