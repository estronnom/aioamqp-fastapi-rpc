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


class RPCClient(AMQP):
    def __init__(self):
        self.response = None
        self.corr_id = str(uuid.uuid1())
        self.callback_queue = None
        self.waiter = asyncio.Event()
        super(RPCClient, self).__init__()

    async def connect(self):
        await super(RPCClient, self).connect()

        result = await self.channel.queue(exclusive=True)
        self.callback_queue = result['queue']
        await self.channel.basic_consume(
            self.__callback,
            no_ack=True,
            queue_name=self.callback_queue,
        )

    async def __callback(self, channel, body, envelope, properties):
        if self.corr_id == properties.correlation_id:
            self.response = body.decode()

        self.waiter.set()

    async def call(self, task, data):
        print('RPC client got a callback')
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
        print('RPC client sent a task')
        await self.waiter.wait()
        await self.protocol.close()
        print('RPC client got a response')
        return self.response


class RPCServer(AMQP):
    def __init__(self, app_name, task):
        self.app_name = app_name
        self.task = task
        super(RPCServer, self).__init__()

    async def __callback(self, channel, body, envelope, properties):
        print(f'{self.app_name.capitalize()} got a callback')
        body = body.decode()
        print(body)

        task_success, task_response = await self.task(body)
        payload = {
            "success": task_success,
            "response": task_response
        }
        payload = str(payload).encode()

        await self.channel.basic_publish(
            payload=payload,
            exchange_name='',
            routing_key=properties.reply_to,
            properties={
                "correlation_id": properties.correlation_id
            }
        )
        print(f'{self.app_name.capitalize()} sent a response')

    async def __consume(self):
        await self.connect()
        queue = await self.channel.queue(
            queue_name=self.app_name,
            durable=True
        )
        await self.channel.queue_bind(
            exchange_name=self.tasks_exc,
            queue_name=self.app_name,
            routing_key=self.app_name
        )

        print(f'Queue {self.app_name} created')
        await self.channel.basic_qos(
            prefetch_count=1,
            prefetch_size=0,
            connection_global=False
        )

        print(f'{self.app_name.capitalize()} listening')
        await self.channel.basic_consume(
            self.__callback,
            queue_name=self.app_name,
            no_ack=True
        )

    def listen(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__consume())
        loop.run_forever()
