import json
from pathlib import Path

from main import RouteConfig, process_route

def test_live_api_and_generation(tmp_path: Path):
    """
    End-to-End Live Integration Test
    1. Read the production routes.json
    2. Inject tmp_path fixture
    3. Call process_route for each route
    4. Assert the .ics file is successfully written with RFC 5545 calendar markers
    """
    routes_file = Path("routes.json")
    assert routes_file.exists(), "routes.json should exist in the repository root"
    
    raw_routes = json.loads(routes_file.read_text())
    routes = [RouteConfig.model_validate(r) for r in raw_routes]
    assert len(routes) > 0, "There should be at least one route in routes.json"
    
    # Process each route, outputting to the tmp_path directory
    calendars_dir = tmp_path / "calendars"
    calendars_dir.mkdir()
    
    for route in routes:
        process_route(route, calendars_dir)
        
        # Verify file creation
        expected_file = calendars_dir / route.filename
        assert expected_file.exists(), f"Expected file {route.filename} was not created"
        
        # Verify content structure
        content = expected_file.read_text()
        assert "BEGIN:VCALENDAR" in content, "ICS file must contain BEGIN:VCALENDAR"
        assert "DTSTART" in content, "ICS file must contain DTSTART"
        assert "Asia/Jerusalem" in content, "ICS file must specify Asia/Jerusalem timezone"

import datetime
from main import get_train_schedule, STATION_IDS

def test_pagination_fetches_all_data():
    """
    Test that we fetch all trains for the day, not just the first page (5 trains).
    """
    origin_id = STATION_IDS["Tel Aviv - Hashalom"]
    dest_id = STATION_IDS["Beer Sheva - University"]
    
    # Test for tomorrow to avoid end-of-day edge cases where there might legitimately be few trains left today
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    routes = get_train_schedule(origin_id, dest_id, tomorrow)
    
    # If the pagination bug is present, this would be exactly 5.
    # Israel Railways typically has > 20 trains a day between these major stations.
    assert len(routes) > 5, f"Expected more than 5 trains for a full day, but got {len(routes)}. Pagination bug may be present."

import time

def test_all_station_ids_valid():
    """
    Test that all stations in STATION_IDS are accepted by the live API without validation errors.
    """
    # Use tomorrow's date
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    # We will test each station as a "fromStation" against a known good "toStation" (e.g. 7300 Beer Sheva)
    # If the station IS 7300, we use 4600 as the "toStation"
    for name, station_id in STATION_IDS.items():
        dest_id = "4600" if station_id == "7300" else "7300"
        try:
            # We don't care about the result length, just that it doesn't raise a 400 validation error
            get_train_schedule(station_id, dest_id, tomorrow)
        except Exception as e:
            pytest.fail(f"Station '{name}' with ID '{station_id}' failed API validation: {e}")
        
        # small sleep to avoid rate limiting
        time.sleep(0.1)
