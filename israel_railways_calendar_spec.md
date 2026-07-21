# Developer Specification: Israel Railways Multi-Calendar Generator

## 1. Core Objective
Build a serverless Python script that reads a list of target routes from a configuration file, fetches the train schedules for each route using the Israel Railways API, and generates a distinct RFC 5545 compliant `.ics` calendar file for each route. Each calendar must plot two separate daily zero-duration events: the first train of the day and the last train of the day.

## 2. Tech Stack
*   **Language:** Python 3.1x
*   **Dependency Management:** `poetry`
*   **Validation & Parsing:** `pydantic` (v2) for strict type checking of both the local JSON config and the external API responses.
*   **Static Analysis:** `pre-commit` running `pyright` (in strict mode).
*   **Dependencies:** `israel-rail-api` (or `requests` / `httpx`), `icalendar`, `pytz`.
*   **Execution & Hosting:** GitHub Actions & GitHub Pages.

## 3. Business Logic
### Configuration & Architecture
1.  Read a `routes.json` file at the root of the repository. Schema example:
    ```json
    [
      {
        "origin": "Tel Aviv - Hashalom", 
        "destination": "Beer Sheva - University", 
        "filename": "hashalom_to_beersheva.ics"
      }
    ]
    ```
2.  **Pydantic Config Model:** Define a `RouteConfig` Pydantic model to parse and validate `routes.json` at startup.

### Data Fetching & Pydantic Parsing (Per Route)
1.  Query the route for a specific date window. 
2.  **Pydantic API Model:** Pipe the raw JSON response from the Israel Railways API directly into a predefined Pydantic model (e.g., `class TrainScheduleResponse(BaseModel):`). This acts as an anti-corruption layer; if the railway changes their API schema, Pydantic will throw a `ValidationError` immediately.
3.  Extract the **first** train (earliest departure) and **last** train (latest departure).
4.  For both trains, calculate the journey duration (`Arrival Time` - `Departure Time`) formatted as a readable string (e.g., `1h 12m`).
5.  Create two separate calendar events for that day:
    *   **Event 1 Title:** `First Train ([Journey Duration])`
    *   **Event 2 Title:** `Last Train ([Journey Duration])`
    *   **Event Timing:** Both `DTSTART` and `DTEND` must be set to the exact **departure time** (zero-duration event).
6.  Apply the `Asia/Jerusalem` timezone to all `datetime` objects.
7.  Save the `.ics` file to the specified output directory using the `filename` specified in the config. *(Note: Code should be structured so the output directory can be passed as an argument, defaulting to the root directory for production).*

### Lookahead & Graceful Fallback
1.  Attempt to fetch **30 days** in advance.
2.  If the API fails or returns empty lists (gracefully caught, not a Pydantic schema error), fallback to **21 days** -> **14 days** -> **7 days** -> **4 days**.
3.  If 4 days fails, log a critical error and crash the execution for that specific route.

## 4. Code Quality & Static Analysis
### Pyright & Pre-commit
*   Configure `pyproject.toml` to enforce Pyright strict mode:
    ```toml
    [tool.pyright]
    typeCheckingMode = "strict"
    ```
*   Create a `.pre-commit-config.yaml` at the repository root containing the `pyright` hook:
    ```yaml
    repos:
      - repo: https://github.com/RobertCraigie/pyright-python
        rev: v1.1.391
        hooks:
          - id: pyright
            additional_dependencies: ["pydantic", "icalendar", "pytz", "requests"]
    ```

## 5. CI/CD Orchestration (GitHub)
Split the pipeline into two separate GitHub Actions workflow files to separate testing from deployment.

### Workflow 1: `ci-test.yml` (Trigger: Push to `master` / PRs)
1. Checkout repository.
2. Setup Python & install Poetry.
3. Run `poetry install`.
4. Run `poetry run pre-commit run --all-files` (Executes Pyright strict type-checking).
5. Run `poetry run pytest` (Executes the live API integration test and `.ics` generation verification).

### Workflow 2: `update-calendars.yml` (Trigger: CRON schedule `0 23 * * *`)
1. Checkout repository.
2. Setup Python & install Poetry.
3. Run `poetry install --only main`.
4. Run `poetry run python main.py` to generate the `.ics` files in the root directory.
5. Commit and push the generated `*.ics` files to the `gh-pages` branch.

## 6. Testing Plan
Use a single, robust integration test to ensure the external API contract remains intact and the calendar generation logic works end-to-end without polluting the repository with test files.

### End-to-End Live Integration Test
*   **File:** `tests/test_live_api_and_generation.py`
*   **Behavior:** 
    1. Read the production `routes.json` file using the `RouteConfig` Pydantic model.
    2. Inject `pytest`'s built-in `tmp_path` fixture (a secure, temporary directory that gets destroyed after the test).
    3. Iterate over **every** start-destination pair defined in the config.
    4. Call the main business logic function for a single date (e.g., "tomorrow"), instructing it to output the `.ics` file into `tmp_path` instead of the repository root.
*   **Assertions:**
    1. **API/Pydantic:** The live network request succeeds and automatically validates against the Pydantic models (implicitly failing the test on a schema change).
    2. **File Creation:** Assert the `.ics` file was successfully written to the `tmp_path` using the `filename` from the config.
    3. **Content Structure:** Open the generated file from `tmp_path` and verify it contains standard RFC 5545 calendar markers (e.g., `BEGIN:VCALENDAR`, `DTSTART`, and `Asia/Jerusalem`).
