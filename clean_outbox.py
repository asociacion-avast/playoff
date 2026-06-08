#!/usr/bin/env python
"""Clean stale or invalid mutations from the outbox."""

import common

print("Analyzing outbox for stale mutations...")

socios = common.readjson("socios")
socio_ids = {s.get("id") for s in socios}

entries = common.sync_store.read_outbox()
print(f"Total entries: {len(entries)}")

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
        if socio_id and socio_id not in socio_ids:
            stale_entries.append(entry)
            continue

    # Valid mutation
    valid_entries.append(entry)

print(f"Valid entries: {len(valid_entries)}")
print(f"Stale entries: {len(stale_entries)} (socio doesn't exist)")

if stale_entries:
    print("\nStale mutations to be removed:")
    stale_by_socio = {}
    for e in stale_entries:
        socio_id = e.get("payload", {}).get("socio")
        if socio_id not in stale_by_socio:
            stale_by_socio[socio_id] = []
        stale_by_socio[socio_id].append(e.get("op"))

    for socio_id, ops in sorted(stale_by_socio.items()):
        print(f"  Socio {socio_id}: {len(ops)} operations ({', '.join(set(ops))})")

    # Ask for confirmation
    response = input("\nRemove these stale entries? (yes/no): ")
    if response.lower() in ["yes", "y"]:
        common.sync_store.write_outbox(valid_entries)
        print(f"\n✓ Outbox cleaned! Removed {len(stale_entries)} stale entries.")
        print(f"  Remaining: {len(valid_entries)} entries")
    else:
        print("\nCancelled - no changes made")
else:
    print("\n✓ No stale entries found")
