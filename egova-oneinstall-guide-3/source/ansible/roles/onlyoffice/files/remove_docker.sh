#!/bin/bash

systemctl stop docker

rm -rf /usr/bin/containerd

rm -rf /usr/bin/containerd-shim

rm -rf /usr/bin/ctr

rm -rf /usr/bin/docker

rm -rf /usr/bin/dockerd

rm -rf /usr/bin/docker-init

rm -rf /usr/bin/docker-proxy

rm -rf /usr/bin/runc

rm -rf /usr/bin/docker-compose

rm -rf /etc/systemd/system/docker.service

rm -rf /egova/egova_docker