# specify base image as official ubuntu image
FROM ubuntu:24.04

# basic setup
ARG BASIC="fish sudo git vim build-essential curl wget tar unzip make openssh-server openssh-client \
  gtkwave libreadline-dev x11-utils x11-apps man-db python3 python3-pip \
  clangd clang-format software-properties-common valgrind unminimize feh sxiv"
ENV TZ="Asia/Taipei"
RUN sed -i "s/archive.ubuntu.com/mirror.twds.com.tw/g" /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get update \
    && apt-get install --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt-get install -y ${BASIC} \
    && yes | unminimize \
    && apt-add-repository ppa:maveonair/helix-editor && apt-get update && apt-get install -y helix \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && service ssh start

# user and workdir setup
RUN echo "ubuntu:1234" | chpasswd \
    && mkdir /home/ubuntu/workspace \
    && chown -R ubuntu:ubuntu /home/ubuntu/workspace
USER ubuntu
WORKDIR /home/ubuntu/workspace
VOLUME /home/ubuntu/workspace

# Install pre-commit framework for Git pre-commit hooks
RUN pip install --user --break-system-package pre-commit
ENV PATH=/home/ubuntu/.local/bin:$PATH


# container entrypoint
ENTRYPOINT ["tail"]
CMD ["-f", "/dev/null"]
