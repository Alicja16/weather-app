Weather_options = ["Current weather",
                   "Hourly forecast up to 4 days",
                   "Daily forecast up to 16 days",
                   "3-hour step forecast to 5 days",
                   "Climate forecast for 30 days"
                   ]

Params = {
    # name, name_in_API, unit
    "weather":[["icon", "description"], "--"],
    "temperature": [["main", "temp"], "°C"],
    "feels like (temp)": [["main", "feels_like"], "°C"],
    "pressure": [["main", "pressure"], "hPa"],
    "humidity": [["main", "humidity"], "%"],
    "wind speed": [["wind", "speed"], "metre/sec"],
    "visibility": [["visibility"], "metres"],
    "rain": [["rain", "1h"], "mm/h"],
    "snow": [["snow", "1h"], "mm/h"],
    "sunrise": [["sys", "sunrise"], "time"],
    "sunset": [["sys", "sunset"], "time"],
    "air pollution": []
}