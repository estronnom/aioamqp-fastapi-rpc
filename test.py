import aioamqp
import asyncio


async def callback(chan, body, envelope, properties):
    print(chan, body, envelope, properties)


async def main():
    transport, protocol = await aioamqp.connect()
    channel = await protocol.channel()
    await channel.queue(queue_name='test', durable=True)
    await channel.basic_consume(callback, 'test')


if __name__ == '__main__':
    asyncio.run(main())
