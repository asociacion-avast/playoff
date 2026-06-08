#!/usr/bin/env python
"""Sync pending mutations in outbox with Playoff API."""

import configparser
import os

import common

# Read configuration
config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))

# Get RW token for mutations
token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

print("Checking outbox...")
entries = common.sync_store.read_outbox()
print(f"Total entries: {len(entries)}")

pending = [e for e in entries if e.get("status") != "completed"]
print(f"Pending entries: {len(pending)}")

if not pending:
    print("✓ Outbox is clean, nothing to sync")
    exit(0)

# Show breakdown by operation type
ops = {}
for e in pending:
    op = e.get("op", "unknown")
    ops[op] = ops.get(op, 0) + 1

print("\nPending operations:")
for op, count in sorted(ops.items()):
    print(f"  {op}: {count}")

print("\nFlushing outbox...")
result = common.flush_outbox(token)

print("\n✓ Sync complete!")
print(f"  Processed: {result.get('processed', 0)}")
print(f"  Succeeded: {result.get('succeeded', 0)}")
print(f"  Failed: {result.get('failed', 0)}")

if result.get("failed", 0) > 0:
    print("\nFailed mutations remain in outbox. Check errors with:")
    print("  ./check_outbox.py")
