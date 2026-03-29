# kuma-pusher

Monitors hosts via ICMP ping or TCP connect and pushes status to [Uptime Kuma](https://github.com/louislam/uptime-kuma) push monitors.

## Monitor format

Each monitor is one line in the `MONITORS` env var:

```
host|https://uptime-kuma/api/push/<token>|<check>
```

**Check types:**

| Check | Behavior |
|-------|----------|
| `ping` | ICMP ping |
| `tcp:PORT` | TCP connect to PORT |

**Examples:**

```
my-server.lan|https://uptime-kuma.example.com/api/push/abc123|ping
alexa.fritz.box|https://uptime-kuma.example.com/api/push/xyz789|tcp:4070
```

## Configuration

All config is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONITORS` | *(required)* | Newline-separated monitor entries (see above) |
| `INTERVAL` | `30` | Seconds between check cycles |
| `PING_COUNT` | `1` | Number of pings per ICMP check |
| `PING_TIMEOUT_S` | `1` | Timeout in seconds per check |
| `FORCE_IPV4` | `true` | Force IPv4 for all checks |
| `SEND_DOWN` | `true` | Push a "down" status when a check fails |

## Kubernetes

The container requires `NET_RAW` capability for ICMP ping:

```yaml
securityContext:
  capabilities:
    add: [NET_RAW]
    drop: [ALL]
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  seccompProfile:
    type: RuntimeDefault
```

## Docker

```bash
docker run --cap-add NET_RAW \
  -e MONITORS="my-host.lan|https://uptime-kuma.example.com/api/push/abc|ping" \
  ghcr.io/schaurian/kuma-pusher
```
