#!/usr/bin/env bash
# usage: bash run-sql.sh 02_stream_raw.sql
cd "$(dirname "$0")"
MSYS_NO_PATHCONV=1 docker compose -f infra/docker-compose.yml exec -T jobmanager \
  ./bin/sql-client.sh -i /opt/sql/00_init.sql -f "/opt/sql/$1"