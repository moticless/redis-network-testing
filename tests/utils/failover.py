#!/usr/bin/python3

from datetime import datetime
import argparse
import docker
import time
import os
import logging

sentinel_stopped = 0
containers = {}

def init(cmd_args=""):
    global client, args
    global containers

    client = docker.from_env()
    parser = argparse.ArgumentParser(description='Failover and recover replicas')
    parser.add_argument("-m", "--mapped_port", action='store_true', help='whether distinct master by ip or by its port')
    parser.add_argument("-t", "--times", type=int, default=1, help='number iterations to execute')
    parser.add_argument("-p", "--proj_name", type=ascii, default="",
                        help='Project name (Used by docker-cmpose and as test header')
    parser.add_argument("-s", "--sentinel_restart", action='store_true', help='in addition restart also one sentinel')
    parser.add_argument("-w", "--wait", type=int, default=60,
                        help='how many seconds to wait after container pause/unpause')
    args = parser.parse_args(cmd_args)
    identify_containers()
    return containers

def failover():
    global i_master
    global sentinel_stopped
    i_master = -1
    # logging.info (f'----> Let system reach steady state. Wait {args.wait}sec')
    time.sleep(5)
    verify_num_sentinels_status_ok(len(containers['sent']))
    i_master = get_master_index()
    logging.info("Steady state: " + get_cluster_status())
    logging.info(f'----> About to stop current master, Replica #{i_master} ({get_master_addr()})')
    containers['repl'][i_master].stop()
    if args.sentinel_restart:
        containers['sent'][sentinel_stopped].stop()
        logging.info(f'----> Replica #{i_master} and Sentinel #{sentinel_stopped} unavailable now')
    else:
        logging.info(f'----> Replica #{i_master} unavailable now')
    logging.info(f'----> Wait {args.wait}sec to failover to complete')
    time.sleep(args.wait)
    verify_num_sentinels_status_ok(len(containers['sent']) - 1 if args.sentinel_restart else len(containers['sent']))
    containers['repl'][i_master].start()
    if args.sentinel_restart:
        containers['sent'][sentinel_stopped].start()
        logging.info(f'----> Replica and Sentinel are available. Now wait {args.wait}sec')
    else:
        logging.info(f'----> Replica is available. Now wait {args.wait}sec')
    time.sleep(args.wait)
    verify_num_sentinels_status_ok(len(containers['sent']))
    sentinel_stopped = (1 + sentinel_stopped) % len(containers['sent'])

def identify_containers():
    global client
    global containers

    containers = {}
    containers['sent'] = []
    containers['repl'] = []
    containers['stndby'] = ""
    index = 0
    for c in client.containers.list():
        if c.name.startswith(args.proj_name.strip("'")):
            if "sentinel" in c.name:
                containers['sent'].append(c)
            if "replica" in c.name:
                containers['repl'].append(c)
            if "standby" in c.name:
                containers['stndby'] = c
        index = index + 1
    print(containers)

def get_status_sentinel(container):
    res = container.exec_run("redis-cli -p 26379 info Sentinel")
    if res[0] != 0:
        return "Failed to run command: redis-cli -p 26379 info Sentinel"
    for line in res[1].decode().splitlines():
        if "status" in line:
            return line

def get_cluster_status():
    global containers
    global sentinel_stopped
    res = ""
    sentinels = containers['sent']
    replicas = containers['repl']
    for i in range(len(containers['sent'])):
        sentinels[i].reload()
        sentinel_status = sentinels[i].attrs['State']['Status']
        if sentinel_status == "running":
            res += f'\n Sentinel {i} [{get_container_ip(sentinels[i])}] status: {get_status_sentinel(sentinels[i])} master_addr:{get_master_addr(i)}'
        else:
            res += f'\n Sentinel {i} [{get_container_ip(sentinels[i])}] status: {sentinel_status}'
    for i in range(len(replicas)):
        replicas[i].reload()
        replica_status = replicas[i].attrs['State']['Status']
        if replica_status == "running":
            res += f'\n Replica  {i} [{get_container_ip(replicas[i])}] status: mapped-port: {get_container_mapped_port(replicas[i])} '
        else:
            res += f'\n Replica  {i} [{get_container_ip(replicas[i])}] status: {replica_status}'
    return res

def get_container_mapped_port(container):
    container_ports = container.attrs['NetworkSettings']['Ports']
    if container_ports and container_ports['6379/tcp']:
        return container_ports['6379/tcp'][0]['HostPort']
    return "None"

def get_container_aliases(container):
    return next(iter(container.attrs['NetworkSettings']['Networks'].values()))['Aliases']

def get_container_ip(container):
    return next(iter(container.attrs['NetworkSettings']['Networks'].values()))['IPAddress']

def get_master_addr(sentinel_to_query=-1):
    global containers
    global sentinel_stopped
    if sentinel_to_query == -1:
        sentinel_to_query = (1 + sentinel_stopped) % len(containers['sent'])

    res = containers['sent'][sentinel_to_query].exec_run("redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster")
    if res[0] != 0:
        raise
    return res[1].decode().split('\n')

def get_master_index():
    global containers
    res = []
    master_addr = get_master_addr()
    index = 0
    for c in containers['repl']:
        if args.mapped_port:
            if master_addr[1] == get_container_mapped_port(c):
                res.append(index)
        else:
            if master_addr[0] == get_container_ip(c):
                res.append(index)
            elif master_addr[0] in get_container_aliases(c):
                res.append(index)

        index = index + 1
    if len(res) == 1:
        return res[0]
    raise

def verify_num_sentinels_status_ok(expect_num_sentinels_ok):
    logging.info(f'----> Done wait {args.wait}sec. Verify {expect_num_sentinels_ok} sentinels status ok')
    containers_status = get_cluster_status()

    if containers_status.count("status=ok") != expect_num_sentinels_ok:
        assert False, f'Invalid containers_status: {containers_status}'
    logging.info(containers_status)


def run_failover():
    for i in range(1, args.times + 1):
        logging.info(f'------------------------------ START TEST {args.proj_name} iter:{i} ---------------------------')
        failover()
        logging.info(
            f'------------------------------ END TEST {args.proj_name} iter:{i} ----------------------------\n\n')

# run_failover()
