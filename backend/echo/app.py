import os
import asyncio
from utils.amqpinterface import AMQP

app_name = os.getenv('APP')
amqp = AMQP()


async def callback(channel, body, envelope, properties):
    print('Echo got a new message')
    print(body)
    body = body.decode()[::-1]

    await channel.basic_publish(
        payload=body.encode(),
        exchange_name='',
        routing_key=properties.reply_to,
        properties={
            'correlation_id': properties.correlation_id
        }
    )
    print('Echo sent a response')

    # await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)


async def main():
    await amqp.connect()
    await amqp.channel.queue(queue_name=app_name, durable=True)
    await amqp.channel.queue_bind(
        exchange_name=amqp.tasks_exc,
        queue_name=app_name,
        routing_key=app_name
    )
    await amqp.channel.basic_qos(
        prefetch_count=1,
        prefetch_size=0,
        connection_global=False
    )

    print('Echo listening')
    await amqp.channel.basic_consume(
        callback,
        queue_name=app_name,
        no_ack=True
    )


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()

