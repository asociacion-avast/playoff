#!/usr/bin/env python

"""Sync CLI: push pending mutations, pull remote changes, inspect outbox."""

import argparse
import configparser
import os
import subprocess
from datetime import datetime

import common
import sync_store


def _get_rw_token():
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~/.avast.ini"))
    return common.gettoken(
        user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
    )


def cmd_status(_args):
    """Show comprehensive sync status."""
    print("=" * 60)
    print("PLAYOFF DATA SYNC STATUS")
    print("=" * 60)

    # Cache freshness
    data_dir = "data"
    cache_files = {
        "socios.json": "Members (socios)",
        "actividades.json": "Activities (actividades)",
        "categorias.json": "Categories",
    }

    print("\n📁 LOCAL CACHE:")
    for filename, description in cache_files.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            mtime = os.path.getmtime(filepath)
            age = datetime.now() - datetime.fromtimestamp(mtime)
            age_str = f"{int(age.total_seconds() / 3600)}h {int((age.total_seconds() % 3600) / 60)}m ago"
            print(f"  ✓ {description}: {age_str}")
        else:
            print(f"  ✗ {description}: NOT FOUND")

    # Outbox status
    print("\n📤 OUTBOX:")
    counts = sync_store.outbox_counts()
    entries = sync_store.read_outbox()

    pending = counts.get("pending", 0)
    failed = counts.get("failed", 0)
    synced = counts.get("synced", 0)

    if not entries:
        print("  ✓ Empty - all mutations synced")
    else:
        print(f"  Total: {len(entries)}")
        if synced:
            print(f"  ✓ Synced: {synced}")
        if pending:
            print(f"  ⏳ Pending: {pending}")
        if failed:
            print(f"  ⚠ Failed: {failed}")

    # Entity cache
    meta = sync_store.read_meta()
    cached_entities = len(meta.get("entities", {}))
    if cached_entities:
        print(f"\n📦 ENTITY CACHE: {cached_entities} entities")
        last_pull = meta.get("last_pull")
        if last_pull:
            print(f"  Last pull: {last_pull}")

    # Connectivity
    online = common.is_online()
    print(f"\n🌐 CONNECTIVITY: {'✓ Online' if online else '✗ Offline'}")

    # Recommendations
    if pending and online:
        print("\n💡 RECOMMENDATIONS:")
        print("  • Flush pending mutations: ./sync.py push")
    if failed and online:
        if not pending:
            print("\n💡 RECOMMENDATIONS:")
        print("  • Clean stale mutations: ./sync.py clean")
        print("  • Or retry failed: ./sync.py retry-failed")

    print("=" * 60 + "\n")


def cmd_push(_args):
    token = _get_rw_token()
    results = common.flush_outbox(token)
    print(f"Synced: {results['synced']}, failed: {results['failed']}")


def cmd_retry_failed(_args):
    entries = sync_store.read_outbox()
    reset = 0
    for entry in entries:
        if entry.get("status") == "failed":
            entry["status"] = "pending"
            reset += 1
    sync_store.write_outbox(entries)
    print(f"Reset {reset} failed entries to pending")
    if reset:
        cmd_push(_args)


def cmd_pull(_args):
    token = common.gettoken()
    changed = sync_store.pull_entities(
        common.apiurl, token, common.headers, common.BearerAuth
    )
    print(f"Updated {changed} colegiat entities")


def cmd_evict(args):
    removed = sync_store.evict_stale_entities(max_age_days=args.days)
    print(f"Evicted {removed} stale entities")


