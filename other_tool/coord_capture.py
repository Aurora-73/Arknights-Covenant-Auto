import win32gui
import win32api
import pyautogui
import time

WINDOW_TITLE = "明日方舟"


def get_hwnd(window_title=WINDOW_TITLE):
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise Exception(f"找不到窗口: {window_title}")
    return hwnd


def get_mouse_pos_relative_to_window(window_title=WINDOW_TITLE):
    hwnd = get_hwnd(window_title)
    left, top, _, _ = win32gui.GetWindowRect(hwnd)
    mouse_x, mouse_y = win32api.GetCursorPos()
    return mouse_x - left, mouse_y - top


def screenshot_region_abs(abs_left, abs_top, w, h, save_path):
    img = pyautogui.screenshot(region=(abs_left, abs_top, w, h))
    img.save(save_path)


def main(window_title=WINDOW_TITLE, save_path="region.png", delay=3.0):
    print(f"请将鼠标移到第一个位置（左上角），{delay:.0f}秒后记录...")
    time.sleep(delay)
    x1, y1 = get_mouse_pos_relative_to_window(window_title)
    print(f"第一个位置（左上角）: ({x1}, {y1})")

    print(f"请将鼠标移到第二个位置（右下角），{delay:.0f}秒后记录...")
    time.sleep(delay)
    x2, y2 = get_mouse_pos_relative_to_window(window_title)
    print(f"第二个位置（右下角）: ({x2}, {y2})")

    rect_left   = min(x1, x2)
    rect_top    = min(y1, y2)
    w = abs(x2 - x1)
    h = abs(y2 - y1)

    print(f"\n矩形区域（窗口坐标）: 左上角=({rect_left}, {rect_top})  宽={w}  高={h}")

    # 转为屏幕绝对坐标截图
    win_left, win_top, _, _ = win32gui.GetWindowRect(get_hwnd(window_title))
    screenshot_region_abs(win_left + rect_left, win_top + rect_top, w, h, save_path)
    print(f"已保存截图: {save_path}")

    print(f"""
# 可直接复制到脚本的参数：
left = {rect_left}
top  = {rect_top}
w, h = {w}, {h}
""")


if __name__ == "__main__":
    main()