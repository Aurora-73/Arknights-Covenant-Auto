import pyautogui
import win32gui
import win32api
import win32con
import time
import numpy as np
import easyocr
import warnings
import logging
import ddddocr

ocr = ddddocr.DdddOcr(show_ad=False)

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

reader = easyocr.Reader(['en'], gpu=False, verbose=False)

# =========================
# ===== 窗口工具 =====
# =========================

def get_window_origin(window_title="明日方舟"):
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise Exception(f"找不到窗口: {window_title}")
    win_left, win_top, _, _ = win32gui.GetWindowRect(hwnd)
    return win_left, win_top

def click_relative(rel_x, rel_y, window_title="明日方舟"):
    """点击窗口内相对坐标"""
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise Exception(f"找不到窗口: {window_title}")
    left, top, _, _ = win32gui.GetWindowRect(hwnd)
    abs_x = left + rel_x
    abs_y = top + rel_y
    win32api.SetCursorPos((abs_x, abs_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, abs_x, abs_y, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, abs_x, abs_y, 0, 0)

# =========================
# ===== 参数配置 =====
# =========================

# 数字区域（窗口相对坐标）
DIGIT_CONFIG = {
    "left": 464,
    "top":  593,
    "dx":   147,
    "w":    10,
    "h":    16,
    "count": 5,
}

# 刷新按钮（窗口相对坐标）
REFRESH_POS = (1228, 526)

# 目标数字集合
TARGET_DIGITS = {0, 1, 2, 3}

# =========================
# ===== 数字识别 =====
# =========================

def recognize_digit_ocr(img) -> int | None:
    """
    用 ddddocr 识别小图中的单个数字（0-3）。
    返回识别到的 int，失败返回 None。
    """
    # 二值化处理
    img = img.convert("L")
    img = img.point(lambda x: 0 if x < 128 else 255)

    # 上下左右补充3个像素的黑色边框

    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = ocr.classification(buf.getvalue())

    text = result.strip()
    if text in ('0', '1', '2', '3'):
        return int(text)
    return None

# =========================
# ===== 区域截图工具 =====
# =========================

def screenshot_digit_slot(slot_index: int):
    """截取第 slot_index 个数字格子的图片"""
    cfg = DIGIT_CONFIG
    win_left, win_top = get_window_origin()
    abs_left = win_left + cfg["left"] + slot_index * cfg["dx"]
    abs_top  = win_top  + cfg["top"]
    return pyautogui.screenshot(region=(abs_left, abs_top, cfg["w"], cfg["h"]))

# =========================
# ===== 区域图校准（仅首次） =====
# =========================

def calibrate_area_images():
    """一次性截取10个出售区域图，保存为 area0.png ~ area9.png"""
    left = 188
    top  = 499
    dx   = 82
    w, h = 82, 67
    win_left, win_top = get_window_origin()
    print("正在保存区域模板图...")
    for i in range(10):
        abs_left = win_left + left + i * dx
        abs_top  = win_top  + top
        img = pyautogui.screenshot(region=(abs_left, abs_top, w, h))
        img.save(f"image\\area{i}.png")
        print(f"  已保存 area{i}.png")

# =========================
# ===== 主校准逻辑 =====
# =========================

def calibrate_digit_templates():
    """
    循环扫描5个数字格子，识别到 0/1/2/3 时保存为对应 {d}.png。
    未集齐则点击刷新，直到 {0,1,2,3} 全部找到为止。
    """
    found: dict[int, bool] = {d: False for d in TARGET_DIGITS}
    refresh_x, refresh_y = REFRESH_POS
    round_num = 0
    try_cnt = 0
    print(f"开始校准数字模板，目标: {sorted(TARGET_DIGITS)}")

    while not all(found.values()) and try_cnt < 20:
        try_cnt += 1
        round_num += 1
        missing = [d for d, v in found.items() if not v]
        print(f"\n=== 第 {round_num} 轮扫描 | 缺少: {missing} ===")

        for slot in range(DIGIT_CONFIG["count"]):
            img = screenshot_digit_slot(slot)
            digit = recognize_digit_ocr(img)
            print(f"  槽位 {slot}: 识别到 {digit}")

            if digit is not None and digit in TARGET_DIGITS and not found[digit]:
                img.save(f"image\\{digit}.png")
                found[digit] = True
                print(f"  已保存 image\\{digit}.png（共找到 {sum(found.values())}/{len(TARGET_DIGITS)}）")

        if all(found.values()):
            break

        # 还有未找到的，点击刷新
        print(f"  未集齐，点击刷新...")
        click_relative(*REFRESH_POS)
        time.sleep(0.5)  # 等待刷新动画

    print(f"\n 全部数字模板已保存: {sorted(TARGET_DIGITS)}")

# =========================
# ===== 入口 =====
# =========================

print("3秒后开始校准，请切换到游戏窗口...")
time.sleep(3)

# 1. 先保存区域模板（只需一次）
calibrate_area_images()

# 2. 循环校准数字模板
calibrate_digit_templates()

print("\n校准完成！")