# Completely Isolated Development Environment with Docker Compose

## Introduction

This is a workaround about how to build a completely isolated development environment for the scenario that you need both complicated software toolchain and EDA tools for digital IC design.

In this solution, it use Docker Compose to build two containers, and one bases on Ubuntu image, while the other one bases on Rocky Linux image.
The two containers can communicate with each other via internal docker network and ssh.

More precisely, the suggested usage is that you use `docker exec -it <container_name> fish` to attach to the fish shell of ubuntu container to use the SW toolchains you need, then you can use `ssh eda` with password `1234` to connect to the rocky container to use EDA tools.

The reason why it uses two container respectively is that ubuntu is more suitable for toolchain/package installation, while the EDA tools are supposed to run on RHEL/RockyLinux.

## About X11 Forwarding and GUI Applications

To make the X11 Forwarding work successfully, you have to copy the *xauth* information from the host (on the server, the word "host" is relative to the container) inside the rocky container. At the first time you create the containers (when you execute `docker compose up -d`), plaese follow these instructions:

```shell
# inside the ubuntu container
cd /home/aislab
cp .xauth/.xauth_temp .Xauthority

# and then login into rocky container via ssh
ssh eda
cd /home/aislab
cp .xauth/.xauth_temp .Xauthority
```

You only need to do this one time when creating the two containers, or when the content of .Xauthority on the server host is changed.
