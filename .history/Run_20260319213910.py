from datetime import datetime
import urllib.request
import urllib.parse
import traceback
from _Run_ import run

# 运行前需要先校准，运行 Calibrate.py

SCT_URL = "https://sctapi.ftqq.com/SCT259530TniDHi0FTZuMoLafxntCzAJG6.send"

start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

exception_info = None
try:
    run(max_rounds=9999999)
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

try:
    data = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
    req = urllib.request.Request(SCT_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        _ = resp.read()
except BaseException:
    pass