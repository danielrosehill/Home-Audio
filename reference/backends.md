# Backends compared

| | Music Assistant | Lyrion (LMS) | Snapcast |
| --- | --- | --- | --- |
| Role | Music server + player hub | Music server | Synchronised audio transport |
| Library / streaming | Local, Spotify, Tidal, Qobuz, radio, Plex, Jellyfin, etc. | Local + plugins (Spotty, etc.) | None: plays whatever is fed to its streams |
| Endpoint client | Squeezelite, snapclient, AirPlay, Cast, DLNA, Sendspin, HA players | Squeezelite, Squeezebox hardware, UPnP bridge | snapclient |
| Multi-room sync | Per protocol; same-protocol groups sync well | Excellent (slimproto sync) | Excellent, any source |
| Control | Web UI, HA integration, API on 8095 | Web UI (Material skin), apps (Squeezer, iPeng), JSON-RPC 9000 | Snapweb, Snapdroid, JSON-RPC 1705/1780, HA integration |
| Footprint | ~1 GB RAM, Python | ~300 MB, Perl | Tiny |
| Runs as | HA add-on or Docker (host network) | Docker or package | Package or Docker |

## Common combinations

- **MA + Squeezelite endpoints.** MA's Squeezelite provider is the slimproto server; no
  Lyrion needed. Good default for HA households.
- **MA + Snapcast endpoints.** MA's built-in snapserver, or an external one on 1705.
- **Lyrion + Squeezelite.** Classic, stable, independent of HA.
- **Snapcast alone** fed by MPD/librespot/a pipe: when sync matters more than a library.

## Rules of thumb

- One slimproto server per LAN, or pin every Squeezelite with `-s`.
- One client per output device per endpoint.
- Wired or 5 GHz with power save off for endpoints that drop out.
- Give servers a fixed address; clients store it.
