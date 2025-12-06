# specify base image as official ubuntu image
FROM ubuntu:24.04

ARG USER_NAME=aislab

# basic setup
ARG BASIC="fish sudo git vim build-essential curl wget tar unzip make openssh-client \
  gtkwave x11-utils x11-apps man-db python3 python3-pip \
  clangd clang-format software-properties-common valgrind unminimize feh sxiv \
  cmake meson"
ENV TZ="Asia/Taipei"
RUN sed -i "s/archive.ubuntu.com/mirror.twds.com.tw/g" /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get update \
    && apt-get install --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt-get install -y ${BASIC} \
    && yes | unminimize \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
# && apt-add-repository ppa:maveonair/helix-editor && apt-get update && apt-get install -y helix \

# user and workdir setup
RUN groupmod -n $USER_NAME ubuntu \
    && usermod -l $USER_NAME -d /home/$USER_NAME -m ubuntu \
    && echo "$USER_NAME:1234" | chpasswd \
    && mkdir /home/$USER_NAME/workspace \
    && chown -R $USER_NAME:$USER_NAME /home/$USER_NAME/workspace
USER $USER_NAME
WORKDIR /home/$USER_NAME/workspace
VOLUME /home/$USER_NAME/workspace

# Install pre-commit framework for Git pre-commit hooks
RUN pip install --user --break-system-package pre-commit
ENV PATH=/home/$USER_NAME/.local/bin:$PATH

# copy some files from the host
RUN mkdir -p /home/$USER_NAME/.ssh
COPY --chown=$USER_NAME:$USER_NAME $PWD/../secrets/id_ed25519 /home/$USER_NAME/.ssh/id_ed25519
COPY ubuntu/ssh_config /home/$USER_NAME/.ssh/config
RUN chmod 600 /home/$USER_NAME/.ssh/id_ed25519

# prepare wrapper scripts for running EDA tools in Rocky side
COPY script/eda_proxy.py /usr/local/bin/eda_proxy.py
COPY script/eda_config.toml /usr/local/bin/eda_config.toml
COPY script/setup_symlinks.py /usr/local/bin/setup_symlinks.py
# RUN chmod +x /usr/local/bin/eda_proxy.py && \
#     chmod +x /usr/local/bin/setup_links.py && \
#     python3 /usr/local/bin/setup_links.py

# container entrypoint
ENTRYPOINT [ "sleep", "infinity" ]
