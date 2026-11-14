# Ports: what an open port usually means

An open port is a hint. Confirm by asking the service (see the `inventory` skill).

| Port | Protocol | Usually |
| --- | --- | --- |
| 3483 tcp+udp | slimproto | LMS/Lyrion, or Music Assistant's Squeezelite provider. Squeezelite connects here; UDP 3483 is discovery |
| 9000 tcp | http | LMS web + JSON-RPC (`/jsonrpc.js`). MA's Squeezelite provider emulates it (`uuid: aioslimproto`). Also MinIO, Portainer |
| 9090 tcp | telnet-style CLI | LMS CLI, also emulated by MA |
| 8095 tcp | http | Music Assistant API, UI, `/info`, `/api`, `/api-docs` |
| 8097 tcp | http | Music Assistant stream server (players pull audio from here) |
| 1704 tcp | snapcast | Snapcast audio stream to clients |
| 1705 tcp | JSON-RPC | Snapcast control |
| 1780 tcp | http | Snapcast HTTP JSON-RPC (`/jsonrpc`) and Snapweb |
| 4953+ tcp | raw PCM | Snapcast TCP stream sources (MA's built-in snapserver uses 4953-5153) |
| 8123 tcp | http | Home Assistant |
| 7000 tcp | RAOP | AirPlay receiver (shairport-sync, AirPlay speakers) |
| 8009 tcp | Cast | Google Cast device |

mDNS types worth looking for: `_snapcast._tcp`, `_snapcast-http._tcp`, `_raop._tcp`,
`_airplay._tcp`, `_googlecast._tcp`, `_spotify-connect._tcp`, `_home-assistant._tcp`,
`_mass._tcp` (Music Assistant).
