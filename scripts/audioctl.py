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
  audioctl.py test-play -p "Living Room" -s 30 --volume 40
  audioctl.py test-play -p "All Home" -s 60     # a group is a player too
  audioctl.py ma-add-podcast --opml https://example.com/feeds.opml
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
    # The HTTP /api returns the result bare. Unwrap only a WebSocket-style envelope:
    # a bare result can itself carry a "result" key (setup-flow steps do).
    if isinstance(res, dict) and "message_id" in res and "result" in res:
        return res["result"]
    return res


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


# ---------- Test playback (through Music Assistant) ----------

TEST_SECONDS = (10, 30, 60, 90)


def resolve_players(wanted: list[str]) -> list[dict]:
    players = ma_call("players/all") or []
    out = []
    for w in wanted:
        wl = w.lower()
        hit = [p for p in players if p.get("player_id") == w] or \
              [p for p in players if wl in ((p.get("display_name") or "").lower(), (p.get("name") or "").lower())]
        if len(hit) != 1:
            names = [f'{p.get("display_name") or p.get("name")} ({p.get("player_id")})' for p in players]
            die(f"player {w!r} matched {len(hit)}; players: {names}")
        out.append(hit[0])
    return out


def player_brief(pid: str) -> dict:
    import time
    p = ma_call("players/get", {"player_id": pid}) or {}
    cm = p.get("current_media") or {}
    state = p.get("playback_state") or p.get("state")
    # elapsed_time is a snapshot taken at elapsed_time_last_updated; extrapolate while playing
    el, upd = p.get("elapsed_time"), p.get("elapsed_time_last_updated")
    if el is not None and upd and state == "playing":
        el = el + max(0.0, time.time() - upd)
    return {"player_id": pid, "name": p.get("display_name") or p.get("name"),
            "available": p.get("available"), "powered": p.get("powered"),
            "state": state,
            "volume": p.get("volume_level"), "elapsed": None if el is None else round(el, 1),
            "media": cm.get("title") or cm.get("uri"),
            "group_childs": p.get("group_childs") or p.get("group_members") or []}


def cmd_test_play(a):
    import time
    media = a.media or setting("HOME_AUDIO_TEST_MEDIA") or \
        die("no test media: pass --media <uri> or set HOME_AUDIO_TEST_MEDIA in profile.env")
    targets = resolve_players(a.player)
    before, during, problems = {}, {}, []
    for p in targets:
        if not p.get("available"):
            problems.append(f'{p.get("display_name") or p.get("name")}: not available in MA (client not connected)')
    t0 = time.time()
    try:
        for p in targets:
            pid = p["player_id"]
            before[pid] = player_brief(pid)
            if a.volume is not None:
                ma_call("players/cmd/volume_set", {"player_id": pid, "volume_level": a.volume})
            ma_call("player_queues/play_media", {"queue_id": pid, "media": media, "option": "replace"})
        time.sleep(min(5, a.seconds / 2))
        for p in targets:
            during[p["player_id"]] = [player_brief(p["player_id"])]
        print(json.dumps({"status": "started", "media": media, "seconds": a.seconds,
                          "players": list(during.values())}, indent=2), flush=True)
        time.sleep(max(0, a.seconds - (time.time() - t0)))
        for p in targets:
            pid = p["player_id"]
            first, last = during[pid][0], player_brief(pid)
            during[pid].append(last)
            if last["state"] != "playing":
                problems.append(f'{last["name"]}: state {last["state"]!r} at the end')
            elif (first["elapsed"] is not None and last["elapsed"] is not None
                  and last["elapsed"] - first["elapsed"] < (a.seconds - 5) * 0.5):
                problems.append(f'{last["name"]}: elapsed only moved {first["elapsed"]} -> {last["elapsed"]}')
    finally:
        for pid, b in before.items():
            ma_call("players/cmd/stop", {"player_id": pid})
            if a.volume is not None and b.get("volume") is not None:
                ma_call("players/cmd/volume_set", {"player_id": pid, "volume_level": b["volume"]})
        time.sleep(1.5)  # MA applies stop/volume asynchronously
    # Power is left alone: powering a Squeezelite player off via MA re-paused it (MA 2.x, 2026-11-14).
    print(json.dumps({"status": "done", "server_side_ok": not problems, "problems": problems,
                      "samples": during,
                      "restored": [player_brief(pid) for pid in before]}, indent=2))
    print("server_side_ok only says MA thinks it played. Ask the listener what they heard.", file=sys.stderr)


