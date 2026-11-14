# Snapcast JSON-RPC cheatsheet

Endpoint: `tcp://<server>:1705` (control port) or `http://<server>:1780/jsonrpc`.

## Read state

```json
{"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}
```

Returns the entire server state: streams, groups, clients, volumes, mutes. Use this to bootstrap or refresh `installation.json` (groups[] in the overlay).

## Group operations

### Set the stream a group plays
```json
{"id":2,"jsonrpc":"2.0","method":"Group.SetStream","params":{"id":"<group-id>","stream_id":"default"}}
```

### Set the client membership of a group
```json
{"id":3,"jsonrpc":"2.0","method":"Group.SetClients","params":{"id":"<group-id>","clients":["<hostID-1>","<hostID-2>"]}}
```
Note: this also implicitly removes those clients from whatever group they were in.

### Rename a group
```json
{"id":4,"jsonrpc":"2.0","method":"Group.SetName","params":{"id":"<group-id>","name":"new-name"}}
```

### Mute a group
```json
{"id":5,"jsonrpc":"2.0","method":"Group.SetMute","params":{"id":"<group-id>","mute":true}}
```

## Client operations

### Set client volume
```json
{"id":6,"jsonrpc":"2.0","method":"Client.SetVolume","params":{"id":"<hostID>","volume":{"percent":60,"muted":false}}}
```

### Set client latency
```json
{"id":7,"jsonrpc":"2.0","method":"Client.SetLatency","params":{"id":"<hostID>","latency":50}}
```

### Set client name (display label in web UI)
```json
{"id":8,"jsonrpc":"2.0","method":"Client.SetName","params":{"id":"<hostID>","name":"Living Room"}}
```

## Calling from CLI

```bash
echo '{"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}' | nc <server> 1705
```

Or via curl over HTTP:

```bash
curl -s -X POST http://<server>:1780/jsonrpc \
  -H 'Content-Type: application/json' \
  -d '{"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}' | jq .
```

## Important

JSON-RPC changes are **runtime + persisted to `server.json`**, but they do NOT update `/etc/snapserver.conf`. If the user reinstalls the server or restores from a backup that only includes the config file, the groups will be gone. That's why the installation record keeps `installation.json` (groups[] in the overlay) separately.
