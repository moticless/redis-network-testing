from .utils import *
import subprocess
import docker
import shutil
import time
import os

class TestPortForwardingSetup:
    SRC_DIR = 'docker-compose-setups/port-forwarding/'
    DST_DIR = f'./tmp/{SRC_DIR}'
    SETUP_NAME = "port-forwarding"

    def setup_class(cls):
        shutil.copytree(cls.SRC_DIR, cls.DST_DIR)
        subprocess.check_call(["docker-compose", "-p", cls.SETUP_NAME, "up", "-d"], cwd=cls.DST_DIR)
        time.sleep(10)

    def teardown_class(cls):
        subprocess.check_call(["docker-compose", "down"], cwd=cls.DST_DIR)
        time.sleep(3)
        shutil.rmtree(cls.DST_DIR)

    def test_master_unavail(self):
        failover_and_recover_init(['--times', '2', '--mapped_port', '--wait', '30', "-p", self.SETUP_NAME ])
        failover_and_recover()

    def test_master_and_sentinel_unavail(self):
        failover_and_recover_init(['--times', '2', '--mapped_port', '--wait', '30', "-p", self.SETUP_NAME, '--sentinel_restart'])
        failover_and_recover ()

#    def test_master_restart_and_ip_change(self):
#        containers = failover_and_recover_init(['--times', '2', '--mapped_port', '--wait', '30', "-p", self.SETUP_NAME, '--sentinel_restart'])
#        print(containers)
#        # Simulate replica restart along with ip change
#        containers['repl'][0].stop()
#
#        #containers['stndby'].stop()
#        time.sleep(20)
#        #containers['stndby'].start(command="redis-server /test/config/replica1.conf")
#        docker.from_env().containers.run("ubuntu:20.04", command='redis-server /test/config/replica1.conf',
#                                         ports={'6379/tcp': 30692},
#                                         volumes={os.getcwd() + "/artifacts": {'bind': '/usr/local/bin/', 'mode': 'rw'},
#                                                  os.getcwd() + '/tmp/docker-compose-setups/port-forwarding/config': {'bind': '/test/config/', 'mode': 'rw'}})
