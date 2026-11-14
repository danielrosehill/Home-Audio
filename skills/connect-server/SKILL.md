---
name: connect-server
description: Point speaker clients at an audio server and wire the server into Music Assistant/HA. Use on "connect to the server", migrating backends.
---

# Connect clients and servers

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`profile.env`, `installation.json`, `connect-server.md`.

## Steps

1. **Server side ready.** For Music Assistant, enable the matching player provider
   (Settings > Providers > Add): *Squeezelite* (slimproto on 3483, CLI 9090, JSON-RPC 9000),
   *Snapcast* (built-in snapserver by default, or an external one on its control port 1705),
   *AirPlay*, *Google Cast*. Check from a client host: `nc -zv <server> 3483` (or 1704/1705).
2. **Repoint each client.** Change only the server address, keep the name and device:
   - Squeezelite: `SB_SERVER_IP` in `/etc/default/squeezelite` or `-s` in the unit. With no
     `-s`, Squeezelite autodiscovers by UDP broadcast and may pick the wrong server.
   - snapclient: `--host` in `SNAPCLIENT_OPTS` or the unit's `ExecStart`.
   Then `systemctl daemon-reload && systemctl restart <unit>` (add `--user` for user units).
3. **Confirm on the server**: the player is listed, `connected`, and plays.
4. **Migration between backends** (e.g. Snapcast to Squeezelite): do one endpoint, verify,
   then the rest. Disable the old client's unit, do not just stop it. Keep the old server
   until every endpoint has moved, then record it `retired` with the date.
5. **Home Assistant**: hand over to the `home-assistant` skill for integrations.
6. Update `installation.json` (each endpoint's `server`, `client`), `changelog.md`.

## Notes

A restart drops playback on that speaker. Two slimproto servers on one LAN make
autodiscovering players flap between them: pin `-s`.

## Data storage

Updates `installation.json` and `changelog.md` in the overlay.
