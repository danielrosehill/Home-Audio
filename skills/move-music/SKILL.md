---
name: move-music
description: Move what is playing from one room to another, or extend it to more rooms. Use on "move the music to the kitchen", "play this in the bedroom too", "follow me".
---

# Move music

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`profile.env` and `installation.json` (rooms -> player names). Run calls through the user's
secrets route if `profile.env` names one. `A="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audioctl.py"`.
Resolve rooms to players by name; `$A ma-players` lists them. Never guess IDs.

## Steps

1. **Move** (source stops, target continues at the same point):
   `$A transfer --to "<room>" [--from "<room>"]`. Without `--from` it picks the one playing
   queue and refuses if several are playing (ask which). `--no-play` moves without starting.
2. **Extend** (both rooms play in sync): use the `groups` skill:
   `$A ma players/cmd/set_members '{"target_player":"<playing>","player_ids_to_add":["<other>"]}'`.
   Cross-provider sync (e.g. Squeezelite with Snapcast) only works through a sync group.
3. Read back with `$A now-playing`.

## Commands underneath

`player_queues/transfer {"source_queue_id","target_queue_id","auto_play"}` (source:
2.10.11), `player_queues/get_active_queue {"player_id"}`. Home Assistant equivalent:
`music_assistant.transfer_queue` (`entity_id` = target, `source_player`, `auto_play`).

## Data storage

Nothing written.
