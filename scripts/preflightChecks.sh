#!/bin/sh
. scripts/config.sh

attempts=0
until $(curl --output /dev/null --silent --head --fail $basepath); do
    if [ ${attempts} -eq 20 ];then
      echo "Max attempts reached"
      exit 1
    fi

    printf '.'
    attempts=$(($attempts+1))
    sleep 9
done