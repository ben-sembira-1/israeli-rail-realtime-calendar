import argparse
import asyncio
import datetime
import itertools
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict

import aiohttp
import pytz
from icalendar import Calendar, vText
from pydantic import RootModel, ValidationError, model_validator

from israeli_rail_calendar.constants import HEADERS, STATION_IDS
from israeli_rail_calendar.models import RouteConfig, TrainRouteModel
from israeli_rail_calendar.api_client import get_train_schedule
from israeli_rail_calendar.calendar_generator import create_event, format_duration, generate_event_description

class StationsConfig(RootModel[Dict[str, bool]]):
    @model_validator(mode="after")
    def check_stations_match(self) -> "StationsConfig":
        config_stations = set(self.root.keys())
        known_stations = set(STATION_IDS.keys())
        
        missing = known_stations - config_stations
        extra = config_stations - known_stations
        
        if missing or extra:
            err_msg: List[str] = []
            if missing:
                err_msg.append(f"Missing stations in config: {missing}")
            if extra:
                err_msg.append(f"Unknown stations in config: {extra}")
            raise ValueError(" | ".join(err_msg))
            
        return self

async def process_day_for_route(
    session: aiohttp.ClientSession,
    origin_id: str,
    dest_id: str,
    day_offset: int,
    semaphore: asyncio.Semaphore,
    today: datetime.date
) -> Optional[List[TrainRouteModel]]:
    
    target_date = today + datetime.timedelta(days=day_offset)
    date_str = target_date.strftime("%Y-%m-%d")
    lookahead_days = [30, 21, 14, 7, 4]
    
    for attempt_days in lookahead_days:
        if target_date > today + datetime.timedelta(days=attempt_days):
            continue
            
        try:
            return await get_train_schedule(session, origin_id, dest_id, date_str, semaphore)
        except Exception as e:
            logging.warning(f"Failed to fetch for {date_str} with {attempt_days} days fallback: {e}")
            if attempt_days == 4:
                logging.error(f"Critical error: Could not fetch schedules for {date_str} even at 4 days lookahead.")
    return None

async def process_route(
    route: RouteConfig, 
    output_dir: Path, 
    session: aiohttp.ClientSession, 
    semaphore: asyncio.Semaphore
):
    if route.origin not in STATION_IDS or route.destination not in STATION_IDS:
        logging.error(f"Unknown station names for route {route.filename}")
        return
        
    origin_id = STATION_IDS[route.origin]
    dest_id = STATION_IDS[route.destination]
    
    cal_first_last = Calendar()
    cal_first_last["prodid"] = vText('-//Israel Railways Calendar Generator (First/Last)//')
    cal_first_last["version"] = vText('2.0')
    cal_first_last["X-WR-CALNAME"] = vText(f"{route.origin} to {route.destination} (First & Last Trains)")
    
    cal_all = Calendar()
    cal_all["prodid"] = vText('-//Israel Railways Calendar Generator (All Trains)//')
    cal_all["version"] = vText('2.0')
    cal_all["X-WR-CALNAME"] = vText(f"{route.origin} to {route.destination} (All Trains)")
    
    today = datetime.date.today()
    update_time = datetime.datetime.now(pytz.timezone("Asia/Jerusalem")).strftime("%Y-%m-%d %H:%M:%S")
    # Process all 31 days concurrently
    tasks = [
        process_day_for_route(session, origin_id, dest_id, day_offset, semaphore, today)
        for day_offset in range(31)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for routes_data in results:
        if isinstance(routes_data, BaseException) or not routes_data:
            continue
            
        for i, train_route in enumerate(routes_data):
            dep = train_route.trains[0].departureTime
            arr = train_route.trains[-1].arrivalTime
            dur = format_duration(dep, arr)
            prefix = "⚠️ Last " if i == len(routes_data) - 1 else ""
            title = f"{prefix}[{dur}] to {route.destination} (from {route.origin})"
            event_desc, html_desc = generate_event_description(train_route, update_time)
            cal_all.add_component(create_event(title, dep, description=event_desc, html_description=html_desc))
            
        first_train = routes_data[0]
        last_train = routes_data[-1]
        
        first_dep = first_train.trains[0].departureTime
        first_arr = first_train.trains[-1].arrivalTime
        first_dur = format_duration(first_dep, first_arr)
        first_title = f"[{first_dur}] to {route.destination} (from {route.origin})"
        first_desc, first_html_desc = generate_event_description(first_train, update_time)
        cal_first_last.add_component(create_event(first_title, first_dep, description=first_desc, html_description=first_html_desc))
        
        last_dep = last_train.trains[0].departureTime
        last_arr = last_train.trains[-1].arrivalTime
        last_dur = format_duration(last_dep, last_arr)
        last_title = f"⚠️ Last [{last_dur}] to {route.destination} (from {route.origin})"
        last_desc, last_html_desc = generate_event_description(last_train, update_time)
        cal_first_last.add_component(create_event(last_title, last_dep, description=last_desc, html_description=last_html_desc))
        
    base_filename = route.filename
    if base_filename.endswith(".ics"):
        base_filename = base_filename[:-4]
        
    out_file_first_last = output_dir / f"{base_filename}.first_last.ics"
    out_file_first_last.write_bytes(cal_first_last.to_ical())
    
    out_file_all = output_dir / f"{base_filename}.all.ics"
    out_file_all.write_bytes(cal_all.to_ical())
    logging.info(f"Successfully generated {out_file_first_last} and {out_file_all}")

def get_active_routes() -> List[RouteConfig]:
    config_file = Path("stations_config.json")
    if not config_file.exists():
        logging.error("stations_config.json not found")
        return []
        
    try:
        raw_config = json.loads(config_file.read_text(encoding="utf-8"))
        config_model = StationsConfig.model_validate(raw_config)
    except ValidationError as e:
        logging.error(f"stations_config.json validation error: {e}")
        return []
    except Exception as e:
        logging.error(f"Failed to parse stations_config.json: {e}")
        return []
        
    active_stations = [name for name, is_active in config_model.root.items() if is_active]
    
    routes: List[RouteConfig] = []
    # Generate all directional permutations for active stations (where origin != dest)
    for origin, destination in itertools.permutations(active_stations, 2):
        safe_origin = origin.lower().replace(" ", "_").replace("-", "_").replace("/", "_").replace("'", "").replace("(", "_").replace(")", "_").replace('`', '_')
        safe_dest = destination.lower().replace(" ", "_").replace("-", "_").replace("/", "_").replace("'", "").replace("(", "_").replace(")", "_").replace('`', '_')
        
        routes.append(RouteConfig(
            origin=origin,
            destination=destination,
            filename=f"{safe_origin}_to_{safe_dest}.ics"
        ))
    return routes

async def main_async(output_dir: Path):
    routes = get_active_routes()
    if not routes:
        logging.info("No active routes to process.")
        return
        
    logging.info(f"Generating calendars for {len(routes)} routes...")
    
    # Restrict concurrent API requests to 20 to prevent DDOS / IP bans
    semaphore = asyncio.Semaphore(20)
    
    # Increase the connector limit so it doesn't bottleneck before the semaphore
    connector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        tasks = [
            process_route(route, output_dir, session, semaphore)
            for route in routes
        ]
        await asyncio.gather(*tasks)

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="calendars", help="Directory to save the .ics files")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    asyncio.run(main_async(output_dir))

if __name__ == "__main__":
    main()