def cmd_ma_add_podcast(a):
    """One podcastfeed provider instance per feed, created through MA's setup flow
    (config/providers/save refuses new providers). Does not dedupe: MA does not expose an
    instance's feed URL, so compare existing_podcasts (by title) before re-running."""
    have = set()
    for c in ma_call("config/providers") or []:
        if c.get("domain") == "podcastfeed":
            have.add(c.get("instance_id"))
    names = {(m.get("provider_instance"), i.get("name")) for i in
             (ma_call("music/podcasts/library_items", {"limit": 1000}) or [])
             for m in i.get("provider_mappings", [])}
    urls = list(a.url)
    if a.opml:
        import re
        body = urllib.request.urlopen(a.opml, timeout=20).read().decode()
        urls += re.findall(r'xmlUrl="([^"]+)"', body)
    out = []
    for url in urls:
        step = ma_call("config/providers/setup", {"provider_domain": "podcastfeed"})
        if step.get("type") != "form":
            out.append({"url": url, "error": step.get("reason") or step.get("type")}); continue
        res = ma_call("config/flows/submit", {"flow_id": step["flow_id"], "values": {"feed_url": url}})
        out.append({"url": url, "type": res.get("type"), "errors": res.get("errors") or None,
                    "instance_id": (res.get("result") or {}).get("instance_id")})
    print(json.dumps({"existing_podcastfeed_instances": len(have),
                      "existing_podcasts": sorted(n for _, n in names if n), "added": out}, indent=2))


# ---------- Household helpers (now-playing, transfer, announce, sleep, podcasts, providers) ----------

def _quiet_ma(command, args=None):
    import contextlib
    import io
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            return ma_call(command, args)
    except SystemExit:
        return None


def _sleep_info(end):
    """players/sleep_timer/get returns the end time as epoch seconds, or null."""
    import datetime
    import time
    if not end:
        return {"sleep_timer": None}
    return {"sleep_timer": {"ends_at": datetime.datetime.fromtimestamp(end).isoformat(timespec="seconds"),
                            "minutes_left": round((end - time.time()) / 60, 1)}}


def _items(res):
    return res.get("items", res) if isinstance(res, dict) else (res or [])


def cmd_now_playing(a):
    import time
    players = {p["player_id"]: p for p in ma_call("players/all") or []}
    rows = []
    for q in ma_call("player_queues/all") or []:
        p = players.get(q.get("queue_id"), {})
        state = q.get("state")
        if state not in ("playing", "paused") and not a.all:
            continue
        ci = q.get("current_item") or {}
        mi = ci.get("media_item") or {}
        el, upd = q.get("elapsed_time"), q.get("elapsed_time_last_updated")
        if el is not None and upd and state == "playing":
            el += max(0.0, time.time() - upd)
        sleep = None
        if state in ("playing", "paused"):  # 500s on some idle/unavailable players (2.10.11)
            sleep = _quiet_ma("players/sleep_timer/get", {"player_id": q.get("queue_id")})
        rows.append({"room": q.get("display_name") or p.get("display_name") or p.get("name"),
                     "queue_id": q.get("queue_id"), "state": state,
                     "title": ci.get("name") or mi.get("name"),
                     "artist": ", ".join(x.get("name", "") for x in mi.get("artists") or []) or None,
                     "elapsed": None if el is None else round(el),
                     "duration": ci.get("duration"), "volume": p.get("volume_level"),
                     "group_childs": p.get("group_childs") or [], **_sleep_info(sleep)})
    out = {"active": rows}
    if a.history:
        out["recently_played"] = [{"name": i.get("name"), "uri": i.get("uri"), "type": i.get("media_type")}
                                  for i in _items(ma_call("music/recently_played_items", {"limit": a.history}))]
        out["in_progress"] = [{"name": i.get("name"), "uri": i.get("uri"), "type": i.get("media_type")}
                              for i in _items(ma_call("music/in_progress_items", {"limit": a.history}))]
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_transfer(a):
    target = resolve_players([a.to])[0]["player_id"]
    if a.source:
        source = resolve_players([a.source])[0]["player_id"]
    else:
        playing = [q for q in ma_call("player_queues/all") or [] if q.get("state") == "playing"]
        if len(playing) != 1:
            die(f"{len(playing)} queues playing; pass --from: {[q.get('display_name') for q in playing]}")
        source = playing[0]["queue_id"]
    ma_call("player_queues/transfer", {"source_queue_id": source, "target_queue_id": target,
                                       "auto_play": not a.no_play})
    print(json.dumps({"from": source, "to": target, "target_now": player_brief(target)}, indent=2))


def cmd_announce(a):
    out = []
    for p in resolve_players(a.player):
        args = {"player_id": p["player_id"]}
        if a.url:
            args["url"] = a.url
        else:
            args["message"] = a.message or die("give a message or --url")
        for k, v in (("tts_engine", a.engine), ("language", a.language), ("volume_level", a.volume)):
            if v is not None:
                args[k] = v
        if a.no_chime:
            args["pre_announce"] = False
        ma_call("players/cmd/play_announcement", args)
        out.append({"player": p.get("display_name") or p.get("name"), "sent": args})
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_sleep(a):
    out = []
    for p in resolve_players(a.player):
        pid = p["player_id"]
        if a.minutes == 0:
            ma_call("players/sleep_timer/clear", {"player_id": pid})
        else:
            ma_call("players/sleep_timer/set", {"player_id": pid, "seconds": int(a.minutes * 60)})
        out.append({"player": p.get("display_name") or p.get("name"),
                    **_sleep_info(ma_call("players/sleep_timer/get", {"player_id": pid}))})
    print(json.dumps(out, indent=2))


