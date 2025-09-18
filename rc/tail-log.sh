#!/bin/bash

if [[ -z $EXPERIMENTS_PATH ]]; then
    EXPERIMENTS_PATH=~/experiments
fi

find-last-log()
{
    experiment_name=$1
    experiment_path=$EXPERIMENTS_PATH/$experiment_name
    if [ ! -e $experiment_path ]; then
        echo "Experiment $experiment_name does not exist" >&2
        exit 1
    fi

    last_log=$(ls -t $experiment_path/*.out | head -n 1)
    if [ "$last_log" == "" ]; then
        echo "Experiment $experiment_name has no logs" >&2
        exit 1
    fi
    echo $last_log
}


experiment_name=$1
if [[ -z $experiment_name ]]; then
    echo "⚠️ The experiment name is required"
    exit 1
fi

experiment_path=~/experiments/$experiment_name
if [[ ! -e $experiment_path ]]; then
    echo "❌ Experiment $experiment_name does not exist"
    exit 1
fi

last_log=$(find-last-log $experiment_name)
if [[ $? == 0 ]]; then
    tail -f $last_log
else
    echo "⚠️ Experiment $experiment_name did not produce any logs"
fi
