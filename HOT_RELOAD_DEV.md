# Hot-Reload Development Environment

## Overview

This setup provides a Docker-based development environment with hot-reload for Open WebUI backend code. Changes to Python files in `./backend` are automatically detected and reloaded without manual container restarts.

## Architecture

- Uses the pre-built `ghcr.io/open-webui/open-webui:main` image
- Mounts local `./backend` directory into container at `/app/backend`
- Runs `python /app/backend/open_webui/__init__.py dev --reload --host 0.0.0.0 --port 8080`
- Preserves persistent data in `open-webui:/app/backend/data` volume
- Loads environment from `.env` file

## Launch Commands

### Start Development Environment
```bash
docker compose -f docker-compose.yaml -f docker-compose.dev.yml up -d open-webui
```

### Monitor Logs
```bash
docker compose -f docker-compose.yaml -f docker-compose.dev.yml logs -f open-webui
```

### Stop Environment
```bash
docker compose -f docker-compose.yaml -f docker-compose.dev.yml down
```

## Development Workflow

1. **Start dev environment** (see above)
2. **Edit code** in `./backend` directory
3. **Watch logs** for reload confirmation: `WARNING: WatchFiles detected changes in 'file.py'. Reloading...`
4. **Test changes** in Open WebUI interface at `http://localhost:3000`
5. **Repeat** - no restarts needed!

## Files Modified

- `docker-compose.dev.yml` - Dev environment configuration
- `backend/open_webui/config.py` - Migration target changed to "heads" for multiple branches

## Validation Tests

All acceptance criteria from FRD verified:

✅ **Sync Test**: Local files appear in container  
✅ **Hot-Reload Test**: Code changes trigger automatic reload  
✅ **Persistence Test**: Files remain on disk after container shutdown  

## Environment Variables

Required in `.env`:
- `OPENROUTER_API_KEY` - For OpenRouter API access
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_DB` - Database name

## Notes

- Frontend is pre-built from main image; backend-only hot-reload
- Database migrations run automatically on startup
- CORS warnings are normal for dev
- Use VS Code or editor with file watching for best experience