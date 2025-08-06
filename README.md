# Completely Isolated Development Environment with Docker Compose

## Introduction

This is a workaround about how to build a completely isolated development environment for the scenario that you need both complicated software toolchain and EDA tools for digital IC design.

In this solution, it use Docker Compose to build two containers, and one bases on Ubuntu image, while the other one bases on Rocky Linux image.
The two containers can communicate with each other via internal docker network and ssh.

More precisely, the suggested usage is that you use `docker exec -it <container_name> fish` to attach to the fish shell of ubuntu container to use the SW toolchains you need, then you can use `ssh eda` with password `1234` to connect to the rocky container to use EDA tools.

## About X11 Forwarding and GUI Applications

To make the X11 Forwarding work successfully, you have to copy the *xauth* information from the host (on the server, the word "host" is relative to the container) inside the rocky container. Please follows these instructions:

```shell
# on the host side (before attaching to ubuntu container)
$ xauth list $DISPLAY # plaese copy the content it prints

# after attacing to ubuntu container
$ ssh eda # enter rocky container via ssh
$ xauth # use it to enter the interactive CLI of xauth
# then type `add <the content you just copy>` inside the xauth interactive CLI interface
```
