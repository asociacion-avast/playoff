# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based member and activity management system for AVAST (Asociación Valenciana de Apoyo a las Altas Capacidades). It integrates with Playoff Informática's API to manage members (socios), activities (actividades), enrollments (inscripciones), and automated workflows.

The system operates in offline-first mode with optimistic updates and a mutation outbox for sync when online.

## Authentication Setup

All scripts require `~/.avast.ini` with:

```ini
[auth]
endpoint=asociacionavast
username=myusername
password=mypass
RWusername=myRWusername
RWpassword=myRWpassword
```

- Regular credentials (username/password): read-only operations
- RW credentials (RWusername/RWpassword): write operations (mutations)

## Core Architecture

### Data Flow

1. **Data Download** (scripts 0-_, 1-_, 2-\*): Fetch data from API, cache as JSON in `data/` directory
2. **Analysis & Reporting** (scripts 3-\*): Read cached JSON, generate reports, no mutations
3. **Automated Processing** (scripts 4-\*): Business logic + mutations (categories, telegram IDs, enrollments)
4. **Administrative Actions** (scripts 5-\*): Create/modify activities, upload to WordPress

### Key Modules

- **`common.py`**: Core library with API client, auth, entity operations, and shared business logic
- **`sync_store.py`**: Offline-first layer - entity cache, mutation outbox, optimistic patches
- **`data/`**: JSON cache directory for socios, actividades, inscripciones, and entity snapshots
- **`data/entities/`**: Entity-level cache (colegiat/, activitat/) with metadata tracking
- **`data/outbox.json`**: Pending mutations queue for offline→online sync

### Category System

Member categories are defined in `common.categorias` dictionary (e.g., `acogida: 74`, `adultoconactividades: 60`). Categories determine member type, payment schedules, and activity access.

Key category groups:

- **Pre-registration**: 32, 33, 54, 59, 85, 86 → Converted to active via `cambiospreinscrip` mapping
- **Active adults**: 53 (without activities), 60 (with activities)
- **Active members**: 1 (without activities), 12 (with activities), 13 (siblings)
- **Age-based**: 36-48, 50-51, 55-57, 68-72 (birth years 2000-2024)
- **AVAST special**: 65 (Avast 15), 66 (Avast 13), 77 (Avast 18)
- **Administrative**: 103 (unpaid), 105 (annual unpaid), 84 (pending card)

### Telegram Integration

Custom fields in Playoff for Telegram IDs:

- `tutor1`: 0_13_20231012041710
- `tutor2`: 0_14_20231012045321
- `socioid`: 0_16_20241120130245
- `fechacambio`: 0_17_20250221121130 (date for auto-category changes)

Scripts 4-\* handle Telegram ID self-service and validation.

### Offline-First Mutations

All write operations go through `common.mutate()`:

1. Apply optimistic patch to local cache (`sync_store.apply_patch()`)
2. If online: execute API call; on failure, queue to outbox
3. If offline: queue to outbox immediately
4. Use `common.flush_outbox(token)` to sync pending mutations

Supported operations:

- `addcategoria` / `delcategoria`: Member category management
- `escribecampo`: Update custom fields
- `create_inscripcio` / `anula_inscripcio` / `delete_inscripcio`: Enrollment operations
- `enviacomunicado`: Send email notifications

### Performance Optimizations

The codebase has been heavily optimized (50-1000x improvements):

- **Phase 1**: ujson instead of json, pre-computed validations
- **Phase 2**: HTTP session reuse, LRU caches, pre-computed category lists (`_cached_categorias`)
- **Phase 3**: Cached translations (`@lru_cache` on `traduce()`)
- **Phase 4**: Parallel processing support (`process_socios_parallel()`)

When adding new scripts:

- Use `_http_session` for API calls (connection pooling)
- Check for `_cached_categorias` before calling `getcategoriassocio()`
- Use `_valid_alta`, `_valid_preinscripcion`, `_valid_baja` pre-computed flags on socio objects
- Import ujson at top: `try: import ujson as json / except: import json`

## Common Development Tasks

### Running Scripts

Scripts are numbered by phase:

