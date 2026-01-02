## Tesla Dashcam AI

Raspberry Pi 5 + Hailo-8L dashcam pipeline for Tesla Model 3 with Cloudflare Workers backend, on-device detections, and a 5" Kivy dashboard. Full architecture details live in `docs/dashcam-tesla-final-architecture.md` and `docs/dashcam-architecture-update.md`.

### Layout
- `pi/` – on-device app (Kivy UI, detection pipelines, services)
- `cloudflare/` – Workers API, Durable Object dashboard hub, queues, workflows
- `dashboard-web/` – optional React dashboard shell
- `scripts/` – deployment helpers for Pi and Cloudflare

### Quick start
- Pi: `cd pi && poetry install && poetry run pytest`
- Cloudflare: `cd cloudflare && npm install && npm test`

Set required env vars listed in the architecture docs before running.
