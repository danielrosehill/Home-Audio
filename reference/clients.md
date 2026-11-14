# Clients: read-only inspection commands

Run over SSH on the endpoint. None of these change anything.

```bash
# what is installed and running
systemctl list-units --all --type=service | grep -Ei 'squeezelite|snapclient|shairport|librespot|raspotify'
systemctl --user list-units --all --type=service | grep -Ei 'squeezelite|snapclient'   # user units
systemctl cat squeezelite snapclient 2>/dev/null
cat /etc/default/squeezelite /etc/default/snapclient 2>/dev/null
squeezelite -? 2>&1 | head -1; snapclient -v
# outputs
aplay -l; squeezelite -l; snapclient -l
pactl info 2>/dev/null | grep -E 'Server Name|Default Sink'; pactl list short sinks
# identity
ip -br addr; cat /sys/class/net/*/address
```

## Squeezelite flags that matter

| Flag | Meaning |
| --- | --- |
| `-n <name>` | Player name shown on the server |
| `-o <device>` | Output: `plughw:CARD=X,DEV=0`, `default`, `pulse`, `pipewire` |
| `-s <server>[:port]` | Server; without it, UDP discovery picks one |
| `-m <mac>` | Player identity; set it so identity survives NIC changes |
| `-a <b>:<p>:<f>:<m>` | ALSA buffer/period; raise buffer for dropouts (e.g. `-a 160:4::`) |
| `-r <rates>` | Supported rates; `-r 48000` for 48 kHz-only USB devices |
| `-V <control>` | Hand volume to an ALSA hardware mixer control |
| `-C <s>` | Close the device after s seconds idle (lets others use it) |
| `-d all=info -f <file>` | Logging |

Debian's `/etc/default/squeezelite` keys: `SL_NAME`, `SL_SOUNDCARD`, `SB_SERVER_IP`,
`SB_EXTRA_ARGS`.

snapclient flags: see `snapcast/snapclient-flags.md`.
