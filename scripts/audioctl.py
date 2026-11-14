#!/usr/bin/env python3
"""audioctl: one stdlib-only CLI over the home-audio backends.

Talks to Music Assistant (HTTP command bus), Lyrion/LMS (JSON-RPC), Snapcast
(JSON-RPC over HTTP) and Home Assistant (REST), and scans the LAN for audio
servers and players. Output is JSON unless a command says otherwise.

Settings come from the overlay's profile.env (see scripts/overlay-paths.sh),
then the environment, which wins. Tokens are never stored in profile.env:
profile.env names the environment variable that holds each token.

  audioctl.py config
  audioctl.py ma players/all
  audioctl.py ma player_queues/play_media '{"queue_id":"<id>","media":"library://playlist/1"}'
  audioctl.py ma-players
  audioctl.py lms players 0 100
  audioctl.py lms --player aa:bb:cc:dd:ee:ff mixer volume 40
  audioctl.py snap Server.GetStatus
  audioctl.py snap-status
  audioctl.py ha GET /api/states/media_player.kitchen
  audioctl.py ha POST /api/services/media_player/volume_set '{"entity_id":"media_player.kitchen","volume_level":0.3}'
  audioctl.py scan --subnet 192.168.1.0/24
  audioctl.py mdns
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PLUGIN = "home-audio"

# port -> what usually listens there
AUDIO_PORTS = {
    3483: "slimproto (LMS / Music Assistant Squeezelite provider)",
    9000: "LMS web + JSON-RPC",
    9090: "LMS CLI",
    8095: "Music Assistant API",
    8097: "Music Assistant stream server",
    1704: "Snapcast stream",
    1705: "Snapcast control (TCP JSON-RPC)",
    1780: "Snapcast HTTP / Snapweb",
    8123: "Home Assistant",
    7000: "AirPlay (RAOP)",
    8009: "Google Cast",
}


def overlay_dir() -> Path:
    home = Path.home()
    if os.environ.get("HOME_AUDIO_HOME"):
        return Path(os.environ["HOME_AUDIO_HOME"])
    if os.environ.get("CLAUDE_USER_DATA"):
        return Path(os.environ["CLAUDE_USER_DATA"]) / PLUGIN
    if (home / ".claude-user-data").is_dir():
        return home / ".claude-user-data" / PLUGIN
    xdg = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")) / "claude-plugins"
    if xdg.is_dir():
        return xdg / PLUGIN
    return home / ".claude-user-data" / PLUGIN


def load_profile() -> dict[str, str]:
    cfg: dict[str, str] = {}
    prof = overlay_dir() / "profile.env"
    if prof.is_file():
        for line in prof.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    for k, v in os.environ.items():
        if k.startswith("HOME_AUDIO_"):
            cfg[k] = v
    return cfg


CFG = load_profile()


def setting(key: str, default: str | None = None) -> str | None:
    return CFG.get(key, default)


def token(var_key: str, default_var: str) -> str | None:
    var = setting(var_key, default_var)
    return os.environ.get(var) if var else None


def die(msg: str, code: int = 1) -> None:
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(code)


def http_json(url: str, payload=None, headers=None, method: str | None = None, timeout=15):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode()
    except urllib.error.HTTPError as e:
        die(f"HTTP {e.code} from {url}: {e.read().decode()[:500]}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        die(f"cannot reach {url}: {e}")
    try:
        return json.loads(body) if body else None
    except json.JSONDecodeError:
        return body


def with_default_port(hostport: str, port: int, scheme="http") -> str:
    if "://" in hostport:
        return hostport.rstrip("/")
    return f"{scheme}://{hostport}" if ":" in hostport else f"{scheme}://{hostport}:{port}"


def parse_json_arg(s: str | None):
    if not s:
        return {}
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        die(f"argument is not valid JSON: {e}")


# ---------- Music Assistant ----------

def ma_call(command: str, args: dict | None = None):
    base = setting("HOME_AUDIO_MA_URL") or die("HOME_AUDIO_MA_URL not set (run the setup skill)")
    base = with_default_port(base, 8095)
    tok = token("HOME_AUDIO_MA_TOKEN_VAR", "MA_TOKEN")
    headers = {"Authorization": f"Bearer {tok}"} if tok else {}
    res = http_json(f"{base}/api", {"message_id": "1", "command": command, "args": args or {}}, headers)
    if isinstance(res, dict) and "error_code" in res:
        die(f"Music Assistant error {res.get('error_code')}: {res.get('details')}")
    return res.get("result", res) if isinstance(res, dict) and "result" in res else res


def cmd_ma(a):
    print(json.dumps(ma_call(a.command, parse_json_arg(a.args)), indent=2))


def cmd_ma_players(a):
    players = ma_call("players/all") or []
    out = []
    for p in players:
        out.append({
            "player_id": p.get("player_id"),
            "name": p.get("display_name") or p.get("name"),
            "provider": p.get("provider"),
            "available": p.get("available"),
            "powered": p.get("powered"),
            "state": p.get("playback_state") or p.get("state"),
            "volume": p.get("volume_level"),
            "group_childs": p.get("group_childs") or p.get("group_members") or [],
            "address": (p.get("device_info") or {}).get("address") or (p.get("device_info") or {}).get("ip_address"),
            "model": (p.get("device_info") or {}).get("model"),
        })
    print(json.dumps(out, indent=2))


# ---------- Lyrion / LMS ----------

def cmd_lms(a):
    host = setting("HOME_AUDIO_LMS") or die("HOME_AUDIO_LMS not set (host[:9000])")
    url = with_default_port(host, 9000) + "/jsonrpc.js"
    res = http_json(url, {"id": 1, "method": "slim.request", "params": [a.player or "", a.cmd]})
    print(json.dumps(res.get("result", res) if isinstance(res, dict) else res, indent=2))


# ---------- Snapcast ----------

def snap_call(method: str, params: dict | None = None):
    host = setting("HOME_AUDIO_SNAPSERVER") or die("HOME_AUDIO_SNAPSERVER not set (host[:1780])")
    url = with_default_port(host, 1780) + "/jsonrpc"
    body = {"id": 1, "jsonrpc": "2.0", "method": method}
    if params:
        body["params"] = params
    res = http_json(url, body)
    if isinstance(res, dict) and "error" in res:
        die(f"Snapcast error: {res['error']}")
    return res.get("result", res) if isinstance(res, dict) else res


def cmd_snap(a):
    print(json.dumps(snap_call(a.method, parse_json_arg(a.params)), indent=2))


def cmd_snap_status(a):
    st = snap_call("Server.GetStatus")["server"]
    out = {
        "server": st.get("server", {}).get("snapserver", {}).get("version"),
        "streams": [{"id": s["id"], "status": s.get("status"), "uri": s.get("uri", {}).get("raw")} for s in st.get("streams", [])],
        "groups": [],
    }
    for g in st.get("groups", []):
        out["groups"].append({
            "id": g["id"], "name": g.get("name"), "stream": g.get("stream_id"), "muted": g.get("muted"),
            "clients": [{
                "id": c["id"], "name": c["config"].get("name") or c["host"].get("name"),
                "host": c["host"].get("name"), "ip": c["host"].get("ip"), "connected": c.get("connected"),
                "volume": c["config"]["volume"].get("percent"), "muted": c["config"]["volume"].get("muted"),
                "latency": c["config"].get("latency"), "version": c.get("snapclient", {}).get("version"),
            } for c in g.get("clients", [])],
        })
    print(json.dumps(out, indent=2))


# ---------- Home Assistant ----------

def cmd_ha(a):
    base = setting("HOME_AUDIO_HA_URL") or die("HOME_AUDIO_HA_URL not set (e.g. http://homeassistant.local:8123)")
    tok = token("HOME_AUDIO_HA_TOKEN_VAR", "HA_TOKEN") or die("Home Assistant token env var is empty")
    path = a.path if a.path.startswith("/") else "/" + a.path
    payload = parse_json_arg(a.body) if a.body else None
    res = http_json(base.rstrip("/") + path, payload, {"Authorization": f"Bearer {tok}"}, method=a.method.upper())
    print(json.dumps(res, indent=2) if not isinstance(res, str) else res)


# ---------- discovery ----------

def probe(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def cmd_scan(a):
    hosts: list[str] = list(a.hosts or [])
    subnet = a.subnet or setting("HOME_AUDIO_SUBNET")
    if subnet:
        net = ipaddress.ip_network(subnet, strict=False)
        if net.num_addresses > 1024:
            die("subnet larger than /22; narrow it")
        hosts += [str(h) for h in net.hosts()]
    if not hosts:
        die("give --subnet CIDR or --hosts, or set HOME_AUDIO_SUBNET")
    ports = [int(p) for p in a.ports.split(",")] if a.ports else list(AUDIO_PORTS)
    jobs = [(h, p) for h in hosts for p in ports]
    with ThreadPoolExecutor(max_workers=128) as ex:
        hits = [j for j, ok in zip(jobs, ex.map(lambda j: probe(j[0], j[1], a.timeout), jobs)) if ok]
    found: dict[str, dict] = {}
    for h, p in hits:
        entry = found.setdefault(h, {"host": h, "ports": {}})
        entry["ports"][str(p)] = AUDIO_PORTS.get(p, "?")
    for e in found.values():
        try:
            e["name"] = socket.gethostbyaddr(e["host"])[0]
        except OSError:
            e["name"] = None
    print(json.dumps(sorted(found.values(), key=lambda e: ipaddress.ip_address(e["host"])), indent=2))


def cmd_mdns(a):
    if not shutil.which("avahi-browse"):
        die("avahi-browse not installed (apt install avahi-utils)")
    out = subprocess.run(["avahi-browse", "-atrpk"], capture_output=True, text=True, timeout=a.timeout + 5).stdout
    keep = ("snapcast", "slim", "mass", "music", "raop", "airplay", "googlecast", "spotify", "sendspin", "home-assistant", "squeeze")
    rows, seen = [], set()
    for line in out.splitlines():
        f = line.split(";")
        if not f or f[0] != "=" or len(f) < 9:
            continue
        if not any(k in (f[4] + f[3]).lower() for k in keep):
            continue
        key = (f[3], f[4], f[7])
        if key in seen:
            continue
        seen.add(key)
        rows.append({"name": f[3], "type": f[4], "host": f[6], "ip": f[7], "port": f[8], "txt": f[9] if len(f) > 9 else ""})
    print(json.dumps(rows, indent=2))


def cmd_config(a):
    shown = {k: v for k, v in sorted(CFG.items())}
    shown["_overlay_dir"] = str(overlay_dir())
    shown["_profile_present"] = (overlay_dir() / "profile.env").is_file()
    shown["_ma_token_present"] = bool(token("HOME_AUDIO_MA_TOKEN_VAR", "MA_TOKEN"))
    shown["_ha_token_present"] = bool(token("HOME_AUDIO_HA_TOKEN_VAR", "HA_TOKEN"))
    print(json.dumps(shown, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="sub", required=True)
    sub.add_parser("config", help="show resolved settings (no secret values)").set_defaults(fn=cmd_config)
    p = sub.add_parser("ma", help="raw Music Assistant command"); p.add_argument("command"); p.add_argument("args", nargs="?"); p.set_defaults(fn=cmd_ma)
    sub.add_parser("ma-players", help="Music Assistant players, summarised").set_defaults(fn=cmd_ma_players)
    p = sub.add_parser("lms", help="LMS/Lyrion CLI command over JSON-RPC"); p.add_argument("--player", "-p"); p.add_argument("cmd", nargs="+"); p.set_defaults(fn=cmd_lms)
    p = sub.add_parser("snap", help="raw Snapcast JSON-RPC"); p.add_argument("method"); p.add_argument("params", nargs="?"); p.set_defaults(fn=cmd_snap)
    sub.add_parser("snap-status", help="Snapcast groups/clients, summarised").set_defaults(fn=cmd_snap_status)
    p = sub.add_parser("ha", help="Home Assistant REST call"); p.add_argument("method"); p.add_argument("path"); p.add_argument("body", nargs="?"); p.set_defaults(fn=cmd_ha)
    p = sub.add_parser("scan", help="TCP-probe hosts for audio ports"); p.add_argument("--subnet"); p.add_argument("--hosts", nargs="*")
    p.add_argument("--ports"); p.add_argument("--timeout", type=float, default=0.4); p.set_defaults(fn=cmd_scan)
    p = sub.add_parser("mdns", help="audio-related mDNS services (avahi)"); p.add_argument("--timeout", type=int, default=5); p.set_defaults(fn=cmd_mdns)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
