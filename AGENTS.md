# Yuvomi (one-week trial, fork of ulsklyc/yuvomi)

Fork `carloscae/yuvomi`, `upstream` = ulsklyc/yuvomi. Trial of a family hub: iCloud Calendar two-way via CalDAV, tasks mirrored to a Radicale container (so iOS Reminders can show them), MCP endpoint for agents. Background: vault page `personal/projects/family-hub-alternatives-2026-10.md`. Fallback if it fails: Tribu.

Upstream code is untouched. Our additions: `AGENTS.md`, `docker-compose.m4.yml`, `scripts/m4-*.sh`, `scripts/mcp-omlx-test.py`, `docs/icloud-sync.md`, `docs/handoff.md`. Never patch upstream files without a written reason in `docs/handoff.md`.

## Deploy (Mac mini M4, OrbStack)

- `scripts/m4-render-env.sh` renders `.env` and the Radicale config from `~/Projects/secrets/` (keys `YUVOMI_*`). Then `docker compose -f docker-compose.m4.yml up -d`.
- Both ports bind the Tailscale IP 100.76.99.98 only: Yuvomi 3100, Radicale 5233. Data under `/Volumes/External/docker/volumes/yuvomi/`.
- Image is the upstream multi-arch `ghcr.io/ulsklyc/yuvomi:latest` (no local build, so no ltp-heavy lock). A local build is a heavy gate: use `lockf -k /Volumes/External/scratch/ltp-heavy.lock`.
- `DB_ENCRYPTION_KEY` cannot be recovered or changed. It lives in the secrets store as `YUVOMI_DB_ENCRYPTION_KEY`.

## Git

Push to main of `carloscae/yuvomi` after the repo's local checks. No PRs. Stage named files. Never push to `upstream`.

## Open, needs Carlos

- iCloud app-specific password (account.apple.com, Sign-In and Security, App-Specific Passwords). Store it with `secret-set -f YUVOMI_ICLOUD_APP_PASSWORD` (value on stdin), then run the steps in `docs/icloud-sync.md`.
- oMLX on the M5 is not reachable from the M4 until the edited plist is loaded (see `docs/handoff.md`).

## Simulators

Use only the shared simulators (iOS/watchOS 27.0): iPhone 17e (small), iPhone 17 (regular), iPhone 18 Pro Max (large), Apple Watch Series 12 46mm. Never `simctl create` per-task or per-build devices: 22 of them filled the internal disk (Carlos, 2026-11-04). Need a clean state: `simctl erase` the shared one and say so. Need an odd size once: create it and `simctl delete <uuid>` in the same session. Memory: `feedback_use-the-shared-simulators-never-create-new-ones-2026-11-04`.
