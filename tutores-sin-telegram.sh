#!/usr/bin/env bash
./3-listado-socios-sin-id.py | grep '=' | cut -d "=" -f 2- | xargs ./4-sendupdate-telegram-tutor.py
