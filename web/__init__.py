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


@app.route('/')
async def get_index():
    return await render_template('index.html')


@app.route('/charge_point')
async def get_charge_points():
    return await render_template('charge_points.html',
            charge_points=charge_points.items())


@app.route('/charge_point/<string:charger_id>')
async def get_charge_point(charger_id):
    return await render_template('charge_point.html', charge_point=charge_points[charger_id])

@app.websocket('/ws')
async def on_user_connect():
    print(asyncio.get_running_loop())
    l.msg('User connected')
    users.append(websocket)

    while True:
        msg = await get_queue().get()
        await websocket.send(msg)
        time.sleep(1)


@app.websocket('/<string:charger_id>')
async def on_charge_point_connect(charger_id):
    print(asyncio.get_running_loop())
    l.msg('Charge point connected', charger_id=charger_id)

    cp = ChargePoint(charger_id, WebSocketProxy(charger_id, websocket, get_queue()))

    charge_points[charger_id] = cp

    await cp.start()

    del charge_points[charger_id]
    l.msg('Charge point disconnected', charger_id=charger_id)


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
        return await self.websocket.send(msg)

    async def receive(self):
        msg = await self.websocket.receive()
        self.queue.put_nowait(json.dumps({
            'chargePointId': self.charger_id,
            'message': msg
        }))

        return msg
