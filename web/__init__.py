import time
import json
import asyncio
import websockets
from structlog import get_logger
from quart import Quart, websocket, render_template

from web.charge_point import ChargePoint

l = get_logger()

users = []
charge_points = {}

queue = None

def get_queue():
    global queue
    if queue is None:
        queue = asyncio.Queue()

    return queue


app = Quart(__name__)



@app.websocket('/ws')
async def on_user_connect():
    l.msg('User connected')
    users.append(websocket)

    for charger_id, cp in charge_points.items():
        await websocket.send(json.dumps({
            'chargePointId': charger_id,
            'message': json.dumps({'action': 'online'}),
        }))

    task = asyncio.create_task(listen(websocket))
    while True:
        msg = await get_queue().get()
        await websocket.send(msg)

    task.cancel()


@app.websocket('/<string:charger_id>')
async def on_charge_point_connect(charger_id):
    cp = ChargePoint(charger_id, WebSocketProxy(charger_id,
        websocket._get_current_object(), get_queue()))

    charge_points[charger_id] = cp

    await cp.start()

    del charge_points[charger_id]
    l.msg('Charge point disconnected', charger_id=charger_id)


async def listen(websocket):
    while True:
        data = await websocket.receive()
        msg = json.loads(data)

        try:
            cp = charge_points[msg['chargePointId']]
            await cp.set_charge_limit(msg['chargeLimit'])
        except KeyError as e:
            l.warning(e)


class WebSocketProxy:
    def __init__(self, charger_id, websocket, queue):
        self.charger_id = charger_id
        self.websocket = websocket
        self.queue = queue

    async def async_send(self, msg):
        self.queue.put_nowait(json.dumps({
            'chargePointId': self.charger_id,
            'message': msg
        }))
        await self.websocket.send(msg)


    async def receive(self):
        msg = await self.websocket.receive()
        l.info("Receive message from CP", proxy=self, websocket=websocket, msg=msg)
        self.queue.put_nowait(json.dumps({
            'chargePointId': self.charger_id,
            'message': msg
        }))

        return msg
