#!/bin/sh
# Renders .env (mode 600, gitignored) and the Radicale config from the SOPS store.
# Never prints a secret. Run from the repo root.
set -eu
S="$HOME/Projects/secrets/bin/secret"
V=/Volumes/External/docker/volumes/yuvomi
mkdir -p "$V/data" "$V/backups" "$V/modules" "$V/radicale/data" "$V/radicale/config"
umask 077
{
  echo "PORT=3000"
  echo "SESSION_SECRET=$($S YUVOMI_SESSION_SECRET)"
  echo "DB_ENCRYPTION_KEY=$($S YUVOMI_DB_ENCRYPTION_KEY)"
  echo "SYNC_INTERVAL_MINUTES=5"
  echo "RATE_LIMIT_MAX_ATTEMPTS=10"
} > .env
cat > "$V/radicale/config/config" <<'CFG'
[server]
hosts = 0.0.0.0:5232
[auth]
type = htpasswd
htpasswd_filename = /config/users
htpasswd_encryption = bcrypt
[storage]
filesystem_folder = /data/collections
[logging]
level = info
CFG
HASH=$(docker run --rm --entrypoint /venv/bin/python3 tomsquest/docker-radicale:latest -c \
  "import bcrypt,sys;print(bcrypt.hashpw(sys.argv[1].encode(),bcrypt.gensalt()).decode())" "$($S YUVOMI_RADICALE_PASSWORD)")
echo "carlos:$HASH" > "$V/radicale/config/users"
chmod 600 "$V/radicale/config/users" .env
echo rendered
