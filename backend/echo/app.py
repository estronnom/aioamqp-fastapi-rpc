import os
import asyncio
from server.app.api.utils.amqpinterface import AMQP

app_name = os.getenv('APP')
amqp = AMQP()


async def callback(chan, body, envelope, properties):
    print(chan, body, envelope, properties)


async def main(event_loop):
    await amqp.connect(event_loop)
    await amqp.channel.queue(queue_name=app_name, durable=True)
    await amqp.channel.queue_bind(
        exchange_name=amqp.tasks_exc,
        queue_name=app_name,
        routing_key=app_name
    )
    print('got there')
    await amqp.channel.basic_consume(callback, queue_name=app_name)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))

