import io
import os
import time
import warnings
import logging

import pyautogui
import win32gui
import win32api
import win32con
import ddddocr

ocr = ddddocr.DdddOcr(show_ad=False)

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

IMAGE_DIR = "image"

# =========================
# ===== 窗口工具 =====
# =========================

_hwnd_cache = None

def get_hwnd(window_title="明日方舟"):
    global _hwnd_cache
    if _hwnd_cache and win32gui.IsWindow(_hwnd_cache):
        return _hwnd_cache
    _hwnd_cache = win32gui.FindWindow(None, window_title)
    if not _hwnd_cache:
        raise Exception(f"找不到窗口: {window_title}")
    return _hwnd_cache

def get_window_origin(window_title="明日方舟"):
    win_left, win_top, _, _ = win32gui.GetWindowRect(get_hwnd(window_title))
    return win_left, win_top

def click_relative(rel_x, rel_y, window_title="明日方舟"):
    """点击窗口内相对坐标"""
    left, top, _, _ = win32gui.GetWindowRect(get_hwnd(window_title))
    abs_x = left + rel_x
    abs_y = top + rel_y
    win32api.SetCursorPos((abs_x, abs_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, abs_x, abs_y, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, abs_x, abs_y, 0, 0)

# =========================
# ===== 参数配置 =====
# =========================

DIGIT_CONFIG = {
    "left":  464,
    "top":   593,
    "dx":    147,
    "w":     10,
    "h":     16,
    "count": 5,
}

REFRESH_POS  = (1228, 526)
TARGET_DIGITS = {0, 1, 2, 3}

# =========================
# ===== 数字识别 =====
# =========================

def recognize_digit_ocr(img) -> int | None:
    """用 ddddocr 识别小图中的单个数字（0-3），失败返回 None"""
    img = img.convert("L").point(lambda x: 0 if x < 128 else 255)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    text = ocr.classification(buf.getvalue()).strip()

    return int(text) if text in ('0', '1', '2', '3') else None

# =========================
# ===== 截图工具 =====
# =========================

def screenshot_digit_slot(slot_index: int):
    """截取第 slot_index 个数字格子的图片"""
    cfg = DIGIT_CONFIG
    win_left, win_top = get_window_origin()
    abs_left = win_left + cfg["left"] + slot_index * cfg["dx"]
    abs_top  = win_top  + cfg["top"]
    return pyautogui.screenshot(region=(abs_left, abs_top, cfg["w"], cfg["h"]))

# =========================
# ===== 校准函数 =====
# =========================

def calibrate_area_images():
    """截取10个出售区域图，保存为 area0.png ~ area9.png"""
    left, top, dx, w, h = 188, 499, 82, 82, 67
    win_left, win_top = get_window_origin()
    print("正在保存区域模板图...")
    for i in range(10):
        img = pyautogui.screenshot(region=(win_left + left + i * dx, win_top + top, w, h))
        path = os.path.join(IMAGE_DIR, f"area{i}.png")
        img.save(path)
        print(f"  已保存 {path}")

def calibrate_digit_templates(max_rounds: int = 20):
    """
    循环扫描5个数字格子，识别到 0/1/2/3 时保存为对应 {d}.png。
    未集齐则点击刷新，直到全部找到或达到 max_rounds 上限。
    """
    found = {d: False for d in TARGET_DIGITS}
    print(f"开始校准数字模板，目标: {sorted(TARGET_DIGITS)}")

    for round_num in range(1, max_rounds + 1):
        missing = [d for d, v in found.items() if not v]
        print(f"\n=== 第 {round_num} 轮扫描 | 缺少: {missing} ===")

        for slot in range(DIGIT_CONFIG["count"]):
            img = screenshot_digit_slot(slot)
            digit = recognize_digit_ocr(img)
            print(f"  槽位 {slot}: 识别到 {digit}")

            if digit is not None and digit in TARGET_DIGITS and not found[digit]:
                path = os.path.join(IMAGE_DIR, f"{digit}.png")
                img.save(path)
                found[digit] = True
                print(f"  已保存 {path}（共找到 {sum(found.values())}/{len(TARGET_DIGITS)}）")

        if all(found.values()):
            break

        print("  未集齐，点击刷新...")
        click_relative(*REFRESH_POS)
        time.sleep(0.5)
    else:
        print(f"警告：达到最大轮数 {max_rounds}，仍缺少: {[d for d, v in found.items() if not v]}")

    print(f"\n数字模板校准完成，已找到: {sorted(d for d, v in found.items() if v)}")

# =========================
# ===== 入口 =====
# =========================

def main():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    print("3秒后开始校准，请切换到游戏窗口...")
    time.sleep(3)
    calibrate_area_images()
    calibrate_digit_templates()
    print("\n校准完成！")

if __name__ == "__main__":
    main()