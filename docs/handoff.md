# Yuvomi trial handoff (2026-10-19)

**Status 2026-10-24: in use, no longer only a trial.** Household was retired the same day and its data moved here; Yuvomi is now the only live copy of the family recipes, body measurements and nutrition targets, and the back end Hermes (M5, house profile) talks to. The 2026-10-26 trial end below is superseded. Retirement log with the details: `~/Projects/household/docs/retirement-2026-10-24.md`.

Fork `carloscae/yuvomi` (upstream ulsklyc/yuvomi, v2.78.0, no code patched). Trial window was one week from 2026-10-19, fallback Tribu. Detail on limits: `docs/icloud-sync.md`.

## What runs (Mac mini M4, OrbStack)

| Thing | Where |
|---|---|
| Yuvomi | `https://mac-mini.tailfa4cdf.ts.net:8443` (`tailscale serve` to 127.0.0.1:3100; Hermes uses this), `http://100.76.99.98:3100` (Tailscale only, nothing on LAN), container `yuvomi`, image `ghcr.io/ulsklyc/yuvomi:latest` (pulled, not built, so no lockf needed) |
| Radicale | `http://100.76.99.98:5233`, container `yuvomi-radicale`, user `carlos`, collection `/carlos/family-tasks/` (VTODO) |
| Compose / env | `docker-compose.m4.yml`, `scripts/m4-render-env.sh` (renders `.env` and Radicale config from the secrets store, never prints) |
| Data | `/Volumes/External/docker/volumes/yuvomi/{data,backups,modules,radicale}`; SQLite is SQLCipher-encrypted; nightly app backup at 02:00 into `backups/` (same drive as the data, no off-drive copy) |
| Secrets (`~/Projects/secrets/`) | `YUVOMI_SESSION_SECRET`, `YUVOMI_DB_ENCRYPTION_KEY` (unrecoverable, never rotate), `YUVOMI_ADMIN_PASSWORD`, `YUVOMI_RADICALE_PASSWORD`, `YUVOMI_MCP_TOKEN` |
| Accounts | the admin test account plus the family members (Carlos, Victoria, Feline as child) with caregiver grants; API token `hermes-house` (secret `YUVOMI_HERMES_TOKEN`, scoped, acts as Carlos) for Hermes. The raw token is in the top-level `token` field of the create response. |
| Memory | Yuvomi 140-156 MiB, Radicale 24 MiB (`docker stats --no-stream`); limits 512m / 128m |

Test residue (harmless, delete any time): tasks "mcp smoke test", "Yuvomi to Radicale test", "oMLX MCP test"; Radicale calendar `/carlos/probe-events/` with two probe events, enabled on Yuvomi's CalDAV account 1 ("Radicale (tasks)"). Scratch: `/Volumes/External/scratch/yuvomi-*`.

Ops: `docker compose -f docker-compose.m4.yml up -d | down | logs`. Update: `docker compose -f docker-compose.m4.yml pull && ... up -d`. Login for REST calls: `POST /api/v1/auth/login` `{username, password}` with a cookie jar, then send the `csrf-token` cookie as `X-CSRF-Token` on writes.

## Verified (commands run today)

- Tailscale URL: `curl http://100.76.99.98:3100/health` returns 200; a LAN-IP request to port 3100 fails (bind is Tailscale only).
- Tasks to Radicale: task created with `sync_target`, after `POST /api/v1/calendar/caldav/reminders/sync` the `.ics` is in `/carlos/family-tasks/` (PROPFIND). Inbound direction not tested for tasks.
- Events two-way, **against Radicale, not iCloud**: external event shows in Yuvomi after sync; Yuvomi event with a target shows in Radicale.
- MCP + model: `scripts/mcp-omlx-test.py` run on the M5 over SSH (M5 reaches Yuvomi over Tailscale, oMLX on its loopback, no key needed today). `Qwen3.8-27B-4bit` returned `tool_calls`, the script ran `create_task` and `list_tasks` on `/mcp`, final answer correct. oMLX log `~/splash/omlx.log` 10:03 local: three `Chat completion ... finish_reason=tool_calls` / final lines.

## Not verified, blocked on Carlos

1. **iCloud two-way events.** No app-specific password exists. Create it at account.apple.com (Sign-In and Security, App-Specific Passwords), store with `secret-set -f YUVOMI_ICLOUD_APP_PASSWORD` (value on stdin, flags before key) and tell the lead; steps are at the end of `docs/icloud-sync.md`. Use a throwaway iCloud calendar first.
2. **Reminders on the iPhone.** Yuvomi cannot touch real iCloud Reminders (Apple moved them off CalDAV in iOS 13). The Radicale list shows in Reminders only after Carlos adds a CalDAV account on the phone (values in `docs/icloud-sync.md`), under "Other", not in the iCloud lists. Decide if that is acceptable; it is the supported design.
3. **oMLX from the M4.** The M5 plist edit (bind 0.0.0.0 + `--api-key`) from the Kinhold work is still NOT loaded; oMLX stays loopback-only. Not needed for this trial (the proof ran on the M5). If the lead loads it, every oMLX caller incl. Hermes must send the key.

## Hermes (applied 2026-10-24)

The house profile on the M5 has a `yuvomi` MCP server at the 8443 URL with `Authorization: Bearer ${YUVOMI_HERMES_TOKEN}` and an allowlist of 7 tools. `100.76.99.98:3100` is not reachable from the M5. A daily no-agent job recomputes nutrition targets from the latest vitals and prints only on change. Detail: vault `personal/projects/homelab/m5-deployment-runbook`, section "What runs in the house profile".

## Decision for the lead

Superseded 2026-10-24: Yuvomi stays, the Household database is deleted. `docker compose -f docker-compose.m4.yml down` stops Hermes's back end (data stays). Cost: ~165 MiB RAM, one 594 MB image. Kinhold is a separate parked effort, listed in `~/Projects/kinhold/docs/handoff.md` (image `kinhold-home:dev`, DB `kinhold_v2`, repo, M5 plist edit); nothing of it was deleted.
