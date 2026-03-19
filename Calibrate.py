import io
import json
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

# =========================
# ===== 加载配置 =====
# =========================

with open("config.json", encoding="utf-8") as _f:
    CFG = json.load(_f)

WINDOW_TITLE    = CFG["window_title"]
IMAGE_DIR       = CFG["image_dir"]
DIGIT_CONFIG    = CFG["digit"]
AREA_CONFIG     = CFG["calibrate_area"]
REFRESH_POS     = tuple(CFG["refresh_pos"])
TARGET_DIGITS   = set(CFG["target_digits"])
MAX_ROUNDS      = CFG["calibrate_max_rounds"]

# =========================
# ===== 窗口工具 =====
# =========================

_hwnd_cache = None

def get_hwnd():
    global _hwnd_cache
    if _hwnd_cache and win32gui.IsWindow(_hwnd_cache):
        return _hwnd_cache
    _hwnd_cache = win32gui.FindWindow(None, WINDOW_TITLE)
    if not _hwnd_cache:
        raise Exception(f"找不到窗口: {WINDOW_TITLE}")
    return _hwnd_cache

def get_window_origin():
    win_left, win_top, _, _ = win32gui.GetWindowRect(get_hwnd())
    return win_left, win_top

def click_relative(rel_x, rel_y):
    """点击窗口内相对坐标"""
    left, top, _, _ = win32gui.GetWindowRect(get_hwnd())
    abs_x = left + rel_x
    abs_y = top + rel_y
    win32api.SetCursorPos((abs_x, abs_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, abs_x, abs_y, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, abs_x, abs_y, 0, 0)

# =========================
# ===== 数字识别 =====
# =========================

def recognize_digit_ocr(img) -> int | None:
    """用 ddddocr 识别小图中的单个数字（0-3），失败返回 None"""
    img = img.convert("L").point(lambda x: 0 if x < 128 else 255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    text = ocr.classification(buf.getvalue()).strip()
    return int(text) if text in {str(d) for d in TARGET_DIGITS} else None

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
    """截取出售区域图，保存为 area0.png ~ area{count-1}.png"""
    cfg = AREA_CONFIG
    win_left, win_top = get_window_origin()
    print("正在保存区域模板图...")
    for i in range(cfg["count"]):
        abs_left = win_left + cfg["left"] + i * cfg["dx"]
        abs_top  = win_top  + cfg["top"]
        img = pyautogui.screenshot(region=(abs_left, abs_top, cfg["w"], cfg["h"]))
        path = os.path.join(IMAGE_DIR, f"area{i}.png")
        img.save(path)
        print(f"  已保存 {path}")

def calibrate_digit_templates():
    """
    循环扫描数字格子，识别到目标数字时保存为对应 {d}.png。
    未集齐则点击刷新，直到全部找到或达到 MAX_ROUNDS 上限。
    """
    found = {d: False for d in TARGET_DIGITS}
    print(f"开始校准数字模板，目标: {sorted(TARGET_DIGITS)}")

    for round_num in range(1, MAX_ROUNDS + 1):
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
        print(f"警告：达到最大轮数 {MAX_ROUNDS}，仍缺少: {[d for d, v in found.items() if not v]}")

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
    win_left, win_top = get_window_origin()
    img = pyautogui.screenshot(region=(win_left + 29, win_top + 431, 54, 42))
    img.save(os.path.join(IMAGE_DIR, "need0.png"))
    exit()
    main()