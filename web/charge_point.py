import asyncio
from datetime import datetime
from functools import partial
from structlog import get_logger

from ocpp import call_result
from ocpp.ocpp_16_enums import Action, RegistrationStatus
from ocpp.ocpp_16_cs import on, OCPP16CentralSystemBase


l = get_logger()


class ChargePoint(OCPP16CentralSystemBase):
    def __init__(self, id, connection):
        self.id = id
        self.connection = connection

        super().__init__(self, None, None, None, None, connection)

        self.model = None
        self.vendor = None
        self.firmware = None

    @on(Action.BootNotification)
    async def on_boot_notification(self, charge_point_model, charge_point_vendor, **kwargs):
        self.model = charge_point_model
        self.vendor = charge_point_vendor

        if 'firmware_version' in kwargs:
            self.firmware = kwargs['firmware_version']

        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat('T', 'seconds') + 'Z',
            interval=1,
            status=RegistrationStatus.accepted.value,
        )

    @on(Action.Heartbeat)
    def on_heartbeat(self):
        return call_result.HeartbeatPayload(
            current_time=datetime.utcnow().isoformat('T', 'seconds') + 'Z',
        )

    async def start(self):
        while True:
            message = await self.connection.receive()
            l.msg('Received message from CP', charger_id=self.id, message=message)
            asyncio.create_task(self.route_message(message))

