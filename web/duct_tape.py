import asyncio
from structlog import get_logger

import websockets
from ocpp.ocpp_16_cs import OCPP16CentralSystemBase

log = get_logger()


class ServerWebSocket(websockets.server.WebSocketServerProtocol):
    async def async_send(self, msg):
        log.info("Message send", msg=msg)
        await self.send(msg)


class ClientWebSocket(websockets.client.WebSocketClientProtocol):
    async def async_send(self, msg):
        log.info("Message send", msg=msg)
        await self.send(msg)


class ChargePoint(OCPP16CentralSystemBase):
    def __init__(self, connection):
        self.connection = connection

        super().__init__(self, None, None, None, None, connection)

    async def start(self):
        async for message in self.connection:
            log.info("Message received", msg=message)
            asyncio.create_task(self.route_message(message))
