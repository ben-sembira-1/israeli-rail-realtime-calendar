# Israel Railways Calendar Generator

This project automatically generates standard `.ics` calendar files representing the daily schedules of Israel Railways trains. The calendars dynamically plot the first train and the last train of the day for specific routes.

## How to Import Your Calendars

Because these calendars are updated daily via GitHub Actions and published to GitHub Pages, you can **subscribe** to them in your favorite calendar app. By subscribing via URL (instead of downloading), your calendar app will automatically refresh and sync any schedule changes.

### 1. Get Your Calendar URL
Once GitHub Pages is enabled for your repository (pointing to the `gh-pages` branch), your calendar files will be accessible at:
```text
https://<your-github-username>.github.io/<repository-name>/hashalom_to_beersheva.ics
https://<your-github-username>.github.io/<repository-name>/beersheva_to_hashalom.ics
```

### 2. Subscribe in Google Calendar
1. Open [Google Calendar](https://calendar.google.com/) on your computer.
2. On the left side, next to **Other calendars**, click the **+** (Add) button.
3. Select **From URL**.
4. Paste the `.ics` URL.
5. Click **Add calendar**. 
*(It may take a few hours for Google Calendar to initially sync).*

### 3. Subscribe in Apple Calendar (Mac)
1. Open the **Calendar** app.
2. In the top menu, go to **File** > **New Calendar Subscription...** (or press `⌥⌘S`).
3. Paste the `.ics` URL and click **Subscribe**.
4. Set the **Auto-refresh** frequency (e.g., Every day) to ensure you always have the latest train times.

### 4. Subscribe in Apple Calendar (iOS / iPhone)
1. Go to **Settings** > **Calendar** > **Accounts**.
2. Tap **Add Account** > **Other** > **Add Subscribed Calendar**.
3. Paste the `.ics` URL and tap **Next**.
4. Tap **Save**.
