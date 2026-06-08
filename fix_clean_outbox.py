#!/usr/bin/env python
"""Fixed version of clean outbox - properly handles string/int ID comparison."""

import common
import sync_store

print("Cleaning stale mutations from outbox...")

socios = common.readjson("socios")
# Build set of IDs, handling both string and int
socio_ids = {
    int(s.get("idColegiat"))
    if isinstance(s.get("idColegiat"), (int, str))
    and str(s.get("idColegiat")).isdigit()
    else s.get("idColegiat")
    for s in socios
    if s.get("idColegiat")
}
# Also keep string versions
socio_ids_str = {str(s.get("idColegiat")) for s in socios if s.get("idColegiat")}
socio_ids = socio_ids | socio_ids_str

print(f"Socios in cache: {len(socios)}")
print(f"Unique socio IDs: {len(socio_ids)}")

entries = sync_store.read_outbox()
print(f"Total outbox entries: {len(entries)}")

# Separate valid from stale
valid_entries = []
stale_entries = []

for entry in entries:
    # Already synced? Keep it (for history)
    if entry.get("status") == "synced":
        valid_entries.append(entry)
        continue

    # Check if socio exists (for socio-related operations)
    op = entry.get("op")
    if op in ["addcategoria", "delcategoria", "escribecampo"]:
        socio_id = entry.get("payload", {}).get("socio")

        # Check both as-is and as int/str
        exists = (
            socio_id in socio_ids
            or str(socio_id) in socio_ids
            or (
                isinstance(socio_id, str)
                and socio_id.isdigit()
                and int(socio_id) in socio_ids
            )
        )

        if not exists:
            stale_entries.append(entry)
            continue

    # Valid mutation
    valid_entries.append(entry)

print(f"Valid entries: {len(valid_entries)}")
print(f"Stale entries: {len(stale_entries)}")

if stale_entries:
    print("\nStale mutations (socio doesn't exist):")
    for e in stale_entries[:10]:
        socio_id = e.get("payload", {}).get("socio")
        op = e.get("op")
        status = e.get("status")
        print(f"  {op} for socio {socio_id} ({status})")

    response = input("\nRemove stale entries? (yes/no): ")
    if response.lower() in ["yes", "y"]:
        sync_store.write_outbox(valid_entries)
        print(f"\n✓ Removed {len(stale_entries)} stale entries")
        print(f"  Remaining: {len(valid_entries)}")
    else:
        print("\nCancelled")
else:
    print("✓ No stale entries found")
