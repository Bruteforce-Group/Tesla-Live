# Cursor Build Prompt

## Dependencies

### pi/pyproject.toml - dev dependencies
```toml
[tool.poetry.group.dev.dependencies]
ruff = "^0.8.0"
pytest = "^8.0.0"
pytest-asyncio = "^0.24.0"
mypy = "^1.13.0"
pre-commit = "^4.0.0"
```

### cloudflare/package.json - dev dependencies
```json
{
  "devDependencies": {
    "@biomejs/biome": "^1.9.0",
    "@cloudflare/workers-types": "^4.20241205.0",
    "typescript": "^5.7.0",
    "wrangler": "^3.95.0",
    "vitest": "^2.1.0"
  }
}
```
