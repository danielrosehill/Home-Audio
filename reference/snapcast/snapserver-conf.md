# /etc/snapserver.conf reference

Structure (Snapcast >= 0.27):

```
[server]
threads = -1
datadir = /var/lib/snapserver

[http]
enabled = true
bind_to_address = 0.0.0.0
port = 1780
doc_root = /usr/share/snapserver/snapweb

[tcp]
enabled = true
bind_to_address = 0.0.0.0
port = 1705

[stream]
source = pipe:///tmp/snapfifo?name=default&sampleformat=48000:16:2
buffer = 1000
codec = flac
sampleformat = 48000:16:2
chunk_ms = 20
```

## Streams

Each `source = ...` line defines one stream. Multiple sources can be added; clients/groups bind to one at a time.

Common source schemes:
- `pipe:///tmp/snapfifo?name=default` — fed by another process writing PCM.
- `tcp://host:port?name=...`
- `process:///usr/bin/librespot?name=spotify&...` — server spawns the process.
- `meta:///stream-a/stream-b?name=combined` — meta-stream switching.

## Group definitions

Snapcast does not have first-class `[group]` config sections in upstream releases — groups are typically created at runtime via JSON-RPC and persisted by the server in `<datadir>/server.json`.

To make a group truly persistent across reinstalls and back it up in version control:

1. Create the group via JSON-RPC (`/create-group` does this for you).
2. The server writes it to `<datadir>/server.json` automatically.
3. Mirror the group definition into `installation.json` (groups[] in the overlay) `groups:` block — that's the version-controlled source of truth.
4. On a fresh server, run `/create-group` for each group in topology to recreate them.

If your build supports config-file `[group.<name>]` sections, prefer those — show the version-correct snippet to the user before writing.

## Reload vs restart

- `systemctl reload snapserver` — re-reads streams; preserves connected clients. Use for stream additions/changes.
- `systemctl restart snapserver` — full restart; drops all clients briefly. Use when reload is insufficient (rare).
