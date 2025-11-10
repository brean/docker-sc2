#!/bin/bash
# we need to run the environment graphically.
declare -x MAP="AbyssalReefLE"
declare -x SC_PATH="$HOME/Games/StarCraftII/"
declare -x SC2_DOCUMENTS="$HOME/Documents/StarCraftII"
docker compose run sc2bot
#docker compose --project-name bot2 run sc2bot &
#docker compose --project-name bot3 run sc2bot &
docker compose kill sc2bot
docker compose down
