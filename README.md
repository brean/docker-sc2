# docker-sc2

Docker environment for StarCraft II bots.

## Installation
You need to download and extract SC2 as well as some maps, see [here](https://github.com/Blizzard/s2client-proto) for details.

Set the folder of your extracted "StarCraft II" folder to "SC_PATH" in your `.env`-file, you also need to set MAP.

Your .env-file could look like this:

```bash
SC_PATH=/home/user/StarCraftII
MAP=KingsCove
```

Note that map names match with the `.SC2Map`-file names but do not end with "LE".

You can run `run_bot.bash` file to start the bot (for now a simple cannon_rush-bot) inside docker compose, it will also start inside an xhost-environment.

## Note
For my convenience this also pulls the [Web-Server-SC2](https://github.com/brean/web-server-sc2) repository with the server there to visualize the games the bot has played. The Bot does not need this server and normally does not connect to it for a live view of a match.

## License
Distributed under the [3-clause BSD license](https://opensource.org/licenses/BSD-3-Clause).

## Maintainer

Andreas Bresser, self@andreasbresser.de

## Authors / Contributers

Authors and contributers are [listed on github](https://github.com/brean/docker-sc2/graphs/contributors).