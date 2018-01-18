#!/usr/bin/env bash
#docker pull blang/latex &
sleep 30 &
BPID=$!
i=0
while :; do
    if jobs %% >/dev/null; then
        echo -e ".\c"
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
