from datetime import datetime, date, timedelta

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
        """
        Returns the time until the bus is due in minutes
        Intelligently handles wrapping to the next day if a late-night evaluation
        refers to an early morning time (e.g., evaluating 1:45am at 11:30pm).
        """
        time_str = self.data["dueIn"].strip().lower()
        formats = ["%I:%M%p", "%I:%M %p", "%H:%M"]
        
        parsed_time = None
        for fmt in formats:
            try:
                parsed_time = datetime.strptime(time_str, fmt).time()
                break
            except ValueError:
                continue
                
        if not parsed_time:
            raise ValueError(f"Time string '{time_str}' did not match supported formats.")
            
        now = datetime.now()
        
        # 1. Start by assuming the target time is today
        target_datetime = datetime.combine(date.today(), parsed_time)
        
        # 2. Calculate initial difference
        diff = target_datetime - now
        
        # 3. Handle midnight wrap-around logic:
        # If the target time is earlier today, but by MORE than 12 hours,
        # it's likely an early morning time meant for tomorrow.
        if diff.total_seconds() < 0 and abs(diff.total_seconds()) > 12 * 3600:
            target_datetime += timedelta(days=1)
            diff = target_datetime - now
            
        # If it's just a little bit behind now (less than 12 hours), 
        # it stays as today and returns a negative value (the recent past).
            
        return diff.total_seconds()


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
