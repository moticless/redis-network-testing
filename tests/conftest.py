import pytest
import shutil
import os

REDIS_IMAGE="redis-sentinel"

@pytest.fixture(scope="session", autouse=True)
def create_tmp_folder_fixture():
    os.mkdir('./tmp')
    yield
    shutil.rmtree('./tmp')

