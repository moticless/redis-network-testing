#!/bin/bash -e

# Replace placeholder __HOST_IP__ with host ip that accessed from inside container
HOST_IP=$(docker run --rm -it redis:latest bash -c "apt-get update;apt-get install dnsutils -y;  dig +short host.docker.internal" | tail -n 1 | sed "s/\r//")

#rm -rf ./config || true
#cp -r ./config-template ./config
find  ./config -type f -name '*.conf' -exec sed -i '' "s/__HOST_IP__/$HOST_IP/g" {} \;

