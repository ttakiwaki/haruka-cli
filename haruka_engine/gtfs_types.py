from dataclasses import dataclass


@dataclass
class StopTimes:
    trip_id: str
    arrival_time: int  # time since midnight
    departure_time: int  # time since midnight
    stop_id: int
    stop_sequence: int


@dataclass
class Stops:
    stop_id: int
    stop_code: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    zone_id: int


@dataclass
class Trips:
    route_id: int
    service_id: str
    trip_id: str
    trip_headsign: str
    direction_id: int


@dataclass
class Routes:
    route_id: int
    agency_id: str
    route_long_name: str
    route_type: int
    route_color: str
