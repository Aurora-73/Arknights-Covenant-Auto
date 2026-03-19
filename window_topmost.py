import win32gui
import win32con

def set_window_topmost(zhiding=True):
    window_title="明日方舟"
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise Exception(f"找不到窗口: {window_title}")
    
    if zhiding:
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    else:
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


set_window_topmost(True)