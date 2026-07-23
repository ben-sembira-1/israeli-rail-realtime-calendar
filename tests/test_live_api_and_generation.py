import datetime
import json
from pathlib import Path

import aiohttp
import pytest

from main import get_train_schedule, STATION_IDS, get_active_routes, process_route
import asyncio

@pytest.mark.asyncio
async def test_live_api_and_generation(tmp_path: Path):
    """
    End-to-End Live Integration Test for async permutation architecture.
    """
    config_file = Path("stations_config.json")
    assert config_file.exists(), "stations_config.json should exist in the repository root"
    
    # We load active routes based on the config file
    routes = get_active_routes()
    assert len(routes) > 0, "There should be at least one active route generated from stations_config.json"
    
    calendars_dir = tmp_path / "calendars"
    calendars_dir.mkdir()
    
    semaphore = asyncio.Semaphore(5)
    async with aiohttp.ClientSession() as session:
        # Just test the first few routes to avoid massive test times
        test_routes = routes[:3]
        tasks = [process_route(route, calendars_dir, session, semaphore) for route in test_routes]
        await asyncio.gather(*tasks)
        
        for route in test_routes:
            expected_file = calendars_dir / route.filename
            assert expected_file.exists(), f"Expected file {route.filename} was not created"
            
            content = expected_file.read_text()
            assert "BEGIN:VCALENDAR" in content, "ICS file must contain BEGIN:VCALENDAR"
            assert "DTSTART" in content, "ICS file must contain DTSTART"
            assert "Asia/Jerusalem" in content, "ICS file must specify Asia/Jerusalem timezone"

@pytest.mark.asyncio
async def test_pagination_fetches_all_data():
    """
    Test that we fetch all trains for the day.
    """
    origin_id = STATION_IDS["Tel Aviv - Hashalom"]
    dest_id = STATION_IDS["Beer Sheva - University"]
    
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    semaphore = asyncio.Semaphore(1)
    async with aiohttp.ClientSession() as session:
        routes = await get_train_schedule(session, origin_id, dest_id, tomorrow, semaphore)
    
    assert len(routes) > 5, f"Expected more than 5 trains, but got {len(routes)}."

@pytest.mark.asyncio
async def test_all_station_ids_valid():
    """
    Test that all stations in STATION_IDS are accepted by the live API without validation errors.
    """
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    semaphore = asyncio.Semaphore(5)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for name, station_id in STATION_IDS.items():
            dest_id = "4600" if station_id == "7300" else "7300"
            tasks.append(get_train_schedule(session, station_id, dest_id, tomorrow, semaphore))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result, (name, station_id) in zip(results, STATION_IDS.items()):
            if isinstance(result, Exception):
                pytest.fail(f"Station '{name}' with ID '{station_id}' failed API validation: {result}")
