---
name: groups
description: Group, sync or ungroup speakers for multi-room playback in Music Assistant, Snapcast, LMS or HA. Use on "play in two rooms".
---

# Groups and multi-room

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`installation.json` (named groups under `groups[]`) and `groups.md`.

## Which layer owns the group

Use the layer the user plays from. Mixing them (an MA sync group over Snapcast clients that
are also in a Snapcast group) makes groups fight.

- **Music Assistant.** Ad-hoc sync of same-protocol players:
  `audioctl.py ma players/cmd/group_many '{"target_player":"<leader_id>","child_player_ids":["<id>",...]}'`,
  undo with `players/cmd/ungroup`. Persistent mixed groups: a "Group player" from the
  Player Group provider (Settings > Providers). Command names vary by version; confirm in
  `http://<ma>:8095/api-docs` and with `${CLAUDE_PLUGIN_ROOT}/reference/music-assistant-api.md`.
- **Snapcast.** A client is in exactly one group. `Group.SetClients` moves clients into a
  group, `Group.SetStream` sets what it plays. See `${CLAUDE_PLUGIN_ROOT}/reference/snapcast/groups-and-streams.md`.
- **LMS.** `audioctl.py lms -p <slave_mac> sync <master_mac>`; `sync -` to unsync.
- **Home Assistant.** `media_player.join` with `group_members`, `media_player.unjoin`;
  works where the integration supports grouping (MA, Squeezebox, Sonos, Cast groups).

## Steps

1. Resolve the speakers by room/name from `installation.json`, then to IDs from the live server.
2. Apply at the chosen layer; read it back from the server.
3. If the user names the group ("downstairs"), save it in `installation.json` `groups[]`
   with members and the layer, so it can be recreated after a server rebuild.

## Data storage

Updates `groups[]` in `installation.json` in the overlay.
