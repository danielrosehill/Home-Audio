# snapclient CLI flags

Set in `/etc/default/snapclient` as `SNAPCLIENT_OPTS="..."`.

| Flag | Purpose |
|------|---------|
| `--host <ip>` | Snapserver address. Required if not on the same multicast subnet. |
| `--port <n>` | Snapserver stream port (default 1704). |
| `--soundcard <id>` | Audio sink. Get the list with `snapclient -l`. |
| `--player <alsa\|pulse>` | Audio backend. Default `alsa`. Use `pulse` for PipeWire/PulseAudio sinks. |
| `--hostID <name>` | **Stable client identity.** Defaults to MAC. Set explicitly to a hostname-like string so the client survives NIC changes and stays bound to its group. |
| `--instance <n>` | Run multiple snapclient instances on one host (different sinks). |
| `--latency <ms>` | Adjust local playback latency. Useful for fixing per-room sync. |
| `--logsink <stdout\|system>` | Where to send logs. Systemd captures stdout fine. |
| `--mixer <hardware\|software\|none>` | Volume control mode. `software` lets the snapserver web UI control it. |

## Multiple instances on one host

Service template approach:

```
# /etc/systemd/system/snapclient-b.service
[Service]
EnvironmentFile=/etc/default/snapclient-b
ExecStart=/usr/bin/snapclient $SNAPCLIENT_OPTS --instance 2
```

`/etc/default/snapclient-b` has its own `--soundcard` and `--hostID`. The two instances appear as two separate clients on the snapserver and can be assigned to different groups.
