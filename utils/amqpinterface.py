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
        self.result_queue = os.getenv('RESULTQUEUE')
        self.__host = os.getenv('RABBITMQHOST', default='localhost')
        self.__port = os.getenv('RABBITMQPORT', default='5672')

    async def __connect(self):
        try:
            self.transport, self.protocol = await aioamqp.connect(
                host=self.__host,
                port=self.__port
            )
        except Exception as exc:
            print('Unable to connect to rabbitmq')
            print(exc)
            await asyncio.sleep(5)
            await self.__connect()
        else:
            self.channel = await self.protocol.channel()
            await self.channel.exchange(
                exchange_name=self.tasks_exc,
                type_name='direct',
                durable=True
            )

            await self.channel.queue(
                queue_name=self.result_queue,
                durable=True
            )

    async def get_chan(self):
        if not self.channel:
            await self.__connect()
        return self.channel


class RPCClient(AMQP):
    def __init__(self):
        self.tasks_id = dict()
        self.response = list()
        self.waiter = asyncio.Event()
        super(RPCClient, self).__init__()

    async def __callback(self, channel, body, envelope, properties):
        print('RPC client got a callback')
        if properties.correlation_id in self.tasks_id:
            body = body.decode()
            self.response.append(body)
            self.tasks_id.pop(properties.correlation_id)

        if not self.tasks_id:
            self.waiter.set()

    async def send_task(self, task, data):
        if not self.channel:
            await self.__connect()

        corr_id = str(uuid.uuid1())
        self.tasks_id[corr_id] = task

        await self.channel.basic_publish(
            payload=data.encode(),
            exchange_name=self.tasks_exc,
            routing_key=task,
            properties={
                'reply_to': self.result_queue,
                'correlation_id': corr_id,
            }
        )
        print('RPC client sent a task')

    async def get_results(self):
        print('RPC client waiting for results')
        await self.channel.basic_consume(
            self.__callback,
            no_ack=True,
            queue_name=self.result_queue,
        )

        await self.waiter.wait()
        print('RPC client collected all responses')
        await self.protocol.close()
        response = self.response.copy()
        self.__init__()
        return response


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
            "task": self.app_name,
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
        await self.__connect()
        await self.channel.queue(
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
