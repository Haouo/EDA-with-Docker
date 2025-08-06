# specify official Rocky Linux 9.3 image as base image
FROM rockylinux:9.3

# install necessary packages for running EDA tools
RUN dnf update -y \
    && dnf install -y \
    sudo openssh-server openssh-clients \
    xorg-x11-xauth xauth xterm \
    epel-release wget vim tar time csh ksh \
    graphite2 bc iputils telnet \
    gcc g++ glibc elfutils-libelf \
    libXrandr libGL libXcomposite libnsl pulseaudio-libs-devel \
    libXi libXp libXp.i686 libXt libXt.i686 \
    libX11.i686 libXext.i686 libXrender.i686 libXtst.i686 \
    && dnf clean all

# mount /cad for using EDA tools
RUN mkdir /cad && ln -s /cad /usr/cad

# generate host ssh-keys
RUN ssh-keygen -q -t rsa -b 2048 -f /etc/ssh/ssh_host_rsa_key -N '' \
    && ssh-keygen -q -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N '' \
    && ssh-keygen -t dsa -f /etc/ssh/ssh_host_ed25519_key  -N ''

# add a user "rocky" and give it proper uid/gid
RUN groupadd -g 1000 rocky \
    && useradd -d /home/rocky -s /bin/bash -u 1000 -g rocky rocky \
    && sudo usermod -aG wheel rocky \
    && mkdir -p /home/rocky/workspace \
    && echo "rocky:1234" | chpasswd \
    && mkdir -p /home/rocky/.ssh \
    && chmod 777 /home/rocky/.ssh \
    && sed -i 's/^#PubkeyAuthentication[[:space:]]\+yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

WORKDIR /home/rocky/workspace
VOLUME /home/rocky/workspace

# copy some files from local
COPY skeleton.tcshrc /home/rocky/.tcshrc

# container entrypoint
EXPOSE 22
CMD [ "/usr/sbin/sshd", "-D", "-e", "-o", "ListenAddress=0.0.0.0" ]