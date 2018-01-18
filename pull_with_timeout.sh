#!/usr/bin/env bash
docker pull blang/latex &
BPID=$!
i=0
while True; do
    if ps -p $BPID >&-; then
        echo ".\c"
        sleep 5
        ((i+=5))

        if (( i > 1200 )); then
            echo " TIMEOUT!"
            exit 1
        fi
    else
        echo " done"
        break
    fi
done
