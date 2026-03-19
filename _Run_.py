import io
import json
import pyautogui  
import time
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity as ssim
import ctypes
import cv2
import win32gui
import os
import warnings
import logging
from datetime import datetime
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
LOG_PATH        = CFG["log_path"]
PURCHASE_CONFIG = CFG["purchase"]
SALE_CONFIG     = CFG["sale"]
REFRESH_POS     = tuple(CFG["refresh_pos"])
CONFIRM_POS     = tuple(CFG["confirm_pos"])
BALANCE_REGION  = CFG["balance_region"]
NEED_CHECK_REGION = CFG["need_check_region"]
WATCH_RATIO     = CFG["watch_region_ratio"]

# ===== DPI 适配 =====
ctypes.windll.user32.SetProcessDPIAware()
pyautogui.FAILSAFE = False

balance = 0
balance_threshold = 10
need_buy_count = 0

# =========================
# ===== 窗口坐标工具 =====
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

def get_watch_region():
    hwnd = get_hwnd()
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    w = right - left
    h = bottom - top
    watch_h = int(h * WATCH_RATIO)
    return (left, top, w, watch_h)

def to_abs(x, y):
    hwnd = get_hwnd()
    left, top, _, _ = win32gui.GetWindowRect(hwnd)
    return left + x, top + y

# =========================
# ===== 图像处理工具 =====
# =========================

def preprocess_digit(img):
    img = img.convert("L")
    img = img.point(lambda x: 0 if x < 128 else 255)
    return np.array(img)

def preprocess_area(img):
    img = img.convert("L")
    return np.array(img)

def screenshot_region(left, top, w, h):
    abs_left, abs_top = to_abs(left, top)
    return pyautogui.screenshot(region=(abs_left, abs_top, w, h))

def double_click(x, y):
    pyautogui.click(x, y)
    pyautogui.click(x, y)

def compute_center(left, top, w, h):
    return left + w // 2, top + h // 2

def img_to_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# =========================
# ===== 模板加载 =====
# =========================

def load_digit_templates():
    return {d: preprocess_digit(Image.open(os.path.join(IMAGE_DIR, f"{d}.png"))) for d in range(5)}

def load_area_templates():
    return [preprocess_area(Image.open(os.path.join(IMAGE_DIR, f"area{i}.png"))) for i in range(SALE_CONFIG["count"])]

def load_need_templates():
    return [preprocess_area(Image.open(os.path.join(IMAGE_DIR, f"need{i}.png"))) for i in range(2)]

digit_templates = load_digit_templates()
area_templates  = load_area_templates()
need_templates  = load_need_templates()

# =========================
# ===== 日志工具 =====
# =========================

def write_log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

# =========================
# ===== 核心逻辑 =====
# =========================

def recognize_digit(img_np):
    best_digit, best_score = None, -1
    for d, tmpl in digit_templates.items():
        score = ssim(img_np, tmpl)
        if score > best_score:
            best_score = score
            best_digit = d
    return best_digit, best_score

def check_need_purchase():
    """检查是否需要购买，比较区域与need模板的相似度"""
    ncr = NEED_CHECK_REGION
    img = screenshot_region(ncr["left"], ncr["top"], ncr["w"], ncr["h"])
    img_np = preprocess_area(img)
    labels = ["单次叠加", "特异化"]
    for i, tmpl in enumerate(need_templates):
        score = ssim(img_np, tmpl)
        print(f"  {labels[i]}相似度={score:.4f}")
        if score > 0.8:
            global need_buy_count
            need_buy_count += 1
            return True
    return False

