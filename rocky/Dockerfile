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
VOLUME /cad
# mount /sys for fixing Design Compiler error
VOLUME /sys 

# add a user "rocky" and give it proper uid/gid
RUN groupadd -g 1000 rocky \
    && useradd -d /home/rocky -s /bin/bash -u 1000 -g rocky rocky \
    && mkdir -p /home/rocky/workspace \
    && echo "rocky:1234" | chpasswd
USER rocky
WORKDIR /home/rocky/workspace
VOLUME /home/rocky/workspace

# container entrypoint
ENTRYPOINT ["tail"]
CMD ["-f", "/dev/null"]