# EDA with Docker

## Brief Introduction to The Architecture

## Introduction

![](eda-with-docker.png)

This is a workaround about how to build a completely isolated development environment for the scenario that you need both complicated software toolchain and EDA tools for digital IC design.

In this solution, it use Docker Compose to build two containers, and one bases on Ubuntu image, while the other one bases on Rocky Linux image.
The two containers can communicate with each other via internal docker network and ssh.

More precisely, the suggested usage is that you use `docker exec -it <container_name> fish` to attach to the fish shell of ubuntu container to use the SW toolchains you need, then you can use `ssh eda` with password `1234` to connect to the rocky container to use EDA tools.

The reason why it uses two container respectively is that ubuntu is more suitable for toolchain/package installation, while the EDA tools are supposed to run on RHEL/RockyLinux.

## How To Use EDA-with-Docker

### Generate SSH Keys on Host

IN order to make the ssh connection between Ubuntu container and Rocky container be without password, we must generate a pair of ssh key on the host before builing images.
During the building process of images, the public key will be copied into the Rocky container, and the private key will be copied into the Ubuntu container.

To generate a pair of ssh key, please execute the following commands:

```bash=
$ mkdir secrets
$ ssh-keygen -f ./secrets/id_ed25519 -N ''
```

### Build Images

The second step is to build both the Ubuntu image and the Rocky image with the given Dockerfile(s).

```bash=
$ docker compose build
```

### Start the Docker Compose

After building the two images, we can now start the docker compose.

```bash
$ docker compose up -d
```

### Attach to The Ubuntu Container with Fish Shell

```bash
$ ./attach.sh
```

## About GUI Applications inside Container

TBD

## How to Execute EDA Tools inside Ubuntu Container?

In order to make seamless execution flow for EDA tools, TBD
