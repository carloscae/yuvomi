# Yuvomi: iCloud, Reminders and MCP, can / can't / limits (2026-10-19)

Sources: README, `docs/installation.md` (Apple CalDAV, "CalDAV tasks are not syncing"), `server/utils/caldav-client.js`, `server/routes/calendar/caldav.js`, `server/mcp/*`. Behaviour marked "tested" was run against the live deploy on the Mac mini (Radicale as the server); iCloud itself is untested, no app-specific password exists yet.

## Calendar (events)

| | |
|---|---|
| Can | Two-way CalDAV for iCloud, Nextcloud, Radicale, Baikal. Create, edit, delete and move between calendars flow both ways. Attendees, alarms, categories and exceptions already on the server are preserved on edit. Several accounts, managed under Settings, Modules, Calendar, Calendar sync (REST: `POST /api/v1/calendar/caldav/accounts` with `name, caldavUrl, username, password`). |
| Tested | Radicale to Yuvomi (event PUT on the server shows in Yuvomi after a sync) and Yuvomi to Radicale (event with `target_caldav_account_id` + `target_caldav_calendar_url` lands as `yuvomi-event-<id>-...ics`). Sync runs every `SYNC_INTERVAL_MINUTES` (set to 5 here) and on save. |
| Can't | Alarms are not imported and Yuvomi writes none of its own: an event it creates on iCloud has no alarm, Yuvomi's reminders fire from Yuvomi only (push or notification channels). A new calendar must be switched on per account (new calendars start off by design) and a Yuvomi event goes to iCloud only when it has a target calendar. |
| Limits | iCloud: needs 2FA and an app-specific password (max 25, revoked when the Apple ID password changes). Use `https://caldav.icloud.com`; Yuvomi's origin guard compares scheme, host and port of each selected calendar, and iCloud serves calendars from `pNN-caldav.icloud.com`. tsdav resolves this in discovery, but it is the first thing to check if the first iCloud sync lists calendars and then refuses to read them (`origin_not_allowed` in `docker logs yuvomi`). Events synced before upgrading to a pre-1.52 version need one run first (irrelevant for a fresh install). |

## Tasks and Reminders

| | |
|---|---|
| Can | Two-way VTODO mirror between CalDAV task lists and Yuvomi Tasks or Shopping. A list is mapped (tasks or shopping) and enabled per household under Settings, Modules, Tasks, Reminder sync. Once enabled for Tasks it becomes a "sync target" in the task dialog (REST: `sync_target: "caldav:<accountId>\|<listUrl>"`). Tested: a task created in Yuvomi with a target appeared in the Radicale list (`yuvomi-task-<id>-...ics`). |
| Can't | **iCloud Reminders is not a CalDAV source** since iOS 13 / macOS 10.15 (upgraded lists live in a private store). Yuvomi's own docs say so. So Yuvomi tasks cannot be written to the real iCloud Reminders lists. The supported route, and what is set up here: Radicale holds the task list, Yuvomi mirrors it, the iPhone adds Radicale as a CalDAV account (Settings, Reminders, Accounts, Add Account, Other, CalDAV) and shows it in Reminders under "Other". |
| Limits | A task without a target stays local. A synced task cannot move to another list. Subtasks are never uploaded alone. A locked task's mirrored fields are still rewritten by inbound sync. |

iPhone setup values for Radicale: server `100.76.99.98`, port `5233`, user `carlos`, password in the secrets store (`YUVOMI_RADICALE_PASSWORD`), SSL off (plain HTTP over Tailscale; the phone must be on Tailscale). Collection: `/carlos/family-tasks/`.

## MCP / API

- Endpoint `POST /mcp` (Streamable HTTP, stateless, JSON-RPC 2.0, protocol 2025-06-18 and two older). Auth: `Authorization: Bearer <API token>` (or `x-api-key`). No batches, no SSE stream, no resources or prompts, only tools.
- API tokens: admin only, `POST /api/v1/auth/api-tokens` (needs a login session and the CSRF header), optional `scopes: ["tasks:read", ...]` and `expires_at`; shown once. Prefix `yuvomi_`. Stored here as `YUVOMI_MCP_TOKEN` in the secrets store (full-access token, subject = the admin test account).
- Tools (9): `list_tasks`, `create_task`, `list_shopping_items`, `add_shopping_item`, `list_upcoming_events`, `create_event`, plus a REST bridge: `list_api_operations`, `get_api_operation`, `call_api_operation` (reaches everything in the OpenAPI 3.1 spec, which is why the token scope matters). Spec: the OpenAPI document served by the app (`server/openapi.js`).
- Tested with `scripts/mcp-omlx-test.py` (see handoff): `Qwen3.8-27B-4bit` on oMLX called `create_task` and `list_tasks` over MCP.

## Footprint

README claim 256 MB. Measured (`docker stats --no-stream`, OrbStack, arm64 image `ghcr.io/ulsklyc/yuvomi:latest`, 594 MB on disk): Yuvomi 140 to 156 MiB, Radicale 24 MiB, idle after a few syncs. One SQLite file (encrypted with SQLCipher, key in the secrets store), data 6 MB.

## Steps once the iCloud app-specific password exists

1. `secret-set -f YUVOMI_ICLOUD_APP_PASSWORD` (value on stdin), Apple ID e-mail as `YUVOMI_ICLOUD_USER`.
2. Log in (see `docs/handoff.md` for the curl recipe), `POST /api/v1/calendar/caldav/accounts` with `caldavUrl=https://caldav.icloud.com`.
3. `GET /api/v1/calendar/caldav/accounts/<id>/calendars?refresh=true`, then `PATCH` the one calendar to test with `enabled: true`. Use a throwaway iCloud calendar, not the main one.
4. Create an event in Calendar.app on that calendar, `POST /api/v1/calendar/caldav/sync`, check `GET /api/v1/calendar?from=&to=`. Reverse: create an event with `target_caldav_account_id` and `target_caldav_calendar_url` and check Calendar.app.
