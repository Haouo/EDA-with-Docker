# specify official Rocky Linux 9.3 image as base image
FROM rockylinux:9.3

# install necessary packages for running EDA tools
RUN dnf update -y \
    && dnf install -y epel-release \
    && dnf install -y sudo openssh-server openssh-clients \
    ncurses ncurses-devel \
    xorg-x11-xauth xauth xterm \
    epel-release wget vim tar time csh ksh \
    graphite2 bc iputils telnet make cmake \
    gcc g++ glibc elfutils-libelf \
    libXrandr libGL libXcomposite libnsl pulseaudio-libs-devel \
    libXi libXp libXt \
    libX11 libXext libXrender libXtst \
    libXScrnSaver procps-ng \
    numactl-libs libxslt libXtst libXdamage nss \
    libxkbcommon-x11 libxkbcommon \
    libxcb xcb-util xcb-util-wm xcb-util-image xcb-util-keysyms \
    xcb-util-renderutil xcb-util-cursor \
    ncurses-compat-libs alsa-lib \
    && dnf clean all

# change timezone
ENV TZ=Asia/Taipei
RUN echo 'ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime'

# mount /cad for using EDA tools
RUN mkdir -p /cad/synopsys \
    && mkdir -p /cad/cadence \
    && mkdir -p /cad/CBDK \
    && ln -s /cad /usr/cad

# generate host ssh-keys for sshd, and make sshd to enable AcceptEnv DISPLAY
RUN ssh-keygen -q -t rsa -b 2048 -f /etc/ssh/ssh_host_rsa_key -N '' \
    && ssh-keygen -q -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N '' \
    && ssh-keygen -t dsa -f /etc/ssh/ssh_host_ed25519_key  -N '' \
    && echo "AcceptEnv DISPLAY" | tee -a /etc/ssh/sshd_config

# add a user "rocky" and give it proper uid/gid
RUN groupadd -g 1000 aislab \
    && useradd -d /home/aislab -s /usr/bin/tcsh -u 1000 -g aislab aislab \
    && sudo usermod -aG wheel aislab \
    && mkdir -p /home/aislab/workspace \
    && echo "aislab:1234" | chpasswd \
    && mkdir -p /home/aislab/.ssh \
    && chmod 700 /home/aislab/.ssh \
    && sed -i 's/^#PubkeyAuthentication[[:space:]]\+yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# setup work directory and mount point
WORKDIR /home/aislab/workspace
VOLUME /home/aislab/workspace

# copy some files from local
COPY skeleton.tcshrc /home/aislab/.tcshrc
COPY setup.sh /setup.sh
RUN chmod +x /setup.sh

ENV SHELL /usr/bin/tcsh
# container entrypoint
EXPOSE 22
ENTRYPOINT ["/setup.sh"]
