# -*- coding: utf-8 -*-
"""用 GitHub REST git-database API 把整个仓库推上去（绕过 github.com:443 git 传输在本机不通的问题）。

用法：python tools/push_via_api.py ["提交消息"]
- 凭据：从 git credential fill（Windows 凭据管理器）读取，绝不打印
- 每次运行重建一个提交并 force 更新 main 分支（本仓库只有我们在推）
- 提交前会打印将要上传的文件清单与大小，确认无 secret.py / .venv
"""
import base64
import datetime
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

OWNER, REPO, BRANCH = "renxiaxin777-droid", "jinji-ai-tour-guide", "main"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES = []  # 自动扫描（下方填充）
EXCLUDE_DIRS = {".venv", "__pycache__", ".git", ".idea", ".pytest_cache"}
EXCLUDE_FILES = {"secret.py", "_tmp_设计文档.html"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".log"}

MSG_DEFAULT = "update: 前端视觉改版（宣纸金体系）+ 竞赛提交材料（截图/简介/设计文档PDF/设计探索归档）"

COMMIT_MSG = (sys.argv[1] if len(sys.argv) > 1 else MSG_DEFAULT)

# 自动扫描项目全部待提交文件（排除敏感/临时/环境目录）
for _root, _dirs, _files in os.walk(ROOT):
    _dirs[:] = [d for d in _dirs if d not in EXCLUDE_DIRS]
    for _f in _files:
        if _f in EXCLUDE_FILES or os.path.splitext(_f)[1] in EXCLUDE_EXTS:
            continue
        _rel = os.path.relpath(os.path.join(_root, _f), ROOT).replace("\\", "/")
        FILES.append(_rel)
FILES.sort()

# ---- 凭据 ----
p = subprocess.run(["git", "credential", "fill"],
                   input="protocol=https\nhost=github.com\n\n",
                   capture_output=True, text=True)
kv = {}
for line in p.stdout.splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        kv[k.strip()] = v.strip()
token = kv.get("password", "")
if not token:
    print("✗ 未找到存储的 GitHub 凭据")
    sys.exit(2)

HDRS = {"Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "jinji-push"}


def call(method, url, body=None, tries=4):
    """带重试退避的 API 调用；链路抖动（SSL EOF/超时）与瞬时 404 都重试"""
    import time as _t
    last = None
    for i in range(tries):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=HDRS)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = (e.code, e.read().decode("utf-8", "ignore")[:120])
            if e.code in (404, 502, 503) and i < tries - 1:
                _t.sleep(2 * (i + 1))
                continue
            print(f"✗ {method} {url} → HTTP {e.code}: {last[1]}")
            sys.exit(1)
        except Exception as e:  # noqa: BLE001
            last = ("ERR", str(e)[:120])
            if i < tries - 1:
                _t.sleep(2 * (i + 1))
                continue
            print(f"✗ {method} {url} → {e}")
            sys.exit(1)
    print(f"✗ {method} {url} → 重试{tries}次仍失败: {last}")
    sys.exit(1)


API = f"https://api.github.com/repos/{OWNER}/{REPO}"

# ---- 0) 待传文件清单核对 ----
print("将要上传的文件：")
total = 0
for f in FILES:
    path = os.path.join(ROOT, f)
    if not os.path.isfile(path):
        print(f"✗ 缺失：{f}")
        sys.exit(1)
    size = os.path.getsize(path)
    total += size
    print(f"  - {f}  ({size} B)")
print(f"合计 {total} B；确认不含 secret.py / .venv / __pycache__\n")

# ---- 1) 创建 blobs ----
blobs = {}
for f in FILES:
    with open(os.path.join(ROOT, f), "rb") as fh:
        content = base64.b64encode(fh.read()).decode()
    r = call("POST", f"{API}/git/blobs", {"content": content, "encoding": "base64"})
    blobs[f] = r["sha"]
print(f"✓ blobs 创建完成：{len(blobs)} 个")

# ---- 2) 创建 tree ----
tree_entries = [{"path": f, "mode": "100644", "type": "blob", "sha": blobs[f]} for f in FILES]
tree = call("POST", f"{API}/git/trees", {"tree": tree_entries})
print("✓ tree 创建完成:", tree["sha"][:10])

# ---- 3) 创建 commit ----
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
who = {"name": "renxiaoxin777-droid", "email": "renxiaoxin777@gmail.com", "date": now}
commit = call("POST", f"{API}/git/commits",
              {"message": COMMIT_MSG, "author": who, "committer": who,
               "tree": tree["sha"], "parents": []})
print("✓ commit 创建完成:", commit["sha"][:10], "|", COMMIT_MSG)

# ---- 4) 更新分支 ref（不存在则创建）----
try:
    call("POST", f"{API}/git/refs", {"ref": f"refs/heads/{BRANCH}", "sha": commit["sha"]})
    print(f"✓ 新建分支 {BRANCH}")
except SystemExit:
    call("PATCH", f"{API}/git/refs/heads/{BRANCH}",
         {"sha": commit["sha"], "force": True})
    print(f"✓ 分支 {BRANCH} 已更新（force）")

# ---- 5) 验证 ----
head = call("GET", f"{API}/commits/{BRANCH}")
print("✓ 远端验证：", head["sha"][:10], "|", head["commit"]["message"][:40])
print("PUSH_OK")
