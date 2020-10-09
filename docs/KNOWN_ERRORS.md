# Docker-compose errors

Running command `docker-compose up -d --build`
Error received: `Creating network "panic_panic_net" with the default driver ERROR: Pool overlaps with other one on this address space`
Solution 1: `service docker restart`
Solution 2: `docker network prune` 
[Link to solution](https://github.com/maxking/docker-mailman/issues/85)