```bash
# Data download (run in order)
./0-soci.py              # Download members
./0-categorias.py        # Download categories
./1-activi.py            # Download activities
./1-socios-familias.py   # Update family relationships
./2-sociosporactiv.py    # Download enrollments per activity

# Analysis (read-only)
./3-listado-socios-categoria.py   # List members by category
./3-actividades-con-huecos.py     # Show activity vacancies

# Automated processing (mutations)
./4-auto-categoria.py             # Auto-assign age/special categories
./4-auto-alta-socios.py           # Process pre-registrations → active
./4-auto-cambios-modalidad.py     # Process scheduled category changes

# Administrative
./5-generar-horario.py            # Generate HTML schedule
./5-actualiza-wordpress.py        # Upload to WordPress
```

### Testing

No automated test suite. Manual testing via:

```bash
# Lint and format (pre-commit hooks)
pre-commit run --all-files

# Test data sync
./sync.py status
./sync.py check
```

Tox environments:

```bash
tox -e py3              # Generate full schedule + web descriptions
tox -e html_upload      # Upload HTML to WordPress (requires ANIO env var)
```

### Data Sync Management

**All sync operations should use the unified `sync.py` command.** Do not create separate scripts for sync-related functionality unless explicitly required for a specific business need.

```bash
./sync.py status        # Check cache freshness, outbox, connectivity
./sync.py download      # Download fresh data from Playoff API
./sync.py push          # Upload pending mutations to API
./sync.py clean         # Remove stale mutations for deleted socios
./sync.py check         # Detailed outbox inspection
./sync.py retry-failed  # Retry failed mutations
./sync.py pull          # Pull changed member entities from API
./sync.py evict         # Remove stale entity cache files
```

Use `./sync.py --help` for complete usage information.

### Adding a New Script

**Important**: Do not create new utility scripts for data sync operations. Use `sync.py` subcommands instead. Only create new scripts for business logic (category automation, reporting, data processing).

1. Start with shebang `#!/usr/bin/env python` and imports from `common`
2. Read config: `config = configparser.ConfigParser(); config.read(os.path.expanduser("~/.avast.ini"))`
3. Get token:
   - Read-only: `token = common.gettoken()`
   - Write ops: `token = common.gettoken(user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"])`
4. Load data: `socios = common.readjson("socios")`
5. Use `common.validasocio()` for member state checks
6. Use `common.getcategoriassocio(socio)` to get category IDs (uses cache)
7. For mutations, use `common.addcategoria()`, `common.delcategoria()`, etc. (not the `_api` versions)
8. All mutations automatically use the offline-first mechanism via `common.mutate()`

### Working with Enrollment Data

```python
# Fetch inscriptions for an activity (cache-first)
inscritos = common.read_inscripciones_actividad(token, idactividad)

# Force refresh from API
inscritos = common.read_inscripciones_actividad(token, idactividad, refresh=True)

# Legacy direct update (prefer read_inscripciones_actividad)
common.updateactividad(token, idactividad, force=True)
```

### Validation Patterns

```python
# Check active member (not pre-registration, not baja)
if common.validasocio(
    socio,
    estado="COLESTVAL",
    estatcolegiat="ESTALTA",
    agrupaciones=["PREINSCRIPCIÓN"],
    reverseagrupaciones=True,
):
    # Active member logic
    pass

# Check pre-registration
if common.validasocio(socio, estado="COLESTPRE", estatcolegiat="ESTALTA"):
    # Pre-registration logic
    pass

# Use pre-computed flags (faster)
if socio.get("_valid_alta"):
    # Active member
    pass
if socio.get("_valid_preinscripcion"):
    # Pre-registration
    pass
```

## Code Quality

- **Linter**: ruff (configured in ruff.toml, runs via pre-commit)
- **Formatter**: ruff-format (runs via pre-commit)
- **Import sorting**: isort (configured in .isort.cfg)
- **Pre-commit hooks**: Run `pre-commit install` after clone
- **Commit messages**: Conventional Commits enforced via commitizen

## Codebase Conventions

- All scripts are executable (`chmod +x`)
- Scripts prefixed by phase number (0-5)
- Use `common.readjson()` / `common.writejson()` for data directory I/O
- Always check `if is_online()` before optional API calls
- Member = socio/colegiat, Activity = activitat, Enrollment = inscripció
- Date format: ISO 8601 where possible; API sometimes uses dd/mm/yyyy
- Print progress with `flush=True` for long-running operations

## WordPress Integration

WordPress credentials in `~/.wordpressauth.json`:

```json
{
  "url": "https://example.com",
  "username": "user",
  "password": "app_password"
}
```

WordPress page IDs in `wordpress.json` (maps year → page ID for schedule uploads).
