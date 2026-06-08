#!/usr/bin/env python
"""Diagnose socios that are in entity cache but missing from socios.json."""

import json
import os

import sync_store

print("Diagnosing missing socios...\n")

# Load socios.json
with open("data/socios.json") as f:
    socios_data = json.load(f)

ids_in_json = {s.get("idColegiat") for s in socios_data if s.get("idColegiat")}
print(f"Socios in socios.json: {len(ids_in_json)}")

# Get entity cache IDs
entity_dir = "data/entities/colegiat"
entity_files = [
    f
    for f in os.listdir(entity_dir)
    if f.endswith(".json") and "sync-conflict" not in f
]
entity_ids = {int(f.replace(".json", "")) for f in entity_files}
print(f"Entities in cache: {len(entity_ids)}")

# Find discrepancies
in_cache_not_json = entity_ids - ids_in_json
in_json_not_cache = ids_in_json - entity_ids

print(f"\nIn entity cache but NOT in socios.json: {len(in_cache_not_json)}")
if in_cache_not_json:
    print(f"  IDs: {sorted(list(in_cache_not_json))}")

    # Check their status
    print("\n  Checking status of missing socios:")
    for socio_id in sorted(list(in_cache_not_json))[:10]:
        entity = sync_store.read_entity("colegiat", socio_id, fetch_fn=None)
        if entity:
            status = entity.get("estatColegiat", {}).get("nom", "?")
            name = entity.get("persona", {}).get("nomCognom1", "?")
            print(f"    {socio_id}: {status} - {name}")

print(f"\nIn socios.json but NOT in entity cache: {len(in_json_not_cache)}")
if in_json_not_cache:
    print(f"  Sample IDs: {sorted(list(in_json_not_cache))[:20]}")

# Check outbox for these missing socios
print("\nChecking outbox for missing socios...")
entries = sync_store.read_outbox()
missing_socio_mutations = []

for entry in entries:
    socio_id = entry.get("payload", {}).get("socio")
    if socio_id and socio_id in in_cache_not_json:
        missing_socio_mutations.append(entry)

if missing_socio_mutations:
    print(f"  ⚠️ Found {len(missing_socio_mutations)} mutations for missing socios!")
    for e in missing_socio_mutations[:5]:
        socio = e.get("payload", {}).get("socio")
        op = e.get("op")
        status = e.get("status")
        print(f"    {op} for socio {socio}: {status}")
else:
    print("  ✓ No mutations for missing socios in outbox")

print("\n" + "=" * 60)
print("RECOMMENDATION:")
if in_cache_not_json:
    print(
        f"  Re-download socios.json to include the {len(in_cache_not_json)} missing socios"
    )
    print("  Run: ./sync.py download")
