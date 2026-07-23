import argparse
import asyncio
import datetime
import itertools
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import pytz
from icalendar import Calendar, Event, vDatetime, vText
from pydantic import BaseModel, ConfigDict, ValidationError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Static mappings for this application (expanded from full list)
STATION_IDS = {
    "Tel Aviv - Hashalom": "4600",
    "Beer Sheva - University": "7300",
    "Tel Aviv-Savidor Center": "3700",
    "Hertsliya": "3500",
    "Bet Yehoshu'a": "3400",
    "Netanya": "3300",
    "Hadera-West": "3100",
    "Binyamina": "2800",
    "Caesarea-Pardes Hana": "2820",
    "Atlit": "2500",
    "Haifa-Bat Galim": "2200",
    "Hutsot HaMifrats": "1300",
    "Kiryat Hayim": "700",
    "Kiryat Motzkin": "1400",
    "Ako": "1500",
    "Haifa-Hof HaKarmel (Razi`el)": "2300",
    "Kfar Sava-Nordau (A.Kostyuk)": "8700",
    "Nahariya": "1600",
    "Jerusalem-Biblical Zoo": "6500",
    "Bet Shemesh": "6300",
    "Kiryat Gat": "7000",
    "Lod": "5000",
    "Be'er Sheva-North/University": "7300",
    "Kfar Habad": "4800",
    "Tel Aviv-HaShalom": "4600",
    "Haifa Center-HaShmona": "2100",
    "Ramla": "5010",
    "Rosh Ha'Ayin-North": "8800",
    "Be'er Ya'akov": "5300",
    "Rehovot (E. Hadar)": "5200",
    "Yavne-East": "5410",
    "Rishon LeTsiyon-HaRishonim": "9100",
    "Ashdod-Ad Halom (M.Bar Kochva)": "5800",
    "Petah Tikva-Segula": "4250",
    "Bnei Brak": "4100",
    "Tel Aviv-University": "3600",
    "Be'er Sheva-Center": "7320",
    "HaMifrats Central Station": "1220",
    "Tel Aviv-HaHagana": "4900",
    "Ben Gurion Airport": "8600",
    "Jerusalem-Malha": "6700",
    "Ashkelon": "5900",
    "Dimona": "7500",
    "Hod HaSharon-Sokolov": "9200",
    "Petah Tikva-Kiryat Arye": "4170",
    "Lod-Gane Aviv": "5150",
    "Lehavim-Rahat": "8550",
    "Pa'ate Modi'in": "300",
    "Modi'in-Center": "400",
    "Holon Junction": "4640",
    "Holon-Wolfson": "4660",
    "Bat Yam-Yoseftal": "4680",
    "Bat Yam-Komemiyut": "4690",
    "Rishon LeTsiyon-Moshe Dayan": "9800",
    "Yavne-West": "9000",
    "Sderot": "9600",
    "Netivot": "9650",
    "Ofakim": "9700",
    "Netanya-Sapir": "3310",
    "Yokne'am-Kfar Yehoshu'a": "1240",
    "Migdal Ha'emek-Kfar Barukh": "1250",
    "Afula R.Eitan": "1260",
    "Beit She'an": "1280",
    "Ahihud": "1820",
    "Karmiel": "1840",
    "Ra'anana West": "2940",
    "Ra'anana South": "2960",
    "Kiryat Malakhi – Yoav": "6150",
    "Jerusalem - Yitzhak Navon": "680",
    "Mazkeret Batya": "6900",
}

ID_TO_STATION = {v: k for k, v in STATION_IDS.items()}

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

class StopStationModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    stationId: int
    arrivalTime: str
    departureTime: str

class TrainPartModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    departureTime: str
    arrivalTime: str
    trainNumber: int
    orignStation: int
    destinationStation: int
    stopStations: List[StopStationModel] = []

class TrainRouteModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    trains: List[TrainPartModel]

class APIResponseModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    result: Dict[str, Any]

