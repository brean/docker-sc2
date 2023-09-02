#!/bin/bash
# start without docker using wine.
#declare -x SC2PF=WineLinux
# Or a wine binary from lutris:
# WINE=/home/burny/.local/share/lutris/runners/wine/lutris-4.20-x86_64/bin/wine64
# Default Lutris StarCraftII Installation path:
#declare -x SC2PATH="/home/andreas/.wine/drive_c/Program Files (x86)/StarCraft II/Replays"
declare -x SC2PATH="/home/andreas/Games/StarCraftII/"
declare -x MAP="AbyssalReefLE"
echo $SC2PATH
python3 bot/cannon_rush.py