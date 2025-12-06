# attach to the ubuntu container
CONTAINER_NAME=eda_docker_ubuntu_container

# check DISPLAY
if [ -z "$DISPLAY" ]; then
    echo "Environment variable DISPLAY is not set!"
    exit 1
fi

# allow docker for X11 forwarding
xhost +local:docker

# attach to the ubuntu container
if docker ps --filter "name=${CONTAINER_NAME}" --filter "status=running" | grep -G "${CONTAINER_NAME}" >> /dev/null; then
    docker exec -e DISPLAY=$DISPLAY -it ${CONTAINER_NAME} /usr/bin/fish
elif docker ps -a --filter "name=${CONTAINER_NAME}" --filter "status=exited" | grep -G "${CONTAINER_NAME}" >> /dev/null; then
    docker start ${CONTAINER_NAME}; docker exec -e DISPLAY=$DISPLAY -it ${CONTAINER_NAME} /usr/bin/fish
else
    printf "Error!"
    exit 1
fi
