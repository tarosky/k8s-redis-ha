#!/bin/bash

set -eux

mkdir -p /opt/bin
cp /dig-a /dig-srv /k8s-redis-ha-server /opt/bin
cp /redis.template.conf /opt
chmod -R +x /opt/bin
