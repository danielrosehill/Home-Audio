# Snapcast troubleshooting matrix

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Client not in web UI at all | snapclient service down, wrong `--host`, firewall blocking 1704 | `systemctl status snapclient`; check `/etc/default/snapclient`; `nc -zv <server> 1704` |
| Client in web UI, no audio | Bound sink missing or muted at OS level | `snapclient -l`; `aplay -L` / `pactl list sinks`; `speaker-test` against the sink |
| Client in web UI, in group, but silent | Group bound to a stream with status `idle`, or group muted | Check stream status via JSON-RPC; check group mute |
| Audio plays but desynced from other rooms | Wi-Fi jitter / bad clock | Move to wired; tune `--latency`; check `iw dev wlan0 link` |
| Client connects, drops, reconnects in a loop | Snapcast version skew between server and client | `snapserver -v` vs `snapclient -v`; upgrade the older one |
| Web UI shows client with garbled name | `--hostID` defaulted to MAC and changed (NIC swap, USB Ethernet adapter) | Set explicit `--hostID` in `/etc/default/snapclient` and update `server.json` mapping |
| Group disappeared after server restart | Group only existed via runtime JSON-RPC and `<datadir>/server.json` was wiped | Recreate from `installation.json` (groups[] in the overlay); investigate why server.json was lost |
| New client refuses to join named group | Snapserver hasn't seen this hostID before | Connect it once (`install-client`), then assign it (`groups` skill) |
| Volume control doesn't work from web UI | `--mixer` set to `hardware` or `none` on the client | Change to `software` and restart snapclient |
| All clients silent simultaneously | Stream source dead (fifo not being written, librespot crashed) | Check the source process; `journalctl -u snapserver`; verify the fifo has data |
