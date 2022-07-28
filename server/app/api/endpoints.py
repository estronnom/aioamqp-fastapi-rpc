from fastapi import APIRouter, HTTPException, Depends

from .utils.schema import TaskIn
from .utils.amqpinterface import RPC

router = APIRouter()


@router.post('/do')
async def do_task(
        task: TaskIn
):
    rpc = RPC()
    response = await rpc.call(task.task, task.dataIn)
    return response