async def get_train_schedule(
    session: aiohttp.ClientSession,
    origin_id: str,
    dest_id: str,
    date_str: str,
    semaphore: asyncio.Semaphore
) -> List[TrainRouteModel]:
    payload = {
        "fromStation": origin_id,
        "toStation": dest_id,
        "date": date_str,
        "hour": "00:00",
        "scheduleType": "ByDeparture",
        "systemType": "2",
        "languageId": "English"
    }
    
    async with semaphore:
        async with session.post(API_URL, json=payload, headers=HEADERS) as resp:
            resp.raise_for_status()
            json_data = await resp.json()
            
            try:
                data = APIResponseModel.model_validate(json_data)
            except ValidationError as e:
                logging.error(f"Schema validation error: {e}")
                raise
                
            result = data.result
            if "travels" not in result:
                return []
                
            travels = result['travels']
            
            routes: List[TrainRouteModel] = []
            for t in travels:
                try:
                    routes.append(TrainRouteModel.model_validate(t))
                except ValidationError:
                    continue
                    
            return routes

def generate_event_description(train_route: TrainRouteModel, update_time: str) -> str:
    desc_lines = [f"Last update: {update_time}", ""]
    for train in train_route.trains:
        leg_origin = ID_TO_STATION.get(str(train.orignStation), str(train.orignStation))
        leg_dest = ID_TO_STATION.get(str(train.destinationStation), str(train.destinationStation))
        
        desc_lines.append(f"Train {train.trainNumber}:")
        
        dep_time = train.departureTime.split("T")[1][:5] if "T" in train.departureTime else train.departureTime
        desc_lines.append(f"- {dep_time} {leg_origin}")
        
        for stop in train.stopStations:
            stop_name = ID_TO_STATION.get(str(stop.stationId), str(stop.stationId))
            arr_time = stop.arrivalTime.split("T")[1][:5] if "T" in stop.arrivalTime else stop.arrivalTime
            desc_lines.append(f"- {arr_time} {stop_name}")
            
        dest_arr_time = train.arrivalTime.split("T")[1][:5] if "T" in train.arrivalTime else train.arrivalTime
        desc_lines.append(f"- {dest_arr_time} {leg_dest}")
        desc_lines.append("")
    
    return "\n".join(desc_lines).strip()

def format_duration(start_time: str, end_time: str) -> str:
    fmt = "%Y-%m-%dT%H:%M:%S"
    start_dt = datetime.datetime.strptime(start_time, fmt)
    end_dt = datetime.datetime.strptime(end_time, fmt)
    delta = end_dt - start_dt
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}h"

def create_event(title: str, departure_time: str, description: Optional[str] = None) -> Event:
    tz = pytz.timezone("Asia/Jerusalem")
    fmt = "%Y-%m-%dT%H:%M:%S"
    dep_dt = datetime.datetime.strptime(departure_time, fmt)
    dep_dt = tz.localize(dep_dt)
    
    event = Event()
    event["summary"] = vText(title)
    event["dtstart"] = vDatetime(dep_dt)
    event["dtend"] = vDatetime(dep_dt) # Zero duration
    if description:
        event["description"] = vText(description)
    return event

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
            event_desc = generate_event_description(train_route, update_time)
            cal_all.add_component(create_event(title, dep, description=event_desc))
            
        first_train = routes_data[0]
        last_train = routes_data[-1]
        
        first_dep = first_train.trains[0].departureTime
        first_arr = first_train.trains[-1].arrivalTime
        first_dur = format_duration(first_dep, first_arr)
        first_title = f"[{first_dur}] to {route.destination} (from {route.origin})"
        first_desc = generate_event_description(first_train, update_time)
        cal_first_last.add_component(create_event(first_title, first_dep, description=first_desc))
        
        last_dep = last_train.trains[0].departureTime
        last_arr = last_train.trains[-1].arrivalTime
        last_dur = format_duration(last_dep, last_arr)
        last_title = f"⚠️ Last [{last_dur}] to {route.destination} (from {route.origin})"
        last_desc = generate_event_description(last_train, update_time)
        cal_first_last.add_component(create_event(last_title, last_dep, description=last_desc))
        
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
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except Exception as e:
        logging.error(f"Failed to parse stations_config.json: {e}")
        return []
        
    active_stations = [name for name, is_active in config.items() if is_active]
    
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="calendars", help="Directory to save the .ics files")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    asyncio.run(main_async(output_dir))

if __name__ == "__main__":
    main()
