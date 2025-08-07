# attach to the ubuntu container
CONTAINER_NAME=eda_docker_ubuntu_container
if docker ps --filter "name=${CONTAINER_NAME}" --filter "status=running" | grep -G "${CONTAINER_NAME}" >> /dev/null; then
    docker exec -it ${CONTAINER_NAME} /usr/bin/fish
elif docker ps -a --filter "name=${CONTAINER_NAME}" --filter "status=exited" | grep -G "${CONTAINER_NAME}" >> /dev/null; then
    docker start ${CONTAINER_NAME}; docker exec -it ${CONTAINER_NAME} /usr/bin/fish
else
    print "Error!"
    exit 1
fi
