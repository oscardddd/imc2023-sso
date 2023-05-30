#!/usr/bin/env bash
set -euo pipefail

underline=$(tput smul)
nounderline=$(tput rmul)
bold=$(tput bold)
normal=$(tput sgr0)

# like ./run.sh ./templates ~/Desktop/Logged-in\ Pages\ Data/*-1.png

print_usage() {
    echo -en "Usage: $0"
    echo -en " ${underline}template-dir${nounderline}"
    echo -en " ${underline}image-dir${nounderline}"
    echo -en "\n"
}

if [[ "$#" -lt 2 ]]; then
    print_usage
    exit 1
fi

for f in "${@:2}"; do
    echo $f
    python3 ./template-match.py $f $1
done