def bulkPurchase():
    global balance
    cfg = PURCHASE_CONFIG
    left = cfg["left"]

    for i in range(cfg["count"]):
        img = screenshot_region(left, cfg["top"], cfg["w"], cfg["h"])
        img_np = preprocess_digit(img)
        digit, score = recognize_digit(img_np)

        click_x, click_y = to_abs(left + cfg["w"] // 2, cfg["top"] + cfg["offset_y"])

        if digit is not None and digit < 2:
            print(f" -> 触发双击 ({click_x}, {click_y})")
            double_click(click_x, click_y)
            time.sleep(0.1)
        elif digit is not None and digit < 4 and balance > balance_threshold:
            print(f" -> 单击检查是否需要购买 ({click_x}, {click_y})")
            pyautogui.click(click_x, click_y)
            time.sleep(0.1)
            if check_need_purchase():
                print(f" -> 需要购买，触发双击")
                double_click(click_x, click_y)
                time.sleep(0.1)
            else:
                print(f" -> 不需要购买，跳过")

        left += cfg["dx"]

def bulkSale():
    cfg = SALE_CONFIG
    to_sell = []
    left = cfg["left"]

    # 第一阶段：扫描
    for i in range(cfg["count"]):
        img = screenshot_region(left, cfg["top"], cfg["w"], cfg["h"])
        img_np = preprocess_area(img)
        score = ssim(img_np, area_templates[i])
        print(f"[{i}] 相似度={score:.4f}")
        if 0.2 < score < 0.8:
            center_x, center_y = compute_center(left, cfg["top"], cfg["w"], cfg["h"])
            to_sell.append((i, center_x, center_y))
        left += cfg["dx"]

    print(f"需要出售的位置: {[i for i, _, _ in to_sell]}")

    # 第二阶段：出售
    confirm_x, confirm_y = to_abs(*CONFIRM_POS)
    for i, center_x, center_y in to_sell:
        abs_x, abs_y = to_abs(center_x, center_y)
        pyautogui.click(abs_x, abs_y)
        time.sleep(0.1)
        pyautogui.click(confirm_x, confirm_y)
        pyautogui.click(confirm_x, confirm_y)
        time.sleep(0.2)

def grab_region_gray():
    region = get_watch_region()
    img = pyautogui.screenshot(region=region)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

def calc_similarity(img1, img2):
    return ssim(img1, img2)

def recognize_balance():
    global balance
    time.sleep(0.1)
    win_left, win_top, _, _ = win32gui.GetWindowRect(get_hwnd())
    br = BALANCE_REGION
    abs_left = win_left + br["offset_x"]
    abs_top  = win_top  + br["offset_y"]

    for attempt in range(3):
        img = pyautogui.screenshot(region=(abs_left, abs_top, br["w"], br["h"]))
        text = ocr.classification(img_to_bytes(img)).strip()
        if text.isdigit():
            return int(text)
        time.sleep(0.1)

    print("余额识别失败3次，保持原值")
    return balance

def check_and_raise_if_changed(baseline, round_idx: int):
    """对比当前界面与基准，变化过大则记录日志并抛出异常"""
    current = grab_region_gray()
    if calc_similarity(baseline, current) < 0.8:
        msg = "界面变化过大，停止运行！"
        print(msg)
        # 清空print缓冲区
        import sys
        sys.stdout.flush()
        write_log(f"第 {round_idx} 轮：{msg}")
        raise RuntimeError(msg)

# =========================
# ===== 主循环入口 =====
# =========================

def run(max_rounds: int = 999999, _balance_threshold_: int = 10):
    global balance
    global balance_threshold
    balance_threshold = _balance_threshold_
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("===== 脚本启动 =====\n")

    time.sleep(3)

    print("获取基准界面...")
    baseline = grab_region_gray()

    for i in range(max_rounds):
        print(f"\n===== 第 {i} 轮 =====")

        check_and_raise_if_changed(baseline, i)
        bulkPurchase()

        refresh_x, refresh_y = to_abs(*REFRESH_POS)
        pyautogui.click(refresh_x, refresh_y)
        time.sleep(0.1)

        check_and_raise_if_changed(baseline, i)
        bulkSale()
        time.sleep(0.1)
        
        balance = recognize_balance()
        print(f"识别余额: {balance}")
        if _balance_threshold_ == 99 and balance == 99:
            print("仅刷钱模式，已完成刷取，自动退出")
            return

        write_log(f"第 {i} 轮结束 | 当前余额: {balance} | 叠加次数 {need_buy_count}")

    write_log("===== 已完成全部轮次 =====")


if __name__ == "__main__":
    run()