from .utils import failover_and_recover
import subprocess
import shutil
import time

class TestStaticIpSetup:
    SRC_DIR='docker-compose-setups/static-ip/'
    DST_DIR = f'./tmp/{SRC_DIR}'

    def setup_class(cls):
        shutil.copytree(cls.SRC_DIR, cls.DST_DIR)
        subprocess.check_call(["docker-compose", "up", "-d"], cwd=cls.DST_DIR)
        time.sleep(10)

    def teardown_class(cls):
        print("teardown")
        subprocess.check_call(["docker-compose", "down"], cwd=cls.DST_DIR)
        time.sleep(3)
        shutil.rmtree(cls.DST_DIR)

    def test_master_unavail(self):
        failover_and_recover (['--times', '2', '--wait', '30'])

    def test_master_and_sentinel_unavail(self):
        failover_and_recover (['--times', '2', '--wait', '30', '--sentinel_restart'])



