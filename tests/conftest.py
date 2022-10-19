import pytest
import shutil
import os

REDIS_IMAGE="ubuntu:20.04"
BIN_SRC_PATH=f'{os.getcwd()}/artifacts'

import logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

@pytest.fixture(scope="session", autouse=True)
def create_tmp_folder_fixture():
    try:
        shutil.rmtree('./tmp')
    except Exception:
        pass
    os.mkdir('./tmp')

    # Let docker-compose consume default image and artifacts
    os.environ["IMAGE"] = REDIS_IMAGE
    os.environ["BIN_SRC_PATH"] = BIN_SRC_PATH

    yield

    shutil.rmtree('./tmp')