def _find_podcast(name: str) -> dict:
    pods = _items(ma_call("music/podcasts/library_items", {"limit": 1000}))
    nl = name.lower()
    hit = [x for x in pods if x.get("name", "").lower() == nl] or [x for x in pods if nl in x.get("name", "").lower()]
    if len(hit) != 1:
        die(f"podcast {name!r} matched {len(hit)}: {[x.get('name') for x in hit][:20]}")
    return hit[0]


def cmd_episodes(a):
    pod = _find_podcast(a.podcast)
    eps = _items(ma_call("music/podcasts/podcast_episodes",
                         {"item_id": pod["item_id"], "provider_instance_id_or_domain": "library"}))
    eps = sorted(eps, key=lambda e: e.get("position") or 0, reverse=True)
    rows = [{"name": e.get("name"), "uri": e.get("uri"), "duration": e.get("duration"),
             "resume_s": (e.get("resume_position_ms") or 0) // 1000 or None,
             "played": e.get("fully_played")} for e in eps[: a.limit]]
    if a.play:
        target = resolve_players([a.play])[0]["player_id"]
        ma_call("player_queues/play_media", {"queue_id": target, "media": rows[0]["uri"], "option": "play"})
        print(json.dumps({"podcast": pod.get("name"), "playing": rows[0], "on": target}, indent=2, ensure_ascii=False))
        return
    print(json.dumps({"podcast": pod.get("name"), "uri": pod.get("uri"), "episodes": rows}, indent=2, ensure_ascii=False))


def cmd_providers(a):
    live = {p.get("instance_id"): p for p in ma_call("providers") or []}
    rows = []
    for c in ma_call("config/providers") or []:
        iid = c.get("instance_id")
        if a.domain and c.get("domain") != a.domain:
            continue
        rows.append({"domain": c.get("domain"), "instance_id": iid, "name": c.get("name"),
                     "enabled": c.get("enabled"), "loaded": iid in live and live[iid].get("available", True),
                     "last_error": c.get("last_error")})
    if a.problems:
        rows = [r for r in rows if r["enabled"] and (r["last_error"] or not r["loaded"])]
    print(json.dumps(rows, indent=2, ensure_ascii=False))


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
    p = sub.add_parser("test-play", help="play test media to Music Assistant players or groups for 10-90 s, check MA's state, stop and restore")
    p.add_argument("--player", "-p", action="append", required=True, help="player or group: id or name; repeat for several")
    p.add_argument("--seconds", "-s", type=int, choices=TEST_SECONDS, default=30)
    p.add_argument("--media", "-m", help="MA uri (default HOME_AUDIO_TEST_MEDIA from profile.env)")
    p.add_argument("--volume", type=int, help="player volume 0-100 for the test, restored after")
    p.set_defaults(fn=cmd_test_play)
    p = sub.add_parser("ma-add-podcast", help="add podcast RSS feeds to Music Assistant (one provider instance each)")
    p.add_argument("url", nargs="*", help="feed URLs"); p.add_argument("--opml", help="OPML URL: add every xmlUrl in it")
    p.set_defaults(fn=cmd_ma_add_podcast)
    p = sub.add_parser("now-playing", help="what each room is playing (MA)")
    p.add_argument("--all", action="store_true", help="include idle queues"); p.add_argument("--history", type=int, metavar="N", help="also N recently played / in-progress items")
    p.set_defaults(fn=cmd_now_playing)
    p = sub.add_parser("transfer", help="move the playing queue to another room (MA)")
    p.add_argument("--to", required=True); p.add_argument("--from", dest="source"); p.add_argument("--no-play", action="store_true")
    p.set_defaults(fn=cmd_transfer)
    p = sub.add_parser("announce", help="speak a message (MA TTS) or play a URL as an announcement")
    p.add_argument("message", nargs="?"); p.add_argument("--player", "-p", action="append", required=True)
    p.add_argument("--url"); p.add_argument("--engine", help="TTS engine uid (players/tts_engines)"); p.add_argument("--language")
    p.add_argument("--volume", type=int); p.add_argument("--no-chime", action="store_true")
    p.set_defaults(fn=cmd_announce)
    p = sub.add_parser("sleep", help="sleep timer: stop after N minutes (0 clears)")
    p.add_argument("minutes", type=float); p.add_argument("--player", "-p", action="append", required=True)
    p.set_defaults(fn=cmd_sleep)
    p = sub.add_parser("episodes", help="latest episodes of a library podcast; --play <room> plays the newest")
    p.add_argument("podcast"); p.add_argument("--limit", type=int, default=5); p.add_argument("--play", metavar="ROOM")
    p.set_defaults(fn=cmd_episodes)
    p = sub.add_parser("providers", help="MA provider health: enabled, loaded, last_error")
    p.add_argument("--domain"); p.add_argument("--problems", action="store_true", help="only enabled providers with an error or not loaded")
    p.set_defaults(fn=cmd_providers)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
