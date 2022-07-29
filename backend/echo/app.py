import os
from utils.amqpinterface import RPCServer

app_name = os.getenv('APP')


async def echo(data: str):
    return True, data[::-1]


if __name__ == '__main__':
    server = RPCServer(app_name, echo)
    server.listen()



