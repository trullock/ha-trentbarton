from datetime import datetime, timedelta

import aiohttp
import json

TRENT_BARTON_API = "https://www.trentbarton.co.uk/RTILiveTimings.aspx"


class Bus:
    """Represents a bus"""

    def __init__(self, data):
        self.data = data
        # self.position = (data["longitude"], data["latitude"])
        # self.bus_stop = bus_stop
        # self.identifier = data["uniqueIdentifier"]

    @property
    def name(self):
        return self.data["serviceName"]

    @property
    def due(self):
        """Returns the time until the bus is due in minutes"""
        if self.data["dueIn"] == "due":
            return 0

        if self.data["dueIn"][:-2] == "pm" or self.data["dueIn"][:-2] == "am":
            now = datetime.now()
            due = datetime.combine(
                now.date(), datetime.strptime(self.data["dueIn"], "%I:%M %p").time()
            )
            if due < now:
                due += timedelta(days=1)
            return (due - now).total_seconds() // 60

        try:
            return int(self.data["dueIn"][:-4])
        except Exception:
            return self.data["dueIn"]

    @property
    def time(self):
        """Returns the expected time the bus will arrive at"""
        time = datetime.datetime.now() + datetime.timedelta(minutes=self.due)
        return time.strftime("%H:%M")

    def __str__(self):
        return f"{self.name} @ {self.time}, due: {self.due}"


class NullBus(Bus):
    """Represents unavailable data"""

    def __init__(self):
        super().__init__({})

    @property
    def name(self):
        return "N/A"

    @property
    def due(self):
        return 0

    @property
    def time(self):
        return "00:00"

    def __str__(self):
        return "Null bus"


class BusStop:
    """Represents a Trent Barton bus stop"""

    def __init__(self, name, stop_id):
        self.name = name
        self.stop_id = stop_id

    async def get_live_times(self):
        """Gets the live times for the buses at this stop"""
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                TRENT_BARTON_API, params={"m": "GetRtiFull", "stop": self.stop_id}
            )
            data = await response.read()
        decoded = json.loads(data)
        buses = [Bus(data) for data in decoded[0]["result"]]

        def sort_buses(bus):
            return bus.due

        buses.sort(key=sort_buses)
        return buses

    async def get_position(self):
        """Gets the position of the bus stop in longitude and latitude"""
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                TRENT_BARTON_API, params={"m": "GetLongLat", "stopId": self.stop_id}
            )
            data = await response.read()
        decoded = json.loads(data)
        return decoded

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"BusStop({repr(self.name)}, {repr(self.stop_id)})"


class Service:
    """Represents a Trent Barton bus service"""

    def __init__(self, name, service_id):
        self.name = name
        self.service_id = service_id

    async def get_directions(self):
        """Gets all the directions for the service"""
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                TRENT_BARTON_API,
                params={"m": "GetDirections", "service": self.service_id},
            )
            data = await response.read()
        decoded = json.loads(data)
        return decoded

    async def get_stops(self, directions=None):
        """Gets all the bus stops for the service, you may specify the specific direction(s) you want"""
        if not directions:
            directions = await self.get_directions()
        stops = []
        async with aiohttp.ClientSession() as session:
            for direction in directions:
                response = await session.get(
                    TRENT_BARTON_API,
                    params={
                        "m": "GetStops",
                        "direction": direction["Id"],
                        "locality": -1,
                    },
                )
                data = await response.read()
                decoded = json.loads(data)
                stops.extend([BusStop(data["Name"], data["Id"]) for data in decoded])
        return stops

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Service({repr(self.name)}, {repr(self.service_id)})"

    @classmethod
    async def get_service(cls, name):
        async with aiohttp.ClientSession() as session:
            response = await session.get(TRENT_BARTON_API, params={"m": "GetServices"})
            data = await response.read()
            decoded = json.loads(data)
            for service_data in decoded:
                if service_data["Name"] == name:
                    return Service(service_data["Name"], service_data["Id"])
