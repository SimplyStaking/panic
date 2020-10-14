import json

from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.moniterables.system import System, SystemType
from alerter.src.monitors.system import SystemMonitor
from alerter.src.utils.logging import DUMMY_LOGGER

# consumer
def main():
    # Set durable to true so that if rabbitmq restarts the queue is not lost
    # channel.queue_declare(queue='task_queue', durable=True)

    monitor.rabbitmq.exchange_declare('raw_data', 'direct', False, True, False, False)
    # Queue is deleted when connection is closed by exclusive flag
    result = monitor.rabbitmq.queue_declare(queue='', exclusive=True)
    # Bind queue to exchange, result.method.queue contains the randomly created queue name
    monitor.rabbitmq.queue_bind(exchange='raw_data', queue=result.method.queue, routing_key='system')

    print(' [*] Waiting for messages. To exit press CTRL+C')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % json.loads(body))
        # time.sleep(body.count(b'.'))
        # print(" [x] Done")
        # ch.basic_ack(delivery_tag=method.delivery_tag)

    # By this code messages are deleted from rabbitmq when they are delivered
    # channel.basic_consume(queue='hello', on_message_callback=callback,
    #                       auto_ack=True)

    # # Do not send next message unless current has been acknowledged
    # channel.basic_qos(prefetch_count=1)
    # channel.basic_consume(queue='task_queue', on_message_callback=callback)

    monitor.rabbitmq.basic_consume(
        queue=result.method.queue, on_message_callback=callback, auto_ack=True)

    monitor.rabbitmq.start_consuming()


if __name__ == '__main__':
    system = System('test_system', 'http://172.16.152.36:9100/metrics',
                    SystemType.BLOCKCHAIN_NODE_SYSTEM, 'test_chain')
    redis = RedisApi(DUMMY_LOGGER, 10)
    monitor = SystemMonitor('test_monitor', system, DUMMY_LOGGER, redis)
    monitor.rabbitmq.connect_till_successful()
    main()


# publisher
system = System('test_system', 'http://172.16.152.36:9100/metrics',
                SystemType.BLOCKCHAIN_NODE_SYSTEM, 'test_chain')
redis = RedisApi(DUMMY_LOGGER, 10)
monitor = SystemMonitor('test_monitor', system, DUMMY_LOGGER, redis)
monitor.rabbitmq.connect_till_successful()
monitor.rabbitmq.confirm_delivery()
monitor.rabbitmq.exchange_declare('raw_data', 'direct', False, True, False,
                                  False)
monitor.send_data()