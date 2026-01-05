## Tesla Dashcam AI

Raspberry Pi 5 + Hailo-8L dashcam pipeline for Tesla Model 3 with Cloudflare Workers backend, on-device detections, and a 5" Kivy dashboard. Full architecture details live in `docs/dashcam-tesla-final-architecture.md` and `docs/dashcam-architecture-update.md`.

### Layout
- `pi/` – on-device app (Kivy UI, detection pipelines, services)
- `cloudflare/` – Workers API, Durable Object dashboard hub, queues, workflows
- `dashboard-web/` – optional React dashboard shell
- `scripts/` – deployment helpers for Pi and Cloudflare
- `docs/ai-camera-strategy-alignment.md` – how this project implements the provided object detection strategy (models, masking, audio, metadata, testing)
- `.githooks/` – local git hooks; pre-commit keeps `cursor-rules` submodule synced

### Quick start
- Pi: `cd pi && poetry install && poetry run pytest`
- Cloudflare: `cd cloudflare && npm install && npm test`

### Git hooks
- To enforce keeping the `cursor-rules` submodule on the latest `main`, set hooks path once:  
  `bash scripts/install-git-hooks.sh`

Set required env vars listed in the architecture docs before running.
