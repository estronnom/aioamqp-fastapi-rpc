import os
import uuid
from fastapi import APIRouter, HTTPException, Depends
from aioamqp.channel import Channel

from .schema.task import TaskIn, TaskOut
from .utils.amqpinterface import AMQP

router = APIRouter()

amqp = AMQP()


@router.post('/do')
async def do_task(
        task: TaskIn,
        channel: Channel = Depends(amqp.get_chan)
):
    task_id = str(uuid.uuid1())
    payload = {
        "id": task_id,
        "data": task.dataIn
    }
    print(payload)

    await channel.publish(
        task.dataIn,
        exchange_name=amqp.tasks_exc,
        routing_key=task.task
    )

    response = TaskOut()

    if task.response:
        pass
        # queue = await channel.queue(
        #     durable=False,
        #     auto_delete=True
        # )
        # queue_name = queue['queue']
        # await channel.queue_bind(
        #     exchange_name=_RESULTS_EXCHANGE,
        #     queue_name=queue_name,
        #     routing_key=task_id
        # )
    else:
        response.sent = True

    return HTTPException(
        200,
        detail=response.dict(exclude_unset=True)
    )

