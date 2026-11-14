# Groups, streams, and clients

## Concepts

- **Stream**: an audio source the snapserver knows about (a fifo, a TCP feed, a spawned process). Defined in `/etc/snapserver.conf` `[stream]` blocks.
- **Group**: a named collection of clients that play the same stream in sync. A client belongs to exactly one group.
- **Client**: a snapclient instance, identified by `hostID`. Bound to one audio sink on its host.

## Relationships

```
stream  <—— bound by ——  group  <—— contains ——  client(s)  ——> sink
```

- Multiple groups can bind to the same stream (they play in sync).
- A client cannot span groups; to play one source on two outputs in different groups, run two snapclient instances.

## Persistence model

- **Streams**: persistent (config file).
- **Groups**: persistent in `<datadir>/server.json`, modifiable via JSON-RPC. Mirror to `installation.json` (groups[] in the overlay) for version control.
- **Client → group binding**: persistent in `server.json`, keyed by hostID.
- **Volume / mute**: persistent per client.

## Implication for the installation record

`installation.json` (groups[] in the overlay) is the version-controlled, human-readable mirror of what's in `server.json`. When the user says "the bedroom group should also include the kitchen client", the agent:

1. Reads the installation record to confirm current state.
2. Issues the JSON-RPC change (or edits the config and reloads).
3. Updates the installation record to match.
4. Commits.

If `server.json` and the installation record ever disagree, treat the live server as authoritative for runtime state and update the record — but flag the divergence to the user, since it usually means someone changed things via the web UI without going through the agent.
