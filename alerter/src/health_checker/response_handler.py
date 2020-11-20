# TODO: This component will receive two types of messages. One is a response
#     : from the managers that all/some of the processes are working as
#     : expected (we need to store this is redis as json). The other response
#     : is a latest update of the monitors when it performed a good monitoring
#     : round last. Whenever either one of these operations is done, the health
#     : checker must save it's last update time to redis, so that the user
#     : can detect if there is a problem with the health checker.
