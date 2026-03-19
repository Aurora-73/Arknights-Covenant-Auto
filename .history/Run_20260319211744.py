import runpy
from datetime import datetime
import urllib.request
import urllib.parse
import traceback

SCRIPT_PATH = r"_Run_.py"
SCT_URL = "https://sctapi.ftqq.com/SCT259530TniDHi0FTZuMoLafxntCzAJG6.send" # 可选，sever酱通知接口地址

# 记录开始时间
start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 运行脚本并捕获异常信息（不在此处终止程序）
exception_info = None
try:
    runpy.run_path(SCRIPT_PATH, run_name="__main__")
    succeeded = True
except BaseException:
    succeeded = False
    exception_info = traceback.format_exc()

# 运行结束时间
end_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 根据是否发生异常构建不同的通知内容
if succeeded:
    title = "卫戍协议自动 运行结束"
    desp = f"脚本正常结束。\n开始：{start_ts}\n结束：{end_ts}"
else:
    title = "卫戍协议自动 异常退出"
    # 将异常信息包含在 desp 中（必要时可截断）
    ex = exception_info or "无异常信息"
    desp = f"脚本异常退出。\n开始：{start_ts}\n结束：{end_ts}\n异常信息：\n{ex}"

# 发送 Server 酱通知（发送过程继续忽略异常）
try:
    data = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
    req = urllib.request.Request(SCT_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        _ = resp.read()
except BaseException:
    pass