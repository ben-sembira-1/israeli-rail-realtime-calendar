import argparse
import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import pytz
import requests
from icalendar import Calendar, Event
from pydantic import BaseModel, ConfigDict, ValidationError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Static mappings for this application
STATION_IDS = {
    "Tel Aviv - Hashalom": "4600",
    "Beer Sheva - University": "7300",
    # Additional mappings can be added here
}

API_KEY = "5e64d66cf03f4547bcac5de2de06b566"
API_URL = "https://rail-api.rail.co.il/rjpa/api/v1/timetable/searchTrain"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "ocp-apim-subscription-key": API_KEY,
    "Content-Type": "application/json",
}

class RouteConfig(BaseModel):
    origin: str
    destination: str
    filename: str

class TrainPartModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    departureTime: str
    arrivalTime: str

class TrainRouteModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    trains: List[TrainPartModel]

class APIResponseModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    result: Dict[str, Any]

def get_train_schedule(origin_id: str, dest_id: str, date_str: str) -> List[TrainRouteModel]:
    payload = {
        "fromStation": origin_id,
        "toStation": dest_id,
        "date": date_str,
        "hour": "00:00",
        "scheduleType": "ByDeparture",
        "systemType": "2",
        "languageId": "English"
    }
    
    resp = requests.post(API_URL, json=payload, headers=HEADERS)
    resp.raise_for_status()
    
    try:
        data = APIResponseModel.model_validate(resp.json())
    except ValidationError as e:
        logging.error(f"Schema validation error: {e}")
        raise
        
    result = data.result
    if "travels" not in result:
        return []
        
    size = result.get('numOfResultsToShow', 0)
    index = result.get('startFromIndex', 0)
    travels = result['travels'][index: index + size]
    
    routes: List[TrainRouteModel] = []
    for t in travels:
        try:
            routes.append(TrainRouteModel.model_validate(t))
        except ValidationError:
            continue
            
    return routes

def format_duration(start_time: str, end_time: str) -> str:
    fmt = "%Y-%m-%dT%H:%M:%S"
    start_dt = datetime.datetime.strptime(start_time, fmt)
    end_dt = datetime.datetime.strptime(end_time, fmt)
    delta = end_dt - start_dt
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

def create_event(title: str, departure_time: str) -> Event:
    tz = pytz.timezone("Asia/Jerusalem")
    fmt = "%Y-%m-%dT%H:%M:%S"
    dep_dt = datetime.datetime.strptime(departure_time, fmt)
    dep_dt = tz.localize(dep_dt)
    
    event = Event()
    event.add("summary", title)  # type: ignore
    event.add("dtstart", dep_dt)  # type: ignore
    event.add("dtend", dep_dt) # Zero duration  # type: ignore
    return event

def process_route(route: RouteConfig, output_dir: Path):
    if route.origin not in STATION_IDS or route.destination not in STATION_IDS:
        logging.error(f"Unknown station names for route {route.filename}")
        return
        
    origin_id = STATION_IDS[route.origin]
    dest_id = STATION_IDS[route.destination]
    
    cal = Calendar()
    cal.add('prodid', '-//Israel Railways Calendar Generator//')  # type: ignore
    cal.add('version', '2.0')  # type: ignore
    
    today = datetime.date.today()
    lookahead_days = [30, 21, 14, 7, 4]
    
    for day_offset in range(31):
        target_date = today + datetime.timedelta(days=day_offset)
        date_str = target_date.strftime("%Y-%m-%d")
        
        routes_data = None
        for attempt_days in lookahead_days:
            if target_date > today + datetime.timedelta(days=attempt_days):
                continue
                
            try:
                routes_data = get_train_schedule(origin_id, dest_id, date_str)
                break
            except Exception as e:
                logging.warning(f"Failed to fetch for {date_str} with {attempt_days} days fallback: {e}")
                if attempt_days == 4:
                    logging.error(f"Critical error: Could not fetch schedules for {date_str} even at 4 days lookahead.")
        
        if not routes_data:
            continue
            
        first_train = routes_data[0]
        last_train = routes_data[-1]
        
        first_dep = first_train.trains[0].departureTime
        first_arr = first_train.trains[-1].arrivalTime
        first_dur = format_duration(first_dep, first_arr)
        cal.add_component(create_event(f"First Train ({first_dur})", first_dep))
        
        last_dep = last_train.trains[0].departureTime
        last_arr = last_train.trains[-1].arrivalTime
        last_dur = format_duration(last_dep, last_arr)
        cal.add_component(create_event(f"Last Train ({last_dur})", last_dep))
        
    out_file = output_dir / route.filename
    out_file.write_bytes(cal.to_ical())
    logging.info(f"Successfully generated {out_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="calendars", help="Directory to save the .ics files")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    routes_file = Path("routes.json")
    if not routes_file.exists():
        logging.error("routes.json not found")
        return
        
    try:
        raw_routes = json.loads(routes_file.read_text())
        routes = [RouteConfig.model_validate(r) for r in raw_routes]
    except Exception as e:
        logging.error(f"Failed to parse routes.json: {e}")
        return
        
    for r in routes:
        process_route(r, output_dir)

if __name__ == "__main__":
    main()
