FROM ubuntu:20.04
RUN apt update
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
      apt-get -y install sudo

RUN apt-get install -y gcc-multilib
RUN apt-get install -y g++-multilib
RUN apt-get install -y cmake
RUN apt-get install -y libdwarf-dev
RUN apt-get install -y libelf-dev
RUN apt-get install -y libsqlite3-dev

RUN apt-get install -y python3-pip
RUN mkdir /home/docker
COPY . /home/docker/auto-yamcs
RUN cd  /home/docker/auto-yamcs && pip3 install -r src/requirements.txt
RUN cd  /home/docker/auto-yamcs && pytest --count=10
