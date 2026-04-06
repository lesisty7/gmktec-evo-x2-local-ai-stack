#!/bin/sh
set -eu

require_env() {
  name="$1"
  eval "val=\${$name:-}"
  if [ -z "$val" ]; then
    echo "[bootstrap] missing required env: $name" >&2
    exit 1
  fi
}

require_env MATTERMOST_BASE_URL
require_env MATTERMOST_SITE_URL
require_env MATTERMOST_ADMIN_USERNAME
require_env MATTERMOST_ADMIN_EMAIL
require_env MATTERMOST_ADMIN_PASSWORD
require_env MATTERMOST_TEAM_NAME
require_env MATTERMOST_TEAM_DISPLAY_NAME
require_env MATTERMOST_CHANNEL_NAME
require_env MATTERMOST_CHANNEL_DISPLAY_NAME
require_env MATTERMOST_WEBHOOK_NAME

api="$MATTERMOST_BASE_URL/api/v4"

echo "[bootstrap] waiting for Mattermost at $MATTERMOST_BASE_URL"
i=0
until curl -fsS "$api/system/ping" >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 90 ]; then
    echo "[bootstrap] Mattermost did not become ready in time" >&2
    exit 1
  fi
  sleep 2
done

echo "[bootstrap] ensuring admin user exists"
admin_payload=$(jq -n \
  --arg email "$MATTERMOST_ADMIN_EMAIL" \
  --arg username "$MATTERMOST_ADMIN_USERNAME" \
  --arg password "$MATTERMOST_ADMIN_PASSWORD" \
  '{email: $email, username: $username, password: $password}')

create_code=$(curl -sS -o /tmp/mm-admin-create.json -w "%{http_code}" \
  -H "Content-Type: application/json" \
  -d "$admin_payload" \
  "$api/users")

if [ "$create_code" = "201" ]; then
  echo "[bootstrap] admin user created"
else
  echo "[bootstrap] admin create returned $create_code (likely already exists)"
fi

echo "[bootstrap] logging in as admin"
login_payload=$(jq -n \
  --arg login_id "$MATTERMOST_ADMIN_USERNAME" \
  --arg password "$MATTERMOST_ADMIN_PASSWORD" \
  '{login_id: $login_id, password: $password}')

curl -sS -D /tmp/mm-login-headers.txt -o /tmp/mm-login.json \
  -H "Content-Type: application/json" \
  -d "$login_payload" \
  "$api/users/login"

token=$(awk -F': ' 'tolower($1)=="token" {print $2}' /tmp/mm-login-headers.txt | tr -d '\r')
if [ -z "$token" ]; then
  echo "[bootstrap] failed to obtain auth token; check admin credentials" >&2
  exit 1
fi

auth_header="Authorization: Bearer $token"

echo "[bootstrap] ensuring team exists: $MATTERMOST_TEAM_NAME"
team_code=$(curl -sS -o /tmp/mm-team.json -w "%{http_code}" \
  -H "$auth_header" \
  "$api/teams/name/$MATTERMOST_TEAM_NAME")

if [ "$team_code" = "200" ]; then
  team_id=$(jq -r '.id' /tmp/mm-team.json)
else
  team_payload=$(jq -n \
    --arg name "$MATTERMOST_TEAM_NAME" \
    --arg display_name "$MATTERMOST_TEAM_DISPLAY_NAME" \
    '{name: $name, display_name: $display_name, type: "O"}')
  curl -sS -o /tmp/mm-team-create.json \
    -H "$auth_header" \
    -H "Content-Type: application/json" \
    -d "$team_payload" \
    "$api/teams"
  team_id=$(jq -r '.id' /tmp/mm-team-create.json)
fi

if [ -z "$team_id" ] || [ "$team_id" = "null" ]; then
  echo "[bootstrap] could not determine team_id" >&2
  exit 1
fi

echo "[bootstrap] ensuring channel exists: $MATTERMOST_CHANNEL_NAME"
channel_code=$(curl -sS -o /tmp/mm-channel.json -w "%{http_code}" \
  -H "$auth_header" \
  "$api/teams/$team_id/channels/name/$MATTERMOST_CHANNEL_NAME")

if [ "$channel_code" = "200" ]; then
  channel_id=$(jq -r '.id' /tmp/mm-channel.json)
else
  channel_payload=$(jq -n \
    --arg team_id "$team_id" \
    --arg name "$MATTERMOST_CHANNEL_NAME" \
    --arg display_name "$MATTERMOST_CHANNEL_DISPLAY_NAME" \
    '{team_id: $team_id, name: $name, display_name: $display_name, type: "O"}')
  curl -sS -o /tmp/mm-channel-create.json \
    -H "$auth_header" \
    -H "Content-Type: application/json" \
    -d "$channel_payload" \
    "$api/channels"
  channel_id=$(jq -r '.id' /tmp/mm-channel-create.json)
fi

if [ -z "$channel_id" ] || [ "$channel_id" = "null" ]; then
  echo "[bootstrap] could not determine channel_id" >&2
  exit 1
fi

echo "[bootstrap] creating incoming webhook"
hook_payload=$(jq -n \
  --arg channel_id "$channel_id" \
  --arg display_name "$MATTERMOST_WEBHOOK_NAME" \
  '{channel_id: $channel_id, display_name: $display_name}')

hook_id=$(curl -sS \
  -H "$auth_header" \
  -H "Content-Type: application/json" \
  -d "$hook_payload" \
  "$api/hooks/incoming" | jq -r '.id')

if [ -z "$hook_id" ] || [ "$hook_id" = "null" ]; then
  echo "[bootstrap] webhook creation failed" >&2
  exit 1
fi

echo "[bootstrap] incoming webhook URL:"
echo "$MATTERMOST_SITE_URL/hooks/$hook_id"
