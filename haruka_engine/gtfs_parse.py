import csv
from bisect import bisect_left

from haruka_engine.gtfs_types import Routes, Stops, StopTimes, Trips


def since_midnight(hms: str) -> int:
    if not hms:
        return 0

    hmslist = hms.strip().split(":")
    h = int(hmslist[0]) * 3600 if hmslist[0] else 0
    m = int(hmslist[1]) * 60 if hmslist[1] else 0
    s = int(hmslist[2]) if hmslist[2] else 0
    return int(h + m + s)


def parse_stoptimes():
    parsed_stop_times: list[StopTimes] = []
    with open("data/tokyo-metro/stop_times.txt", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed_stop_times.append(
                StopTimes(
                    row["trip_id"],
                    since_midnight(row["arrival_time"]),
                    since_midnight(row["departure_time"]),
                    int(row["stop_id"]),
                    int(row["stop_sequence"]),
                )
            )
    return parsed_stop_times


def parse_stops():
    parsed_stops: list[Stops] = []
    with open("data/tokyo-metro/stops.txt", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed_stops.append(
                Stops(
                    int(row["stop_id"]),
                    row["stop_code"],
                    row["stop_name"],
                    float(row["stop_lat"]),
                    float(row["stop_lon"]),
                    int(row["zone_id"]),
                )
            )
    return parsed_stops


def parse_routes():
    parsed_routes: list[Routes] = []
    with open("data/tokyo-metro/routes.txt", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed_routes.append(
                Routes(
                    int(row["route_id"]),
                    row["agency_id"],
                    row["route_long_name"],
                    int(row["route_type"]),
                    str(row["route_color"]),
                )
            )
    return parsed_routes


def parse_trips():
    parsed_trips: list[Trips] = []
    with open("data/tokyo-metro/trips.txt", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed_trips.append(
                Trips(
                    int(row["route_id"]),
                    row["service_id"],
                    row["trip_id"],
                    row["trip_headsign"],
                    int(row["direction_id"]),
                )
            )
    return parsed_trips


# Index 1 - Match stop_id to route_id. Creates dict of these routes will stop at this station. Stop -> Routes
# returns dict -> {stop_id(int): set(route_id(int), ...)}


def stops_at_this_station():
    all_stop_times = parse_stoptimes()

    trips_to_routes = trips_to_routes_helper()
    stops_at_this_station: dict[int, set[int]] = {}

    for stoptime in all_stop_times:
        stop_id = stoptime.stop_id
        route_id: int = trips_to_routes[stoptime.trip_id]
        if stop_id not in stops_at_this_station:
            stops_at_this_station[stop_id] = set()

        stops_at_this_station[stop_id].add(route_id)
    return stops_at_this_station


# Index 2 - Given this route, what stops does it visit and in what order. Route -> Ordered Stops
# returns dict -> {route_id(int), list[stop_id(int)]}


def get_stops_from_route():
    all_trips = parse_trips()

    found_routes: dict[int, str] = {}
    for trip in all_trips:
        route_id = trip.route_id
        if route_id not in found_routes:
            found_routes[route_id] = trip.trip_id

    ordered_routes: dict[int, list[int]] = {}
    timetable = get_times()
    for item in found_routes.items():
        route = item[0]
        trip = item[1]
        stop_ids: list[int] = []
        sorted_stoptimes = sorted(
            timetable[trip].values(), key=lambda x: x.stop_sequence
        )
        for stoptime in sorted_stoptimes:
            stop_ids.append(stoptime.stop_id)
        ordered_routes[route] = stop_ids
    return ordered_routes


# Index 3 - Given a route and a stop on it along with a t = "time i'd like to get on the train", find the earliest departing at/after t


def build_depart_times():
    all_stop_times = parse_stoptimes()

    trips_to_routes = trips_to_routes_helper()

    departure_times: dict[tuple[int, int], list[StopTimes]] = {}
    for stoptime in all_stop_times:
        route_id = trips_to_routes[stoptime.trip_id]
        dict_key = (route_id, stoptime.stop_id)

        if dict_key not in departure_times:
            departure_times[dict_key] = []
        departure_times[dict_key].append(stoptime)

    for values in departure_times.values():
        values.sort(key=lambda x: x.departure_time)

    return departure_times


def get_depart_times(query_time: int, route_id: int, stop_id: int):
    all_depart_times = build_depart_times()
    times_at_stop = all_depart_times[(route_id, stop_id)]

    idx = bisect_left(
        times_at_stop,
        query_time,
        key=lambda x: x.departure_time,
    )

    if idx == len(times_at_stop):
        return None
    return times_at_stop[idx]


# Index 4 - Given a specific stop and trip, immediately find the arrival & departure times. funcArr(trip, stop) Trip -> Stop -> StopTime
# returns dict -> {trip_id(int): {stop_id(int): stoptime(Stop_times), ...}}


def get_times():
    all_stop_times = parse_stoptimes()
    timetable: dict[str, dict[int, StopTimes]] = {}

    for stoptime in all_stop_times:
        trip_id = stoptime.trip_id
        stop_id = stoptime.stop_id

        if trip_id not in timetable:
            timetable[trip_id] = {}
        timetable[trip_id][stop_id] = stoptime

    return timetable


# Helper Functions


def trips_to_routes_helper():

    all_trips = parse_trips()

    trips_to_routes: dict[str, int] = {}  # {trip_id: route_id}

    for trip in all_trips:
        trips_to_routes[trip.trip_id] = trip.route_id
    return trips_to_routes
