#!/bin/sh
function error_exit
{
   echo "Error: ${1:-"Unknown Error"}" 1>&2
   exit 1 # This unfortunately also exits the terminal
}

. scripts/config.sh

echo "workloads"
for experiment in "${experiments[@]}"
do
   
   echo "running bechmakr b$experiment"
   worload="workloads/b${experiment}.yml"
   ./bin/doom --verbose --target $basepath --workload $worload --data $data
done

echo "experimentes compleat terminating"