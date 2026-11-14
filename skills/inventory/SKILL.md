---
name: inventory
description: Discover and document every audio server, speaker endpoint and HA media player on the LAN. Use for "what's on the network".
---

# Inventory: document what is on the network

## Load

`bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir` -> `DIR`. Read `DIR/profile.env`,
`DIR/installation.json` and `DIR/inventory.md` (private notes win). No overlay: run
discovery anyway and offer `setup` before writing.

`ACTL="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audioctl.py"`. Wrap it in the user's secrets
route (a profile.env comment) when a step needs MA or HA tokens.

## Steps

1. **Ports.** `$ACTL scan --subnet <HOME_AUDIO_SUBNET>`. Interpret with `${CLAUDE_PLUGIN_ROOT}/reference/ports.md`.
   An open port is a hint, not an identity: 9000 can be MinIO, 8095 another web app.
2. **Identify each server**, by asking it:
   - Music Assistant: `curl -s http://<h>:8095/info` (JSON with `server_version`,
     `homeassistant_addon`). HTML means it is not MA.
   - LMS or MA's Squeezelite provider: `HOME_AUDIO_LMS=<h> $ACTL lms serverstatus 0 100`.
     `uuid: aioslimproto` means Music Assistant is the slimproto server, not Lyrion.
   - Snapcast: `HOME_AUDIO_SNAPSERVER=<h> $ACTL snap-status`.
   - Home Assistant: `$ACTL ha GET /api/` then the media players:
     `$ACTL ha GET /api/states` filtered to `media_player.*`.
3. **Players.** Merge three views: the server's player list (`ma-players`, `lms players`,
   `snap-status`), mDNS (`$ACTL mdns`), and HA entities. Key endpoints by MAC or hostID.
4. **Endpoints.** For each endpoint reachable over SSH, read the client config without
   changing anything (commands in `${CLAUDE_PLUGIN_ROOT}/reference/clients.md`): service unit and state, client
   version, configured server, output device, player name, and the sink list.
5. **Reconcile** with the existing `installation.json`: mark entries `confirmed` with
   today's date, flag anything recorded but not seen as `missing_since`, and add new ones.
   Never delete an entry silently; report it.
6. Write `installation.json` (schema: `${CLAUDE_PLUGIN_ROOT}/templates/installation.json`) and regenerate
   `installation.md` (a table per server, a table of endpoints: room, host, IP, client,
   server, sink, state). Append a dated line to `changelog.md`.
7. Report: what changed since the last inventory, and contradictions (a client pointed at
   a server that is not there, two servers fighting over port 3483, duplicate names).

## Data storage

Writes `installation.json`, `installation.md`, `changelog.md` and `endpoints/<host>.md` in the
overlay. Read-only on the network and the endpoints.
