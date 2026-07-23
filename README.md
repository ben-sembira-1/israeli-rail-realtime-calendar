# 🚆 Israel Railways Real-Time Calendar

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Active-success.svg)](https://ben-sembira-1.github.io/israeli-rail-realtime-calendar/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

> **A smart, automated calendar generator providing daily schedules of Israel Railways trains right to your favorite calendar app.**

This project automatically generates standard `.ics` calendar files representing the daily schedules of Israel Railways trains. The calendars dynamically plot the **first** and **last** trains of the day for specific routes. It updates automatically via GitHub Actions and is served through GitHub Pages.

---

## ✨ Available Calendars

Currently, the following train routes are actively generated and updated. You can subscribe to them directly using the provided URLs:

| Origin | Destination | Calendar Subscription URL |
| :--- | :--- | :--- |
| **Tel Aviv - Hashalom** | **Beer Sheva - University** | `https://ben-sembira-1.github.io/israeli-rail-realtime-calendar/hashalom_to_beersheva.ics` |
| **Beer Sheva - University** | **Tel Aviv - Hashalom** | `https://ben-sembira-1.github.io/israeli-rail-realtime-calendar/beersheva_to_hashalom.ics` |

---

## 🚀 How to Import Your Calendars

Because these calendars are updated daily and published to GitHub Pages, you should **subscribe** to them in your calendar app (instead of simply downloading the file). By subscribing, your app will automatically refresh and sync any schedule changes.

### 📅 Subscribe in Google Calendar
1. Open [Google Calendar](https://calendar.google.com/) on your computer.
2. On the left sidebar, click the **+** (Add) button next to **Other calendars**.
3. Select **From URL**.
4. Paste the `.ics` subscription URL from the table above.
5. Click **Add calendar**. 
*(Note: It may take a few hours for Google Calendar to complete the initial sync).*

### 🍏 Subscribe in Apple Calendar (Mac)
1. Open the **Calendar** app.
2. In the top menu, navigate to **File** > **New Calendar Subscription...** (or press `⌥⌘S`).
3. Paste the `.ics` subscription URL and click **Subscribe**.
4. Set the **Auto-refresh** frequency (e.g., *Every day*) to ensure you always have the latest train times.

### 📱 Subscribe in Apple Calendar (iOS / iPhone)
1. Go to **Settings** > **Calendar** > **Accounts**.
2. Tap **Add Account** > **Other** > **Add Subscribed Calendar**.
3. Paste the `.ics` subscription URL and tap **Next**.
4. Tap **Save**.

---

## 🛠️ Local Development

If you'd like to run the generator locally or add your own routes:

### Prerequisites
- Python 3.10+
- [Poetry](https://python-poetry.org/)

### Setup
1. Clone the repository:
   ```bash
   git clone git@github.com:ben-sembira-1/israeli-rail-realtime-calendar.git
   cd israeli-rail-realtime-calendar
   ```
2. Install dependencies:
   ```bash
   poetry install
   ```

### Running the Generator
```bash
poetry run python main.py --output-dir calendars
```
This will fetch the latest schedules for the routes defined in `routes.json` and generate `.ics` files in the `calendars/` directory.

### Adding New Routes
To add new routes, update `routes.json` with the new origin, destination, and desired filename. Make sure the station names map correctly in `main.py` (`STATION_IDS`).
```json
[
  {
    "origin": "Station A", 
    "destination": "Station B", 
    "filename": "station_a_to_station_b.ics"
  }
]
```

## 📄 License
This project is open-source and available under the terms of the LICENSE file.
