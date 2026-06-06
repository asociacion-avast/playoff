#!/usr/bin/env python

"""Offline sync layer: entity cache, mutation outbox, optimistic patches."""

import hashlib
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Use ujson (ultra-fast) if available, fallback to standard json (OPTIMIZATION)
try:
    import ujson as json
except ImportError:
    import json

import requests

DATA_DIR = Path("data")
ENTITIES_DIR = DATA_DIR / "entities"
META_FILE = DATA_DIR / "_meta.json"
OUTBOX_FILE = DATA_DIR / "outbox.json"

SCHEMA_VERSION = 1
_ONLINE_CACHE = {"result": None, "checked_at": 0.0}
_ONLINE_TTL = 30


def _utcnow():
    return datetime.now(timezone.utc).isoformat()


def _ensure_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    ENTITIES_DIR.mkdir(exist_ok=True)
    (ENTITIES_DIR / "colegiat").mkdir(parents=True, exist_ok=True)
    (ENTITIES_DIR / "activitat").mkdir(parents=True, exist_ok=True)


def read_meta():
    _ensure_dirs()
    if not META_FILE.exists():
        return {"schema_version": SCHEMA_VERSION, "entities": {}, "last_pull": None}
    with META_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def write_meta(meta):
    _ensure_dirs()
    with META_FILE.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=4)


def _entity_key(entity_type, entity_id):
    return f"{entity_type}:{entity_id}"


def _entity_path(entity_type, entity_id):
    return ENTITIES_DIR / entity_type / f"{entity_id}.json"


def _subresource_path(entity_type, entity_id, resource):
    return ENTITIES_DIR / entity_type / str(entity_id) / f"{resource}.json"


def mark_entity_meta(entity_type, entity_id, *, dirty=False, fetched=False):
    meta = read_meta()
    key = _entity_key(entity_type, entity_id)
    entry = meta.setdefault("entities", {}).setdefault(key, {})
    if dirty:
        entry["dirty"] = True
    if fetched:
        entry["last_fetched_at"] = _utcnow()
        entry.setdefault("dirty", False)
    write_meta(meta)


def is_online(apiurl, timeout=5):
    if _ONLINE_CACHE["result"] is not None:
        if time.time() - _ONLINE_CACHE["checked_at"] < _ONLINE_TTL:
            return _ONLINE_CACHE["result"]
    try:
        requests.get(apiurl, timeout=timeout)
        result = True
    except requests.RequestException:
        result = False
    _ONLINE_CACHE["result"] = result
    _ONLINE_CACHE["checked_at"] = time.time()
    return result


def read_outbox():
    _ensure_dirs()
    if not OUTBOX_FILE.exists():
        return []
    with OUTBOX_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def write_outbox(entries):
    _ensure_dirs()
    with OUTBOX_FILE.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=4)


def enqueue_mutation(op, entity, entity_id, payload):
    entries = read_outbox()
    dedup_key = (op, str(entity_id), json.dumps(payload, sort_keys=True))
    for entry in entries:
        if (
            entry.get("status") == "pending"
            and (
                entry["op"],
                str(entry["entity_id"]),
                json.dumps(entry.get("payload", {}), sort_keys=True),
            )
            == dedup_key
        ):
            return entry["id"]
    entry = {
        "id": str(uuid.uuid4()),
        "op": op,
        "entity": entity,
        "entity_id": entity_id,
        "payload": payload,
        "created_at": _utcnow(),
        "status": "pending",
        "retries": 0,
        "last_error": None,
    }
    entries.append(entry)
    write_outbox(entries)
    return entry["id"]


def outbox_counts():
    entries = read_outbox()
    counts = {"pending": 0, "failed": 0, "synced": 0}
    for entry in entries:
        status = entry.get("status", "pending")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _load_socio_from_snapshot(socio_id):
    socios_file = DATA_DIR / "socios.json"
    if not socios_file.exists():
        return None
    with socios_file.open(encoding="utf-8") as f:
        socios = json.load(f)
    for socio in socios:
        if int(socio["idColegiat"]) == int(socio_id):
            return socio
    return None


def _save_socio_snapshot(socio):
    socios_file = DATA_DIR / "socios.json"
    if not socios_file.exists():
        return
    with socios_file.open(encoding="utf-8") as f:
        socios = json.load(f)
    socio_id = int(socio["idColegiat"])
    updated = False
    for index, item in enumerate(socios):
        if int(item["idColegiat"]) == socio_id:
            socios[index] = socio
            updated = True
            break
    if updated:
        with socios_file.open("w", encoding="utf-8") as f:
            json.dump(socios, f, ensure_ascii=False, indent=4)


def _print_progress(label, current, total):
    pct = int(100 * current / total) if total else 100
    print(f"{label}: {current}/{total} ({pct}%)", flush=True)


