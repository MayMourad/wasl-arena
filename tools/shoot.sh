#!/usr/bin/env bash
# usage: tools/shoot.sh BASE_URL  -> docs/screenshots/*.png (real captures of the running app)
BASE=${1:-http://127.0.0.1:5173}
CH="/c/Program Files/Google/Chrome/Application/chrome.exe"
mkdir -p docs/screenshots
shot(){ "$CH" --headless=new --disable-gpu --use-angle=swiftshader --enable-unsafe-swiftshader --hide-scrollbars --window-size=1440,900 --virtual-time-budget=12000 --screenshot="$(cygpath -w "$PWD/docs/screenshots/$1.png")" "$BASE$2" >/dev/null 2>&1; echo "$1 $(stat -c %s docs/screenshots/$1.png 2>/dev/null)"; }
shot 01-launch "/"; shot 02-setup "/setup"; shot 03-library "/games"; shot 04-prepare "/prepare"; shot 05-arena "/arena"
shot 06-replay-football "/replay?report=sample-football_goal"; shot 07-replay-falaj "/replay?report=sample-falaj_valid"
shot 08-replay-souq "/replay?report=sample-souq_correct_gemini"; shot 09-replay-review "/replay?report=sample-football_uncertain"
shot 10-cup "/cup?demo=1"; shot 11-lab "/lab"
