#!/usr/bin/env python

"""Sync CLI: push pending mutations, pull remote changes, inspect outbox."""

import argparse
import configparser
import os

import common
import sync_store


def _get_rw_token():
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~/.avast.ini"))
    return common.gettoken(
        user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
    )


def cmd_status(_args):
    counts = sync_store.outbox_counts()
    meta = sync_store.read_meta()
    online = common.is_online()
    print(f"Online: {online}")
    print(f"Outbox pending: {counts.get('pending', 0)}")
    print(f"Outbox failed: {counts.get('failed', 0)}")
    print(f"Outbox synced: {counts.get('synced', 0)}")
    print(f"Cached entities: {len(meta.get('entities', {}))}")
    print(f"Last pull: {meta.get('last_pull')}")


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


def main():
    parser = argparse.ArgumentParser(description="Playoff offline sync")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show sync and outbox status").set_defaults(
        func=cmd_status
    )
    sub.add_parser("push", help="Flush pending mutations to API").set_defaults(
        func=cmd_push
    )
    sub.add_parser("retry-failed", help="Retry failed outbox entries").set_defaults(
        func=cmd_retry_failed
    )
    sub.add_parser("pull", help="Pull changed colegiats from API").set_defaults(
        func=cmd_pull
    )
    evict = sub.add_parser("evict", help="Remove stale clean entity cache files")
    evict.add_argument("--days", type=int, default=30)
    evict.set_defaults(func=cmd_evict)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
