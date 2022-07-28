import os
import aioamqp
import asyncio


class AMQP:
    def __init__(self):
        self.transport = None
        self.protocol = None
        self.channel = None
        self.tasks_exc = os.getenv('TASKEXCHANGE')
        self.results_exc = os.getenv('RESULTEXCHANGE')
        self.__host = os.getenv('RABBITMQHOST', default='localhost')
        self.__port = os.getenv('RABBITMQPORT', default='5672')

    async def connect(self, loop):
        try:
            self.transport, self.protocol = await aioamqp.connect(
                host=self.__host,
                port=self.__port,
                loop=loop
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
            await self.channel.exchange(
                exchange_name=self.results_exc,
                type_name='direct',
                durable=True
            )

