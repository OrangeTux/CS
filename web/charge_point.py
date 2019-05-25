import asyncio
from datetime import datetime
from functools import partial
from structlog import get_logger

from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call_result, call
from ocpp.v16.enums import Action, RegistrationStatus

log = get_logger()


def create_charging_profile(limit):
    return {
        'charging_profile_id': 1,
        'transaction_id': 0,
        'stack_level': 0,
        'charging_profile_purpose': 'TxProfile',
        'charging_profile_kind': 'Relative',
        'charging_schedule': {
            'charging_rate_unit': 'A',
            'charging_schedule_period': [{
                'start_period': 0,
                'limit': limit,
            }]
        }
    }


class ChargePoint(cp):
    def __init__(self, id, connection):
        self.id = id
        self.connection = connection

        super().__init__(id, connection)

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
            status=RegistrationStatus.accepted
        )

    @on(Action.Heartbeat)
    def on_heartbeat(self):
        return call_result.HeartbeatPayload(
            current_time=datetime.utcnow().isoformat('T', 'seconds') + 'Z',
        )

    @on(Action.MeterValues)
    def on_meter_value(self, connector_id, meter_value, **kwargs):
        return call_result.MeterValuesPayload()

    async def set_charge_limit(self, limit):
        response = await self.call(call.SetChargingProfilePayload(
            connector_id=0,
            cs_charging_profiles=create_charging_profile(limit),
        ))

    # async def start(self):
        # while True:
            # message = await self.connection.receive()
            # log.info("Message received", msg=message)
            # asyncio.create_task(self.route_message(message))
