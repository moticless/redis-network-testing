from .utils import *
import subprocess
import shutil
import time

class TestHostnameBasedSetup:
    SRC_DIR = 'docker-compose-setups/hostname-based'
    DST_DIR = f'./tmp/{SRC_DIR}'
    SETUP_NAME = "hostname-based"

    def setup_class(cls):
        shutil.copytree(cls.SRC_DIR, cls.DST_DIR)
        subprocess.check_call(["docker-compose", "-p", cls.SETUP_NAME, "up", "-d", "--force-recreate"], cwd=cls.DST_DIR)
        time.sleep(10)

    def teardown_class(cls):
        subprocess.check_call(["docker-compose", "down"], cwd=cls.DST_DIR)
        time.sleep(3)
        shutil.rmtree(cls.DST_DIR)

    def test_master_unavail(self):
        failover_and_recover_init(['--times', '2', '--wait', '30', "-p", self.SETUP_NAME])
        failover_and_recover()

    def test_master_and_sentinel_unavail(self):
        failover_and_recover_init(['--times', '2', '--wait', '30', "-p", self.SETUP_NAME, '--sentinel_restart'])
        failover_and_recover ()
