import win32api
import win32gui
import time

# 手动获取位置 先运行脚本，3秒内将鼠标移到游戏窗口内想记录的位置，程序打印出相对坐标

def get_mouse_pos_relative_to_window(window_title="明日方舟"):
    # 1. 找到目标窗口句柄
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise Exception(f"找不到窗口: {window_title}")
    
    # 2. 获取窗口在屏幕上的位置（左上角坐标）
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    
    # 3. 获取当前鼠标的全局坐标
    mouse_x, mouse_y = win32api.GetCursorPos()
    
    # 4. 计算相对坐标
    rel_x = mouse_x - left
    rel_y = mouse_y - top
    
    return rel_x, rel_y


time.sleep(3)
x, y = get_mouse_pos_relative_to_window("明日方舟")
print(f"相对于窗口的位置: ({x}, {y})")