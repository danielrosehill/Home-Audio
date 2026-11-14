# Server install recipes

## Music Assistant

**Home Assistant add-on** (HA OS / Supervised): Settings > Add-ons > Add-on store >
"Music Assistant Server" > Install > Start. Then add the `music_assistant` integration
(usually auto-discovered).

**Docker** (`network_mode: host` is required for discovery and stream ports):

```yaml
services:
  music-assistant:
    image: ghcr.io/music-assistant/server:latest
    container_name: music-assistant
    network_mode: host
    restart: unless-stopped
    volumes:
      - ./data:/data
    cap_add: [SYS_ADMIN, DAC_READ_SEARCH]   # only if mounting SMB/NFS from inside
    security_opt: [apparmor:unconfined]
```

Then the UI on `http://<host>:8095`: create the admin user, add player providers
(Squeezelite, Snapcast, AirPlay, Google Cast) and music providers.

Provider notes (music-assistant.io, checked 2026-11-14): the Squeezelite provider emulates
LMS (slimproto 3483 tcp+udp, CLI 9090, JSON-RPC 9000; set either to 0 to disable). Don't
run Lyrion on the same host. Snapcast provider: built-in snapserver by default (ports
1704, 1705, 4953-5153, buffer 1000 ms); external snapserver must be >= 0.27, and the docs
list 0.30.0 as unsupported. Check the provider page again before relying on version limits.

## Lyrion Music Server

```yaml
services:
  lms:
    image: lmscommunity/lyrionmusicserver:stable
    network_mode: host          # or macvlan with its own IP if 9000 is taken on the host
    restart: unless-stopped
    volumes:
      - ./config:/config
      - /path/to/music:/music:ro
      - ./playlist:/playlist
    environment: [TZ=Etc/UTC, HTTP_PORT=9000]
```

Ports: 9000 web/JSON-RPC, 9090 CLI, 3483 tcp+udp slimproto. Material skin is the usual UI
(`/material/`).

## snapserver

```bash
sudo apt install snapserver          # or the .deb from github.com/badaix/snapcast/releases
sudo systemctl enable --now snapserver
```

Config `/etc/snapserver.conf`; streams in `[stream] source = pipe:///tmp/snapfifo?name=default`
(see `snapcast/snapserver-conf.md`). Docker: host network, mount the fifo/source.
