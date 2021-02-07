# we need to run the environment graphically.
xhost +local:root
docker-compose run sc2bot
docker-compose down
xhost -local:root