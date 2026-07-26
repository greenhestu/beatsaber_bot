#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

export SS_MAPS_MAP_LIMIT="${SS_MAPS_MAP_LIMIT:-2000}"
export SS_MAPS_TOP_N="${SS_MAPS_TOP_N:-240}"
export SS_MAPS_RATE_PER_MIN="${SS_MAPS_RATE_PER_MIN:-180}"
export SS_MAPS_WORKERS="${SS_MAPS_WORKERS:-4}"

export SS_USERS_N_PLAYERS="${SS_USERS_N_PLAYERS:-3000}"
export SS_USERS_TOP_SCORES="${SS_USERS_TOP_SCORES:-100}"
export SS_USERS_RATE_PER_MIN="${SS_USERS_RATE_PER_MIN:-180}"
export SS_USERS_WORKERS="${SS_USERS_WORKERS:-4}"

echo "== ScoreSaber map catalog =="
(
  cd ss_maps
  python3 fetch.py catalog
)

echo "== ScoreSaber map user distributions =="
(
  cd ss_maps
  python3 fetch.py scores
)

echo "== ScoreSaber user top-pp scores =="
(
  cd ss_users
  python3 fetch.py
)

echo "== recommendation data fetch complete =="
