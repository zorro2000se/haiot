#!/usr/bin/env bash
#echo Enter mem[Enter] to run db in memory. Default is from disk
#read -t 3 answer
#if [ $? == 0 ]; then
#    echo "Selected"
#else
#    echo "Can't wait anymore!"
#answer=disk
#fi
#echo "Your answer is: $answer"

function run_app {
    scripts/stopserver.sh
    source venv/bin/activate
    python run_all.py $1
    exit_code=$?
    echo "Program exit with code $exit_code"
    echo "---------------------------------"
}

must_run=true
while $must_run; do
    run_app $1
    if [ $exit_code == 131 ]; then
        echo "Restarting app"
    fi
    if [ $exit_code == 132 ]; then
        echo "Upgrading app"
        git pull --no-edit
    fi
    if [ $exit_code == 133 ]; then
        echo "Shutdown app"
        must_run=false
    fi
    if [ $exit_code == 143 ]; then
        echo "App was killed"
        must_run=false
    fi
    if [ $exit_code == 137 ]; then
        echo "App was killed with -9"
        must_run=false
    fi
    if [ $exit_code == 1 ]; then
        echo "App was interrupted with CTRL-C"
        must_run=false
    fi
done