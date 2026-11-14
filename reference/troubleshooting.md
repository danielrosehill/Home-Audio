# Troubleshooting: symptom -> cause -> check

Snapcast-specific rows: `snapcast/troubleshooting-matrix.md`.

| Symptom | Likely cause | Check / fix |
| --- | --- | --- |
| Squeezelite player missing from MA/LMS | Wrong or no `-s`; firewall on 3483; service crashed | `journalctl -u squeezelite`; `nc -zv <server> 3483`; pin `-s` |
| Player flips between two servers | Two slimproto servers on the LAN, client autodiscovering | Pin `-s`; disable one server's slimproto |
| Player listed, connected, silent | Output device wrong/missing (USB re-enumerated), mixer muted, amp off | `aplay -l` vs configured `CARD=`; `amixer -c <card>`; `speaker-test` with client stopped |
| "Device or resource busy" | Another process holds the ALSA `hw:` device (second client, PipeWire) | `fuser -v /dev/snd/*`; one client per device, or go through PipeWire |
| Plays at wrong speed / chipmunk / no sound on USB | Device supports only 48 kHz | Use `plughw:`; Squeezelite `-r 48000` |
| Dropouts / stutter | Wi-Fi power save, weak signal, small buffer | `iw dev wlan0 set power_save off`; raise `-a` buffer; wire it |
| Out of sync across rooms | Mixed protocols in one group; per-device latency | Group same-protocol players only; adjust latency (snapclient `--latency`, MA player setting) |
| MA API 401 | Missing/expired token | New long-lived token; check the env var the profile names |
| MA player "unavailable" in HA | Player offline in MA, or HA integration lost connection | `audioctl.py ma-players`; reload the integration |
| Desktop Squeezelite silent after login change | User unit without linger, or PipeWire default sink moved | `loginctl enable-linger`; pin the sink (`PULSE_SINK`) |
| TTS clipped at start/end | Speaker wake-up / buffer | MA `play_announcement` with pre-announce; pad TTS; keep device open (`-C` off) |
| Everything silent at once | Server down or source dead | Server logs; `curl <ma>/info`; snapserver stream status |
