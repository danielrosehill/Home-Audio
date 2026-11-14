---
name: now-playing
description: Report what each room is playing, paused, sleep timers, and what was played recently. Read-only. Use on "what's playing", "what's on in the kitchen", "what did we listen to".
---

# Now playing

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`profile.env` and `installation.json` (rooms -> player names). Run calls through the user's
secrets route if `profile.env` names one. `A="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audioctl.py"`.
Resolve rooms to players by name; `$A ma-players` lists them. Never guess IDs.

## Steps

1. `$A now-playing` lists playing and paused queues: room, title, artist, elapsed, duration,
   volume, group members, sleep timer (`ends_at`, `minutes_left`). `--all` adds idle queues;
   `--history N` adds `music/recently_played_items` and `music/in_progress_items`
   (podcasts and audiobooks with a resume point).
2. Answer in one line per room. Nothing playing is a valid answer; say so.

## Commands underneath (MA 2.10.11, confirmed live)

`player_queues/all`, `players/all`, `players/sleep_timer/get {"player_id"}` (epoch end time
or null; HTTP 500 on some idle players, so only asked for playing/paused ones),
`music/recently_played_items {"limit","media_types?","fully_played_only?"}`,
`music/in_progress_items {"limit"}`. `elapsed_time` is a snapshot at
`elapsed_time_last_updated`; the helper extrapolates while playing.

## Data storage

Nothing written.