def cmd_clean(args):
    """Clean stale mutations from outbox."""
    print("Analyzing outbox for stale mutations...")

    socios = common.readjson("socios")
    socio_ids = {s.get("id") for s in socios}

    entries = sync_store.read_outbox()
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

    print(f"Valid: {len(valid_entries)}, Stale: {len(stale_entries)}")

    if stale_entries:
        print("\nStale mutations (socio doesn't exist):")
        stale_by_socio = {}
        for e in stale_entries:
            socio_id = e.get("payload", {}).get("socio")
            if socio_id not in stale_by_socio:
                stale_by_socio[socio_id] = []
            stale_by_socio[socio_id].append(e.get("op"))

        for socio_id, ops in sorted(stale_by_socio.items()):
            print(f"  Socio {socio_id}: {len(ops)} ops ({', '.join(set(ops))})")

        if args.yes or input("\nRemove stale entries? (yes/no): ").lower() in [
            "yes",
            "y",
        ]:
            sync_store.write_outbox(valid_entries)
            print(f"\n✓ Removed {len(stale_entries)} stale entries")
            print(f"  Remaining: {len(valid_entries)}")
        else:
            print("\nCancelled")
    else:
        print("✓ No stale entries found")


def cmd_check(_args):
    """Detailed outbox inspection."""
    entries = sync_store.read_outbox()
    if not entries:
        print("Outbox is empty")
        return

    print(f"Outbox entries: {len(entries)}\n")

    # Group by status
    by_status = {}
    for e in entries:
        status = e.get("status", "unknown")
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(e)

    for status, status_entries in sorted(by_status.items()):
        print(f"=== {status.upper()} ({len(status_entries)}) ===")

        # Group by operation
        by_op = {}
        for e in status_entries:
            op = e.get("op", "unknown")
            if op not in by_op:
                by_op[op] = []
            by_op[op].append(e)

        for op, op_entries in sorted(by_op.items()):
            print(f"  {op}: {len(op_entries)}")

        # Show details for failed
        if status == "failed" and status_entries:
            print("\n  Sample errors:")
            for i, e in enumerate(status_entries[:3]):
                socio = e.get("payload", {}).get("socio", "?")
                error = e.get("last_error", "no error")[:100]
                print(f"    {i + 1}. {e.get('op')} socio={socio}")
                print(f"       {error}")
        print()


def cmd_download(_args):
    """Download fresh data from Playoff API."""
    print("Downloading fresh data from Playoff API...\n")

    scripts = ["./0-soci.py", "./0-categorias.py", "./1-activi.py"]

    for script in scripts:
        if not os.path.exists(script):
            print(f"⚠ {script} not found, skipping")
            continue

        print(f"Running {script}...")
        result = subprocess.run([script], capture_output=True, text=True)

        if result.returncode != 0:
            print("  ✗ Failed")
            if result.stderr:
                print(f"    {result.stderr[:200]}")
        else:
            # Show last line of output (usually has count)
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                if lines:
                    print(f"  ✓ {lines[-1]}")

    print("\n✓ Download complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Playoff offline sync utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./sync.py status                 Show sync status (cache, outbox, connectivity)
  ./sync.py download               Download fresh data from Playoff API
  ./sync.py push                   Upload pending mutations to API
  ./sync.py clean --yes            Remove stale mutations (auto-confirm)
  ./sync.py check                  Detailed outbox inspection
  ./sync.py retry-failed           Retry failed mutations
  ./sync.py pull                   Pull changed member entities from API
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show sync and outbox status").set_defaults(
        func=cmd_status
    )
    sub.add_parser("download", help="Download fresh data from API").set_defaults(
        func=cmd_download
    )
    sub.add_parser("push", help="Flush pending mutations to API").set_defaults(
        func=cmd_push
    )
    clean_parser = sub.add_parser("clean", help="Remove stale mutations from outbox")
    clean_parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirm")
    clean_parser.set_defaults(func=cmd_clean)

    sub.add_parser("check", help="Detailed outbox inspection").set_defaults(
        func=cmd_check
    )
    sub.add_parser("retry-failed", help="Retry failed outbox entries").set_defaults(
        func=cmd_retry_failed
    )
    sub.add_parser("pull", help="Pull changed colegiats from API").set_defaults(
        func=cmd_pull
    )
    evict = sub.add_parser("evict", help="Remove stale entity cache files")
    evict.add_argument("--days", type=int, default=30)
    evict.set_defaults(func=cmd_evict)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
