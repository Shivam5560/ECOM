#!/usr/bin/env sh
# consul-register.sh
# Runs at container startup: registers this service with Consul, then
# exec's the actual application process (so PID 1 stays the app).
#
# Required env vars (set in docker-compose.yml):
#   CONSUL_ADDR          - e.g. consul:8500
#   CONSUL_SERVICE_NAME  - e.g. auth-service
#   CONSUL_SERVICE_PORT  - e.g. 8000
#   CONSUL_SERVICE_TAGS  - comma-separated Traefik tags
#
# The container's hostname is used as the service ID so each replica is unique.

set -e

CONSUL_ADDR="${CONSUL_ADDR:-consul:8500}"
SERVICE_NAME="${CONSUL_SERVICE_NAME:-unknown}"
SERVICE_PORT="${CONSUL_SERVICE_PORT:-8000}"
SERVICE_ID="${SERVICE_NAME}-$(hostname)"

# Convert comma-separated tags string → JSON array
# e.g. "tag1,tag2" → ["tag1","tag2"]
tags_json() {
  echo "$CONSUL_SERVICE_TAGS" | awk -v ORS="" '
    BEGIN { printf "[" }
    {
      n=split($0,a,",")
      for(i=1;i<=n;i++){
        gsub(/^ +| +$/,"",a[i])
        printf "\"" a[i] "\""
        if(i<n) printf ","
      }
    }
    END { printf "]" }
  '
}

echo "[consul-register] Registering ${SERVICE_ID} on port ${SERVICE_PORT} with Consul at ${CONSUL_ADDR} ..."

# Wait for Consul to be reachable (max 10s — infra should already be up)
i=0
until curl -fsS "http://${CONSUL_ADDR}/v1/status/leader" >/dev/null 2>&1; do
  i=$((i+1))
  if [ "$i" -ge 10 ]; then
    echo "[consul-register] WARNING: Consul not reachable after 10s — continuing without registration"
    break
  fi
  echo "[consul-register] Waiting for Consul... (${i}/10)"
  sleep 1
done

TAGS=$(tags_json)

# Register service via Consul HTTP API
curl -sf -X PUT "http://${CONSUL_ADDR}/v1/agent/service/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"ID\": \"${SERVICE_ID}\",
    \"Name\": \"${SERVICE_NAME}\",
    \"Address\": \"$(hostname -i | awk '{print $1}')\",
    \"Port\": ${SERVICE_PORT},
    \"Tags\": ${TAGS},
    \"Check\": {
      \"HTTP\": \"http://$(hostname -i | awk '{print $1}'):${SERVICE_PORT}/health\",
      \"Interval\": \"10s\",
      \"Timeout\": \"3s\",
      \"DeregisterCriticalServiceAfter\": \"5m\"
    }
  }" && echo "[consul-register] Registered ${SERVICE_ID} successfully." \
     || echo "[consul-register] WARNING: Registration failed — continuing anyway."

# Hand off to the real application (exec preserves PID 1)
exec "$@"
