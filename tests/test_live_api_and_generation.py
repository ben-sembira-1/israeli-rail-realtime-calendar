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
