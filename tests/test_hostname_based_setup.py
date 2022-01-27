from .utils import failover_and_recover
import subprocess
import shutil
import time

class TestHostnameBasedSetup:
    DOCKER_COMPOSE_SETUP="docker-compose-setups/hostname-based/"

    def setup_class(cls):
        shutil.copytree(cls.DOCKER_COMPOSE_SETUP, f'./tmp/{cls.DOCKER_COMPOSE_SETUP}')
        subprocess.check_call(["docker-compose", "up", "-d"], cwd=f'./tmp/{cls.DOCKER_COMPOSE_SETUP}')
        time.sleep(10)

    def teardown_class(cls):
        print ("teardown")
        subprocess.check_call(["docker-compose", "down"], cwd=f'./tmp/{cls.DOCKER_COMPOSE_SETUP}')
        time.sleep(3)
        shutil.rmtree(f'./tmp/{cls.DOCKER_COMPOSE_SETUP}')

    def test_master_unavail(self):
        failover_and_recover (['--times', '2', '--wait', '30'])

    def test_master_and_sentinel_unavail(self):
        failover_and_recover (['--times', '2', '--wait', '30', '--sentinel_restart'])



