# israeli-rail-realtime-calendar
Serverless Python script that reads a list of target routes from a configuration file, fetches the train schedules for each route using the Israel Railways API, and generates a distinct RFC 5545 compliant .ics calendar file for each route. Each calendar will have two separate daily zero-duration events: the first and last train of the day.
