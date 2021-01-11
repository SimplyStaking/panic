# Frequently asked questions

Sometimes depending on the system you are setting up PANIC on, errors may occur, here as some documented problems and solutions.

# Docker-compose network error

Running command `docker-compose up -d --build`
Error received: `Creating network "panic_panic_net" with the default driver ERROR: Pool overlaps with other one on this address space`
Solution 1: `service docker restart`
Solution 2: `docker network prune`
Solution 3: Change the IPs of the Docker network, including the subnet
[Link to solution](https://github.com/maxking/docker-mailman/issues/85)
[Link to solution](https://stackoverflow.com/questions/50514275/docker-bridge-conflicts-with-host-network)