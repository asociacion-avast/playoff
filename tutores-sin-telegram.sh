#!/usr/bin/env bash
for socio in $(./3-listado-socios-sin-id.py | grep '=' | cut -d "=" -f 2- | xargs echo); do ./4-sendupdate-telegram-tutor.py $socio; done
