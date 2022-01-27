#!/usr/bin/env python3
import docker
import os
import shutil

REDIS_IMAGE='ubuntu:20.04'

shutil.rmtree('./artifacts',ignore_errors=True)
print ("Building redis artifacts ...")
out = docker.from_env().containers.run(
    image=REDIS_IMAGE,
    command=" bash -c \"apt-get update; apt-get install -y build-essential libssl-dev; cd /redis && make\"",
    volumes={os.getcwd() + "/redis": {'bind': '/redis/', 'mode': 'rw'}})
print(out)

os.mkdir('./artifacts')
shutil.copyfile('./redis/src/redis-server', './artifacts/redis-server')
os.chmod('./artifacts/redis-server', 777)
shutil.copyfile('./redis/src/redis-benchmark', './artifacts/redis-benchmark')
os.chmod('./artifacts/redis-benchmark', 777)
shutil.copyfile('./redis/src/redis-sentinel', './artifacts/redis-sentinel')
os.chmod('./artifacts/redis-sentinel', 777)
shutil.copyfile('./redis/src/redis-cli', './artifacts/redis-cli')
os.chmod('./artifacts/redis-cli', 777)
