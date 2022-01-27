# redis-network-tests
Currently, redis OSS testbench has limited capabilities to test various network configurations such as, 
port-forwarding, hostname-discovery, or simulate network latency.

This repo attempts to test only Sentinel feature, but might be useful later on to test other network 
related features as well. This testbench creates a redis cluster with `docker-compose`, before invocation 
each group of tests.

Redis project is referenced as submodule and required to build artifacts with command `build_redis.py` before
invoking the tests:
    
    $ ./build_redis.py

To run the tests it is recommend to setup first pythov venv and then run:

    $ pytest


