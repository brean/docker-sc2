# docker-sc2

Docker environment for StarCraft II bots.

You need to download and extract SC2 as well as some maps, see [here](https://github.com/Blizzard/s2client-proto) for details.

Set the folder of your extracted "StarCraftII" folder to "SC_PATH" in your `.env`-file, you also need to set MAP.

Your .env-file could look like this:
```bash
SC_PATH=/home/user/StarCraftII
MAP=KingsCove
```
Note that map names match with the `.SC2Map`-file names but do not end with "LE".

You can run `start.bash` file to start docker-compose, it will also start inside an xhost-environment.
