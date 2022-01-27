#!/usr/bin/python3

from datetime import datetime
import argparse
import docker
import time
import os

sentinel_stopped = 0

def init(cmd_args=""):
    global client, args
    client = docker.from_env()
    parser = argparse.ArgumentParser(description='Pause Wait Unpause Master')
    parser.add_argument("-m","--mapped_port", action='store_true', help='whether distinct master by ip or by its port')
    parser.add_argument("-t","--times", type=int, default=1, help='number iterations to execute')
    parser.add_argument("--header", type=ascii, default="", help='Header of test')
    parser.add_argument("-s","--sentinel_restart", action='store_true', help='in addition restart also one sentinel')
    parser.add_argument("-w","--wait", type=int, default=60, help='how many seconds to wait after container pause/unpause')
    args=parser.parse_args(cmd_args)
    identify_containers()

def failover():
    global i_master
    global sentinels
    global sentinel_stopped
    i_master = -1
    i_master = get_master_index()
    print( "Steady state: " + get_containers_status() )
    print (f'----> About to stop current master, Replica #{i_master} ({get_master_addr()})')
    replicas[i_master].stop()
    if args.sentinel_restart:
        sentinels[sentinel_stopped].stop()
        print (f'----> Replica #{i_master} and Sentinel #{sentinel_stopped} unavailable now')
    else:
        print (f'----> Replica #{i_master} unavailable now')
    print(f'----> Wait {args.wait}sec to failover to complete')
    time.sleep(args.wait)
    verify_num_sentinels_status_ok(len(sentinels)-1 if args.sentinel_restart else len(sentinels))
    replicas[i_master].start()
    if args.sentinel_restart:
        sentinels[sentinel_stopped].start()
        print (f'----> Replica and Sentinel are available. Now wait {args.wait}sec')
    else:
        print (f'----> Replica is available. Now wait {args.wait}sec')
    time.sleep(args.wait)
    verify_num_sentinels_status_ok(len(sentinels))
    sentinel_stopped = (1 + sentinel_stopped) % len(sentinels)

def identify_containers():
    global sentinels
    global replicas
    global contlist
    global client

    sentinels = []
    replicas = []
    contlist = client.containers.list()
    index = 0
    for c in contlist:
        if "sentinel" in c.name:
            sentinels.append(c)
        else:
            replicas.append(c)
        index = index + 1

def get_status_sentinel(container):
    res = container.exec_run("redis-cli -p 26379 info Sentinel")
    if res[0] != 0:
        return "Failed to run command: redis-cli -p 26379 info Sentinel"
    for line in res[1].decode().splitlines():
        if "status" in line:
            return line

def get_containers_status():
    global sentinels
    global sentinel_stopped
    res = ""
    for i in range(len(sentinels)):
        sentinels[i].reload()
        sentinel_status=sentinels[i].attrs['State']['Status']
        if sentinel_status == "running":
            res += f'\n Sentinel {i} [{get_container_ip(sentinels[i])}] status: {get_status_sentinel(sentinels[i])} master_addr:{get_master_addr(i)}'
        else:
            res += f'\n Sentinel {i} [{get_container_ip(sentinels[i])}] status: {sentinel_status}'
    for i in range(len(replicas)):
        replicas[i].reload()
        replica_status=replicas[i].attrs['State']['Status']
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

def get_master_addr( sentinel_to_query =-1 ):
    global sentinels
    global sentinel_stopped
    if sentinel_to_query == -1:
        sentinel_to_query = (1 + sentinel_stopped) % len(sentinels)

    res = sentinels[sentinel_to_query].exec_run("redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster")
    if res[0] != 0:
        raise
    return res[1].decode().split('\n')

def get_master_index():
    global replicas
    res = []
    master_addr = get_master_addr()
    index = 0
    for c in replicas:
        if args.mapped_port:
            if  master_addr[1] == get_container_mapped_port(c):
                res.append(index)
        else:
            if  master_addr[0] == get_container_ip(c):
                res.append(index)
            elif master_addr[0] in get_container_aliases(c):
                res.append(index)

        index = index + 1
    if len(res) == 1:
        return res[0]
    raise

def verify_num_sentinels_status_ok(expect_num_sentinels_ok):
    print (f'----> Done wait {args.wait}sec. Verify {expect_num_sentinels_ok} sentinels status ok')
    containers_status = get_containers_status()

    if containers_status.count("status=ok") != expect_num_sentinels_ok:
        os.system('say "your program has failed"')
        time.sleep(1000)
        print("Current Failure Time =", datetime.now().strftime("%H:%M:%S"))
        assert False, f'containers_status: {containers_status}'
    print( containers_status )

def main(cmd_args):
    init(cmd_args)
    for i in range(1,args.times+1):
        print (f'------------------------------ START TEST {args.header} iter:{i} ---------------------------')
        failover()
        print (f'------------------------------ END TEST {args.header} iter:{i} ----------------------------\n\n')

#main()

