#!/usr/bin/env python
"""Check sync status between local cache and Playoff API."""

import os
from datetime import datetime

import common

print("=" * 60)
print("PLAYOFF DATA SYNC STATUS")
print("=" * 60)

# Check cache freshness
data_dir = "data"
cache_files = {
    "socios.json": "Members (socios)",
    "actividades.json": "Activities (actividades)",
    "categorias.json": "Categories",
}

print("\n📁 LOCAL CACHE STATUS:")
for filename, description in cache_files.items():
    filepath = os.path.join(data_dir, filename)
    if os.path.exists(filepath):
        mtime = os.path.getmtime(filepath)
        age = datetime.now() - datetime.fromtimestamp(mtime)
        age_str = f"{int(age.total_seconds() / 3600)}h {int((age.total_seconds() % 3600) / 60)}m ago"
        print(f"  ✓ {description}: {age_str}")
    else:
        print(f"  ✗ {description}: NOT FOUND")

# Check outbox
print("\n📤 OUTBOX (Pending Mutations):")
try:
    entries = common.sync_store.read_outbox()
    if not entries:
        print("  ✓ Empty - all mutations synced")
    else:
        statuses = {}
        ops = {}
        for e in entries:
            status = e.get("status", "unknown")
            op = e.get("op", "unknown")
            statuses[status] = statuses.get(status, 0) + 1
            ops[op] = ops.get(op, 0) + 1

        print(f"  Total entries: {len(entries)}")
        print("\n  By status:")
        for status, count in sorted(statuses.items()):
            icon = "✓" if status == "synced" else "⚠" if status == "failed" else "⏳"
            print(f"    {icon} {status}: {count}")

        print("\n  By operation:")
        for op, count in sorted(ops.items()):
            print(f"    - {op}: {count}")

        # Show failed entry sample
        failed = [e for e in entries if e.get("status") == "failed"]
        if failed:
            print(f"\n  ⚠ {len(failed)} failed mutations need attention")
            print("    Sample error:", failed[0].get("last_error", "no error")[:80])

except FileNotFoundError:
    print("  ✓ No outbox file (no pending mutations)")

# Check connectivity
print("\n🌐 CONNECTIVITY:")
if common.is_online():
    print("  ✓ Online - can sync with Playoff API")
else:
    print("  ✗ Offline - mutations queued for later sync")

print("\n" + "=" * 60)
print("\nRECOMMENDATIONS:")

# Recommendations based on status
try:
    entries = common.sync_store.read_outbox()
    failed = [e for e in entries if e.get("status") == "failed"]
    pending = [e for e in entries if e.get("status") == "pending"]

    if failed and common.is_online():
        print("  • Retry failed mutations: manually investigate errors")
        print("    Some operations may need to be re-queued or cancelled")
    if pending and common.is_online():
        print("  • Flush pending mutations: ./sync_outbox.py")
except FileNotFoundError:
    pass

# Check cache age
for filename in cache_files.keys():
    filepath = os.path.join(data_dir, filename)
    if os.path.exists(filepath):
        mtime = os.path.getmtime(filepath)
        age_hours = (
            datetime.now() - datetime.fromtimestamp(mtime)
        ).total_seconds() / 3600
        if age_hours > 24:
            print(f"  • Refresh {filename}: last updated {int(age_hours)}h ago")
            print("    Run: ./0-soci.py (or relevant download script)")
            break

print()
