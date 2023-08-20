#!/bin/sh

[ -z "$1" ] && T=$(date +"%d.%m.%Y-%H:%M:%S") || T=$1

alembic revision --autogenerate -m "$T"
