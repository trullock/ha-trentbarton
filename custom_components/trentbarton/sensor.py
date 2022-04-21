"""Platform for sensor integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from sqlalchemy import null
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.const import TIME_MINUTES

from .const import *
from . import DOMAIN
from .trentbarton import *

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""

    serviceName = hass.data[DOMAIN][CONF_SERVICE]
    stopid = hass.data[DOMAIN][CONF_STOPID]
    num_buses = hass.data[DOMAIN][CONF_NUMBUSES]

    our_stop = null

    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    service = await Service.get_service(serviceName)
    bus_stops = await service.get_stops()
    for bus_stop in bus_stops:
        if bus_stop.stop_id == stopid:
            our_stop = bus_stop
            break

    sensorEntities = []

    async def async_update_data():
        # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        # handled by the data update coordinator.
        return await our_stop.get_live_times()

    def update_entities():
        i = 0
        for entity in sensorEntities:
            if len(coordinator.data) > i:
                entity.setValues(coordinator.data[i])
            else:
                entity.setValues(NullBus())
            entity.async_write_ha_state()
            i += 1

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name = "buses",
        update_method = async_update_data,
        update_interval = timedelta(seconds=60),
    )

    coordinator.async_add_listener(update_entities)

    await coordinator.async_config_entry_first_refresh()

    # Deliberately dont use initial bus data so the sensors get alphabetically ordered default names - so the default card gets them set up in the right order
    for i in range(0, num_buses - 1):
        sensor = BusSensor(coordinator, i)
        sensorEntities.append(sensor)

    async_add_entities(sensorEntities)


class BusSensor(CoordinatorEntity, SensorEntity):

    _attr_icon = "mdi:bus"
    _attr_native_unit_of_measurement = TIME_MINUTES

    def __init__(self, coordinator, index):
        super().__init__(coordinator)
        self._data = {}
        self.entity_id = f"trentbarton.upcoming_bus_{index}"
        self._bus = null
        self._index = index

    @property
    def name(self):
        return self._bus.name if self._bus == null else f"Bus {self._index}"

    @property
    def native_value(self):
        return self._bus.due if self._bus == null else 0

    def setBus(self, bus: Bus):
        self._bus = bus
