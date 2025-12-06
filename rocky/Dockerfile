# specify official Rocky Linux 9.3 image as base image
FROM rockylinux:9.3

# arguments
ARG USER_NAME=aislab

# install necessary packages for running EDA tools
RUN dnf update -y \
    && dnf install -y epel-release \
    && dnf install -y sudo openssh-server openssh-clients \
    ncurses ncurses-devel wget \
    xorg-x11-xauth xauth xterm \
    epel-release wget vim tar time csh ksh \
    graphite2 bc iputils telnet make cmake \
    gcc gcc-c++ glibc elfutils-libelf \
    libXrandr libGL libXcomposite libnsl pulseaudio-libs-devel \
    libXi libXp libXt \
    libX11 libXext libXrender libXtst \
    libXScrnSaver procps-ng \
    numactl-libs libxslt libXtst libXdamage nss \
    libxkbcommon-x11 libxkbcommon \
    libxcb xcb-util xcb-util-wm xcb-util-image xcb-util-keysyms \
    xcb-util-renderutil xcb-util-cursor \
    ncurses-compat-libs alsa-lib \
    tcl tcl-devel environment-modules \
    libmng libjpeg \
    && dnf clean all

# change timezone
ENV TZ=Asia/Taipei
RUN echo 'ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime'

# mount /cad for using EDA tools
RUN mkdir -p /cad/synopsys \
    && mkdir -p /cad/cadence \
    && mkdir -p /cad/CBDK \
    && ln -s /cad /usr/cad

# RUN ssh-keygen -q -t rsa -b 2048 -f /etc/ssh/ssh_host_rsa_key -N '' \
    # && ssh-keygen -q -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N '' \
    # && ssh-keygen -t dsa -f /etc/ssh/ssh_host_ed25519_key  -N '' \
# generate host ssh-keys for sshd, and make sshd to enable AcceptEnv DISPLAY
RUN ssh-keygen -A \
    && echo "AcceptEnv DISPLAY" | tee -a /etc/ssh/sshd_config \
    && sed -i 's/^#X11Forwarding yes/X11Forwarding yes/' /etc/ssh/sshd_config \
    && sed -i 's/^X11Forwarding no/X11Forwarding yes/' /etc/ssh/sshd_config \
    && sed -i 's/^#PubkeyAuthentication[[:space:]]\+yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# add a user "rocky" and give it proper uid/gid
RUN groupadd -g 1000 $USER_NAME \
    && useradd -d /home/$USER_NAME -s /usr/bin/tcsh -u 1000 -g $USER_NAME $USER_NAME \
    && sudo usermod -aG wheel $USER_NAME \
    && mkdir -p /home/$USER_NAME/workspace \
    && echo "$USER_NAME:1234" | chpasswd \
    && mkdir -p /home/$USER_NAME/.ssh \
    && chown $USER_NAME:$USER_NAME /home/$USER_NAME/.ssh \
    && chmod 700 /home/$USER_NAME/.ssh

# prepare shared ssh pubkey for ssh connection without password
COPY --chown=$USER_NAME:$USER_NAME secrets/id_ed25519.pub /home/$USER_NAME/.ssh/authorized_keys
RUN chmod 600 /home/$USER_NAME/.ssh/authorized_keys

# setup work directory and mount point
WORKDIR /home/$USER_NAME/workspace
VOLUME /home/$USER_NAME/workspace

# copy some files from local
COPY rocky/skeleton.tcshrc /home/$USER_NAME/.tcshrc

# set default shell to be tcsh
ENV SHELL /usr/bin/tcsh

# container entrypoint
EXPOSE 22
RUN mkdir -p /run/sshd
ENTRYPOINT [ "/usr/sbin/sshd", "-D", "-e", "-o", "ListenAddress=0.0.0.0" ]
