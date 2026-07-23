import datetime
from typing import Optional, Tuple, List
import pytz
from icalendar import Event, vDatetime, vText

from israeli_rail_calendar.models import TrainRouteModel
from israeli_rail_calendar.constants import ID_TO_STATION

def generate_event_description(train_route: TrainRouteModel, update_time: str) -> Tuple[str, str]:
    text_lines: List[str] = []
    html_lines: List[str] = []
    
    if train_route.travelMessages:
        for msg in train_route.travelMessages:
            if msg.message:
                text_lines.append(f"**{msg.message}**")
                html_lines.append(f"<b>{msg.message}</b><br>")
        text_lines.append("")
        html_lines.append("<br>")
        
    text_lines.extend([f"Last update: {update_time}", ""])
    html_lines.extend([f"Last update: {update_time}<br>", "<br>"])
    
    for train in train_route.trains:
        leg_origin = ID_TO_STATION.get(str(train.orignStation), str(train.orignStation))
        leg_dest = ID_TO_STATION.get(str(train.destinationStation), str(train.destinationStation))
        
        text_lines.append(f"Train {train.trainNumber}:")
        html_lines.append(f"Train {train.trainNumber}:<br>")
        
        dep_time = train.departureTime.split("T")[1][:5] if "T" in train.departureTime else train.departureTime
        orig_plat = f" (Platform {train.originPlatform})" if train.originPlatform is not None else ""
        
        text_lines.append(f"- {dep_time} {leg_origin}{orig_plat}")
        html_lines.append(f"- {dep_time} {leg_origin}{orig_plat}<br>")
        
        for stop in train.stopStations:
            stop_name = ID_TO_STATION.get(str(stop.stationId), str(stop.stationId))
            arr_time = stop.arrivalTime.split("T")[1][:5] if "T" in stop.arrivalTime else stop.arrivalTime
            stop_plat = f" (Platform {stop.platform})" if stop.platform is not None else ""
            
            text_lines.append(f"- {arr_time} {stop_name}{stop_plat}")
            html_lines.append(f"- {arr_time} {stop_name}{stop_plat}<br>")
            
        dest_arr_time = train.arrivalTime.split("T")[1][:5] if "T" in train.arrivalTime else train.arrivalTime
        dest_plat = f" (Platform {train.destPlatform})" if train.destPlatform is not None else ""
        
        text_lines.append(f"- {dest_arr_time} {leg_dest}{dest_plat}")
        html_lines.append(f"- {dest_arr_time} {leg_dest}{dest_plat}<br>")
        
        text_lines.append("")
        html_lines.append("<br>")
    
    return "\n".join(text_lines).strip(), "".join(html_lines).strip()

def format_duration(start_time: str, end_time: str) -> str:
    fmt = "%Y-%m-%dT%H:%M:%S"
    start_dt = datetime.datetime.strptime(start_time, fmt)
    end_dt = datetime.datetime.strptime(end_time, fmt)
    delta = end_dt - start_dt
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}h"

def create_event(title: str, departure_time: str, description: Optional[str] = None, html_description: Optional[str] = None) -> Event:
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
    if html_description:
        alt_desc = vText(html_description)
        alt_desc.params['FMTTYPE'] = vText('text/html')
        event["X-ALT-DESC"] = alt_desc
    return event