def save_entity(
    entity_type,
    entity_id,
    data,
    *,
    dirty=False,
    skip_snapshot=False,
    skip_meta=False,
):
    _ensure_dirs()
    path = _entity_path(entity_type, entity_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    if not skip_meta:
        mark_entity_meta(entity_type, entity_id, dirty=dirty, fetched=True)
    if entity_type == "colegiat" and not skip_snapshot:
        _save_socio_snapshot(data)


def read_entity(entity_type, entity_id, fetch_fn=None):
    data = None
    path = _entity_path(entity_type, entity_id)
    if path.exists():
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    elif entity_type == "colegiat":
        data = _load_socio_from_snapshot(entity_id)
        if data is not None:
            save_entity(entity_type, entity_id, data)
    elif fetch_fn is not None:
        data = fetch_fn(entity_id)
        if data is not None:
            save_entity(entity_type, entity_id, data)
    if entity_type == "colegiat" and data is not None:
        enrich_socio_modalitats(data)
    return data


def read_subresource(entity_type, entity_id, resource, fetch_fn=None):
    _ensure_dirs()
    path = _subresource_path(entity_type, entity_id, resource)
    if path.exists():
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    if fetch_fn is not None:
        data = fetch_fn(entity_id)
        if data is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            mark_entity_meta(entity_type, entity_id, fetched=True)
            return data
    return None


_CATEGORIAS_CACHE = None


def _load_categorias_lookup():
    global _CATEGORIAS_CACHE
    if _CATEGORIAS_CACHE is not None:
        return _CATEGORIAS_CACHE
    categorias_file = DATA_DIR / "categorias.json"
    lookup = {}
    if categorias_file.exists():
        with categorias_file.open(encoding="utf-8") as f:
            for cat in json.load(f):
                cat_id = cat.get("idModalitat")
                if cat_id is not None:
                    lookup[int(cat_id)] = cat
    _CATEGORIAS_CACHE = lookup
    return lookup


def _build_modalitat_entry(categoria_id):
    lookup = _load_categorias_lookup()
    cat = lookup.get(int(categoria_id))
    if cat:
        agrupacio = cat.get("agrupacio", {"nom": ""})
        if not isinstance(agrupacio, dict):
            agrupacio = {"nom": str(agrupacio)}
        return {
            "idModalitat": str(categoria_id),
            "modalitat": {
                "idModalitat": str(cat.get("idModalitat", categoria_id)),
                "nom": cat.get("nom", ""),
                "agrupacio": agrupacio,
            },
        }
    return {
        "idModalitat": str(categoria_id),
        "modalitat": {
            "idModalitat": str(categoria_id),
            "nom": "",
            "agrupacio": {"nom": ""},
        },
    }


def enrich_socio_modalitats(socio):
    """Repair incomplete modalitat stubs using data/categorias.json."""
    modalitats = socio.get("colegiatHasModalitats")
    if not isinstance(modalitats, list):
        return socio
    for index, item in enumerate(modalitats):
        if not isinstance(item, dict):
            continue
        categoria_id = item.get("idModalitat")
        if categoria_id is None:
            continue
        modalitat = item.get("modalitat", {})
        needs_repair = (
            not isinstance(modalitat, dict)
            or "agrupacio" not in modalitat
            or not modalitat.get("nom")
        )
        if needs_repair:
            modalitats[index] = _build_modalitat_entry(categoria_id)
    return socio


def entity_hash(entity_type, data):
    if entity_type == "colegiat":
        payload = {
            "idColegiat": data.get("idColegiat"),
            "colegiatHasModalitats": data.get("colegiatHasModalitats", []),
            "campsDinamics": data.get("campsDinamics", {}),
            "estat": data.get("estat"),
            "estatColegiat": data.get("estatColegiat"),
        }
    else:
        payload = data
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def patch_addcategoria(socio_id, categoria, extra=None):
    socio = read_entity("colegiat", socio_id) or {"idColegiat": socio_id}
    modalitats = socio.setdefault("colegiatHasModalitats", [])
    existing = {int(item.get("idModalitat", 0)) for item in modalitats}
    if int(categoria) not in existing:
        modalitats.append(_build_modalitat_entry(categoria))
    save_entity("colegiat", socio_id, socio, dirty=True)


def patch_delcategoria(socio_id, categoria):
    socio = read_entity("colegiat", socio_id)
    if not socio:
        return
    modalitats = socio.get("colegiatHasModalitats", [])
    socio["colegiatHasModalitats"] = [
        item for item in modalitats if int(item.get("idModalitat", 0)) != int(categoria)
    ]
    save_entity("colegiat", socio_id, socio, dirty=True)


def patch_escribecampo(socio_id, campo, valor):
    socio = read_entity("colegiat", socio_id) or {"idColegiat": socio_id}
    camps = socio.setdefault("campsDinamics", {})
    if not isinstance(camps, dict):
        camps = {}
        socio["campsDinamics"] = camps
    if valor:
        camps[campo] = valor
    elif campo in camps:
        del camps[campo]
    save_entity("colegiat", socio_id, socio, dirty=True)


def _patch_inscripcion_status(id_activitat, inscripcion_id, status):
    if not id_activitat:
        return
    path = DATA_DIR / f"{id_activitat}.json"
    if not path.exists():
        return
    with path.open(encoding="utf-8") as f:
        inscripciones = json.load(f)
    for item in inscripciones:
        if str(item.get("idInscripcio")) == str(inscripcion_id):
            item["estat"] = status
    with path.open("w", encoding="utf-8") as f:
        json.dump(inscripciones, f, ensure_ascii=False, indent=4)


def _patch_delete_inscripcion(id_activitat, inscripcion_id):
    if not id_activitat:
        return
    path = DATA_DIR / f"{id_activitat}.json"
    if not path.exists():
        return
    with path.open(encoding="utf-8") as f:
        inscripciones = json.load(f)
    inscripciones = [
        item
        for item in inscripciones
        if str(item.get("idInscripcio")) != str(inscripcion_id)
    ]
    with path.open("w", encoding="utf-8") as f:
        json.dump(inscripciones, f, ensure_ascii=False, indent=4)


def apply_patch(op, entity, entity_id, payload):
    if op == "addcategoria":
        patch_addcategoria(entity_id, payload["categoria"], payload.get("extra"))
    elif op == "delcategoria":
        patch_delcategoria(entity_id, payload["categoria"])
    elif op == "escribecampo":
        patch_escribecampo(entity_id, payload["campo"], payload.get("valor", ""))
    elif op == "anula_inscripcio":
        _patch_inscripcion_status(
            payload.get("idActivitat"), payload["inscripcion"], "anulada"
        )
    elif op == "delete_inscripcio":
        _patch_delete_inscripcion(payload.get("idActivitat"), payload["inscripcion"])
    elif op == "enviacomunicado":
        # Comunicados don't modify local state, skip patch
        pass


def split_entities_from_snapshot(entity_type, records, id_field, show_progress=True):
    total = len(records)
    saved = 0
    meta = read_meta()
    progress_every = max(1, total // 20)

    if show_progress and total:
        print(f"Saving {entity_type} cache (0/{total})...", flush=True)

    for index, record in enumerate(records, 1):
        entity_id = record.get(id_field)
        if entity_id is not None:
            save_entity(
                entity_type,
                entity_id,
                record,
                skip_snapshot=True,
                skip_meta=True,
            )
            key = _entity_key(entity_type, entity_id)
            entry = {
                "last_fetched_at": _utcnow(),
                "dirty": False,
            }
            if entity_type == "colegiat":
                entry["hash"] = entity_hash(entity_type, record)
            meta.setdefault("entities", {})[key] = entry
            saved += 1

        if show_progress and (
            index == 1 or index == total or index % progress_every == 0
        ):
            _print_progress(f"Saving {entity_type} cache", index, total)

    write_meta(meta)
    if show_progress:
        print(f"Saved {saved} {entity_type} entities to cache", flush=True)
    return saved


def pull_entities(
    apiurl,
    token,
    headers,
    auth_cls,
    entity_type="colegiat",
    page_size=100,
    show_progress=True,
):
    meta = read_meta()
    page = 0
    changed = 0
    processed = 0

    if show_progress:
        print(f"Pulling {entity_type} changes from API...", flush=True)

    while True:
        url = f"{apiurl}/colegiats?page={page}&pageSize={page_size}"
        response = requests.get(url, auth=auth_cls(token), headers=headers, timeout=30)
        batch = response.json()
        if not batch:
            break

        if show_progress:
            print(f"Pulling page {page + 1} ({len(batch)} records)...", flush=True)

        for socio in batch:
            processed += 1
            socio_id = socio["idColegiat"]
            key = _entity_key(entity_type, socio_id)
            old_hash = meta.get("entities", {}).get(key, {}).get("hash")
            new_hash = entity_hash(entity_type, socio)
            if old_hash != new_hash:
                save_entity(
                    entity_type,
                    socio_id,
                    socio,
                    skip_snapshot=True,
                    skip_meta=True,
                )
                meta.setdefault("entities", {}).setdefault(key, {})["hash"] = new_hash
                meta["entities"][key]["last_fetched_at"] = _utcnow()
                meta["entities"][key]["dirty"] = False
                changed += 1
                if show_progress:
                    print(
                        f"  updated {entity_type} {socio_id} "
                        f"({changed} changed, {processed} checked)",
                        flush=True,
                    )

        if len(batch) < page_size:
            break
        page += 1

    meta["last_pull"] = _utcnow()
    write_meta(meta)
    if show_progress:
        print(
            f"Pull complete: {changed} updated, {processed} checked",
            flush=True,
        )
    return changed


def evict_stale_entities(max_age_days=30):
    meta = read_meta()
    now = datetime.now(timezone.utc)
    removed = 0
    for key, entry in list(meta.get("entities", {}).items()):
        if entry.get("dirty"):
            continue
        fetched_at = entry.get("last_fetched_at")
        if not fetched_at:
            continue
        fetched = datetime.fromisoformat(fetched_at)
        if (now - fetched).days < max_age_days:
            continue
        entity_type, entity_id = key.split(":", 1)
        path = _entity_path(entity_type, entity_id)
        if path.exists():
            path.unlink()
            removed += 1
        del meta["entities"][key]
    write_meta(meta)
    return removed
