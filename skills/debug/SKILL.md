---
name: debug
description: Debug home audio: silent speaker, player missing/offline, dropouts, out of sync, wrong server. Plays a 10/30/60/90 s test of known music to one speaker, several or a group. Squeezelite, Snapcast, MA, LMS.
---

# Debug

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`installation.json` (what *should* exist), `debug.md`, `endpoints/<host>.md` (known quirks).

## Method: walk the chain, one link at a time

source -> server -> network -> client process -> output device -> amplifier/speaker.
Find the first link that fails. Check the thing itself at each link, not a status that
stands in for it (an "active" unit can be playing to a missing device).

1. **Server sees the player?** `audioctl.py ma-players`, `audioctl.py lms players 0 100`,
   `audioctl.py snap-status`. Note `connected`, `available`, `powered`, the IP it reports.
2. **Network.** From the endpoint: `nc -zv <server> 3483` (Squeezelite) or `1704`/`1705`
   (Snapcast). Wi-Fi: `iw dev wlan0 link`, power save `iw dev wlan0 get power_save`
   (turn it off for audio endpoints).
3. **Client process.** `systemctl status <unit>`, `journalctl -u <unit> -n 100`
   (`--user` for user units). Look for: wrong server IP, "device busy", "No such device",
   reconnect loops, version mismatch.
4. **Device.** Stop the client, `speaker-test -D <device> -c 2 -t sine -l 1`. Check mixer
   levels and mute (`amixer -c <card>`, `alsamixer`). USB speakers re-enumerate after
   reboot or replug: is the `CARD=` name still the same (`aplay -l`)?
5. **Test playback end to end** (Music Assistant). Play known media for 10, 30, 60 or 90 s
   to one player, several (`-p` repeated) or a group (a group is a player in MA):

   ```bash
   audioctl.py test-play -p "<player or group>" -s 30 --volume 40
   ```

   Media: `--media <uri>`, else `HOME_AUDIO_TEST_MEDIA` in `profile.env`. Pick a long track
   with steady level from the user's own library (classical works well), so the test does
   not depend on a streaming service or on this machine being reachable from MA. Find
   one with `audioctl.py ma music/search '{"search_query":"concerto","media_types":["track"]}'`.
   It sets the volume, plays, samples MA's state at ~5 s and at the end, then stops and
   restores the volume. `server_side_ok` only says MA thinks it played. At the same time,
   check the endpoint: `cat /proc/asound/<card>/pcm0p/sub0/status` should be `RUNNING` and
   `hw_params` shows what the client opened. Then **ask the listener** what they heard.
   MA playing + ALSA `RUNNING` + silence means the fault is past the DAC (mixer, amp, cable).
   Use a direct device tone (step 4) to split client from device.
6. **Server logs.** Music Assistant: `audioctl.py ma logging/get` if the version has it,
   else `GET <ma>/log` or the HA add-on log (`audioctl.py ha GET /api/hassio/addons/<slug>/logs`,
   needs an admin token). LMS: `server.log` in its config volume. snapserver:
   `journalctl -u snapserver`.
7. Use `${CLAUDE_PLUGIN_ROOT}/reference/troubleshooting.md` (symptom table, all backends) and
   `${CLAUDE_PLUGIN_ROOT}/reference/snapcast/troubleshooting-matrix.md`.

## After the fix

Write it down: `endpoints/<host>.md` gets what was broken, what fixed it, and what was
ruled out; one dated line in `changelog.md`. If the fix generalises, say so.

## Notes

Read-only until a cause is found. Restarting units is a change: say so before doing it.
A test play makes sound in someone's room: say which speaker and how long before running it.

Learned 2026-11-14 (MA 2.10.11):
- `elapsed_time` from `players/get` is a snapshot taken at `elapsed_time_last_updated`;
  it does not move between reads. Extrapolate while `playing` (`test-play` does).
- Do not power a Squeezelite player off through MA to "restore" it: it came back paused
  with `powered` still true. Stop it instead.
- A plain `http://` URL works as `play_media` media, but MA must reach it: a URL served from
  a laptop behind a host firewall fails as `MediaNotFoundError: No playable items found`
  (log: "Unable to retrieve info ... Connection timed out"). Library media avoids that.

## Data storage

Writes `endpoints/<host>.md` and `changelog.md` in the overlay.
