from fastapi import APIRouter

from .schema import TaskIn
from .utils.amqpinterface import RPCClient

router = APIRouter()


@router.post('/do')
async def do_task(
        task_list: TaskIn
):
    rpc = RPCClient()
    data = task_list.dict()['task_list']

    for item in data:
        await rpc.send_task(item['task'], item['data'])

    response = await rpc.get_results()
    return response



