#!/usr/bin/env bash

set -e
REQ="requirements.txt"

if [[ -f "$REQ" ]]; then
	echo "requestss" >> "$REQ"
fi

pip install -r "$REQ"
