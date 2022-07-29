from fastapi import APIRouter

from .schema import TaskIn
from .utils.amqpinterface import RPCClient

router = APIRouter()


@router.post('/do')
async def do_task(
        task: TaskIn
):
    client = RPCClient()
    response = await client.call(task.task, task.data_in)
    return response

