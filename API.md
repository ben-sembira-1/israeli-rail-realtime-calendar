# Israel Railways API Documentation

This document describes the unofficial API used by the Israel Railways (Rakevet Yisrael) real-time application to fetch train timetables.

## Endpoint

**POST** `https://rail-api.rail.co.il/rjpa/api/v1/timetable/searchTrain`

## Headers

The API requires a subscription key and standard headers:

| Header | Value | Notes |
| :--- | :--- | :--- |
| `Content-Type` | `application/json` | |
| `ocp-apim-subscription-key` | `5e64d66cf03f4547bcac5de2de06b566` | Required. Static API key used by the official web/mobile clients. |
| `User-Agent` | (Standard Browser User-Agent) | Used to prevent blocks. |

## Request Body

The request payload is a JSON object with the routing and timing requirements:

```json
{
  "fromStation": "7300",
  "toStation": "4600",
  "date": "2026-07-23",
  "hour": "00:00",
  "scheduleType": "ByDeparture",
  "systemType": "2",
  "languageId": "English"
}
```

### Parameters

* **`fromStation`** (string): Origin station ID (e.g. `"7300"` for Be'er Sheva - University).
* **`toStation`** (string): Destination station ID (e.g. `"4600"` for Tel Aviv - Hashalom).
* **`date`** (string): Date of departure in `YYYY-MM-DD` format.
* **`hour`** (string): Time to start searching from in `HH:MM` format. Using `"00:00"` generally returns the entire day's schedule.
* **`scheduleType`** (string): `"ByDeparture"` (search forward from the specified hour) or `"ByArrival"` (search backwards so the user arrives by the specified hour).
* **`systemType`** (string): Internal system identifier (typically `"2"`).
* **`languageId`** (string): Language for text elements (e.g. `"English"`, `"Hebrew"`).

## Response Format

A successful request returns a JSON response containing the available route options under `result.travels`. Each element in `travels` represents one possible journey from origin to destination, which may comprise one or more train rides (legs).

### Example Structure

```json
{
  "result": {
    "travels": [
      {
        "departureTime": "2026-07-23T04:41:00",
        "arrivalTime": "2026-07-23T06:20:00",
        "freeSeats": 0,
        "travelMessages": [],
        "trains": [
          {
            "trainNumber": 616,
            "orignStation": 7300,
            "destinationStation": 4600,
            "originPlatform": 2,
            "destPlatform": 3,
            "predictedPctLoad": 6,
            "freeSeats": 0,
            "arrivalTime": "2026-07-23T06:20:00",
            "departureTime": "2026-07-23T04:41:00",
            "stopStations": [
              {
                "stationId": 9700,
                "arrivalTime": "2026-07-23T04:55:00",
                "departureTime": "2026-07-23T04:55:00",
                "platform": 1,
                "predictedPctLoad": 6
              }
              // ... additional intermediate stops
            ],
            "routeStations": [
              // Contains ALL stations on the train's route, including those outside the passenger's journey.
            ]
          }
          // ... additional train legs if a transfer is required
        ]
      }
    ]
  }
}
```

### Key Object Definitions

#### Travel Object (Journey)
Represents a full journey connecting the `fromStation` to `toStation`.
* `departureTime` / `arrivalTime`: Overall departure and arrival times for the journey.
* `trains`: Array of `Train` objects. If there are transfers, this array will have > 1 item.

#### Train Object (Leg)
Represents a single train segment.
* `trainNumber`: Official train identifier.
* `orignStation` / `destinationStation`: Station IDs for where the passenger boards and alights this specific train. Note the typo `orignStation` in the official API.
* `originPlatform` / `destPlatform`: Platform numbers.
* `predictedPctLoad`: Estimated crowdedness percentage.
* `departureTime` / `arrivalTime`: Departure and arrival time for this leg.
* `stopStations`: Array of stations the train will stop at *between* the passenger's origin and destination.

#### Stop Station Object
* `stationId`: The ID of the intermediate station.
* `arrivalTime` / `departureTime`: Schedule for this specific stop.
* `platform`: Platform number for the stop.
* `predictedPctLoad`: Estimated passenger load at this stop.
