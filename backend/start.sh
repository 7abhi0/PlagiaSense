#!/usr/bin/env bash
set -e

exec gunicorn --bind "0.0.0.0:${PORT:-10000}" wsgi:app
