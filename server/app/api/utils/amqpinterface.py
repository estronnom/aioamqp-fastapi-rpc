import os
import uuid

import aioamqp
import asyncio


class AMQP:
    def __init__(self):
        self.transport = None
        self.protocol = None
        self.channel = None
        self.tasks_exc = os.getenv('TASKEXCHANGE')
        self.__host = os.getenv('RABBITMQHOST', default='localhost')
        self.__port = os.getenv('RABBITMQPORT', default='5672')

    async def connect(self):
        try:
            self.transport, self.protocol = await aioamqp.connect(
                host=self.__host,
                port=self.__port
            )
        except Exception as exc:
            print('Unable to connect to rabbitmq')
            print(exc)
            await asyncio.sleep(5)
            await self.connect()
        else:
            self.channel = await self.protocol.channel()
            await self.channel.exchange(
                exchange_name=self.tasks_exc,
                type_name='direct',
                durable=True
            )

    async def get_chan(self):
        if not self.channel:
            await self.connect()
        return self.channel


class RPC(AMQP):
    def __init__(self):
        self.response = None
        self.corr_id = str(uuid.uuid1())
        self.callback_queue = None
        self.waiter = asyncio.Event()
        super(RPC, self).__init__()

    async def connect(self):
        await super(RPC, self).connect()

        result = await self.channel.queue(exclusive=True)
        self.callback_queue = result['queue']
        await self.channel.basic_consume(
            self.__callback,
            no_ack=True,
            queue_name=self.callback_queue,
        )

    async def __callback(self, channel, body, envelope, properties):
        if self.corr_id == properties.correlation_id:
            self.response = body

        self.waiter.set()

    async def call(self, task, data):
        await self.connect()
        await self.channel.basic_publish(
            payload=data.encode(),
            exchange_name=self.tasks_exc,
            routing_key=task,
            properties={
                'reply_to': self.callback_queue,
                'correlation_id': self.corr_id,
            }
        )

        await self.waiter.wait()
        await self.protocol.close()
        return self.response

