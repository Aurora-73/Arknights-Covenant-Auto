from datetime import datetime
import urllib.request
import urllib.parse
import traceback
from _Run_ import run

# 运行前需要先校准，运行 Calibrate.py

SCT_URL = "https://sctapi.ftqq.com/.send" # 使用server酱

start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

exception_info = None
# 点击 win + D 结束运行
try:
    # max_rounds：最大运行次数，balance_threshold：当余额小于阈值，不再买入1费以上干员
    run(max_rounds=9999999, _balance_threshold_=50)
    succeeded = True
except BaseException:
    succeeded = False
    exception_info = traceback.format_exc()

end_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if succeeded:
    title = "卫戍协议自动 运行结束"
    desp = f"脚本正常结束。\n开始：{start_ts}\n结束：{end_ts}"
else:
    title = "卫戍协议自动 异常退出"
    ex = exception_info or "无异常信息"
    desp = f"脚本异常退出。\n开始：{start_ts}\n结束：{end_ts}\n异常信息：\n{ex}"

print(desp)

try:
    data = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
    req = urllib.request.Request(SCT_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        _ = resp.read()
except BaseException:
    pass

