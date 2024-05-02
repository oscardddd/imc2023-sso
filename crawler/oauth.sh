#!/usr/bin/env bash
set -euo pipefail

# example usage:
#
#   bash oauth.sh 9999 https://www.grubhub.com
#
#
# parallel invocations (requires gnu parallel):
#
#   parallel -d "\r\n" -j3 --delay 2 --colsep ',' "bash oauth.sh {1} {2}" :::: <(head -1 top-1m.csv)
#   parallel -d "\r\n" -j3 --delay 2 --colsep ',' "bash oauth.sh {1} {2}" :::: <(head -1000 top-1m.csv)
#

# change into this script's directory
cd "$(dirname "${BASH_SOURCE[0]}")"

USER_DATA_DIR=$(mktemp -d "${TMPDIR:-/tmp}/playwright.XXXXXXXXX")

function cleanup {
    # cleanup on exit
    echo "[.] cleanup: removing ${USER_DATA_DIR}"
    rm -rf ${USER_DATA_DIR}
}
trap cleanup EXIT

# TODO() this should really be a parameter
TIMESTAMP_RUN=DEV
OUTPUT_DIR=output-${TIMESTAMP_RUN}
OUTPUT_LOG=log-${TIMESTAMP_RUN}.txt
mkdir -p ${OUTPUT_DIR}

declare -a OPTS=( )

OPTS+=(--timetolive 4000)
OPTS+=(--url $2)
OPTS+=(--outputprefix $1)
OPTS+=(--outputdir ${OUTPUT_DIR})
OPTS+=(--userdir ${USER_DATA_DIR})
#OPTS+=(--headless)
#OPTS+=(--debug)

node --unhandled-rejections=strict clicker.js "${OPTS[@]}" 2>&1 | tee -a ${OUTPUT_DIR}/$1-log.txt

