#!/usr/bin/env python3
"""
Python ICMP pinger -> Uptime Kuma pusher
Config via env:
  MONITORS: newline-separated entries "host|https://uptime-kuma/api/push/<token>"
  INTERVAL: seconds between checks (default 30)
  PING_COUNT: pings per cycle (default 1)
  PING_TIMEOUT_S: per-ping timeout seconds (default 1)
  FORCE_IPV4: "true"|"false" (default true)
  SEND_DOWN: "true"|"false" (default true)
"""

import os, time, platform, subprocess, re, urllib.parse, urllib.request, sys

INTERVAL = int(os.getenv("INTERVAL", "30"))
PING_COUNT = int(os.getenv("PING_COUNT", "1"))
PING_TIMEOUT_S = int(os.getenv("PING_TIMEOUT_S", "1"))
FORCE_IPV4 = os.getenv("FORCE_IPV4", "true").lower() == "true"
SEND_DOWN = os.getenv("SEND_DOWN", "true").lower() == "true"

raw_monitors = os.getenv("MONITORS", "").strip()
if not raw_monitors:
    print("ERROR: MONITORS is empty. Provide lines like 'host|https://.../api/push/<token>'", file=sys.stderr)
    sys.exit(1)

MONITORS = []
for line in raw_monitors.splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    try:
        host, base = line.split("|", 1)
    except ValueError:
        print(f"WARN: skipping malformed line: {line}", file=sys.stderr)
        continue
    MONITORS.append((host.strip(), base.strip()))

_TIME_REGEXES = [
    re.compile(r"time[=<]\s*([0-9]+(?:\.[0-9]+)?)\s*ms", re.IGNORECASE),
    re.compile(r"Average\s*=\s*([0-9]+)\s*ms", re.IGNORECASE),  # Windows summary
]

def _ping_cmd(host: str):
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", str(PING_COUNT), "-w", str(PING_TIMEOUT_S * 1000), host]
        if FORCE_IPV4:
            cmd.insert(1, "-4")
        return cmd
    else:
        cmd = ["ping", "-c", str(PING_COUNT), "-W", str(PING_TIMEOUT_S), host]
        if FORCE_IPV4:
            cmd.insert(1, "-4")
        return cmd

def ping_ms(host: str):
    try:
        proc = subprocess.run(
            _ping_cmd(host),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=max(PING_TIMEOUT_S * 2, 3),
        )
    except Exception:
        return None

    if proc.returncode != 0:
        return None

    out = proc.stdout or ""
    for rx in _TIME_REGEXES:
        m = rx.search(out)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                return 0.0
    return 0.0

def push(base_url: str, status: str, msg: str, ping_val):
    params = {"status": status, "msg": msg}
    if ping_val is not None and ping_val != "":
        params["ping"] = f"{float(ping_val):.2f}"
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=5):
        pass

print(f"Starting kuma pusher: {len(MONITORS)} monitor(s), interval={INTERVAL}s", file=sys.stderr)
while True:
    for host, base in MONITORS:
        rtt = ping_ms(host)
        if rtt is not None:
            try:
                push(base, "up", "OK", rtt)
            except Exception as e:
                print(f"WARN push failed for {host} (up): {e}", file=sys.stderr)
        else:
            if SEND_DOWN:
                try:
                    push(base, "down", "no reply", None)
                except Exception as e:
                    print(f"WARN push failed for {host} (down): {e}", file=sys.stderr)
    time.sleep(INTERVAL)
