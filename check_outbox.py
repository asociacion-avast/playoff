#!/usr/bin/env python3

import common

try:
    entries = common.sync_store.read_outbox()
    print(f"Outbox entries: {len(entries)}")

    failed = [
        e
        for e in entries
        if e.get("op") == "enviacomunicado" and e.get("status") == "failed"
    ]
    print(f"Failed comunicados: {len(failed)}")

    for e in failed[:5]:
        dest = e.get("payload", {}).get("data", {}).get("destinataris", "unknown")
        error = e.get("last_error", "no error")[:100]
        print(f"  - Destinatario: {dest}, Error: {error}")

except FileNotFoundError:
    print("No outbox file found")
