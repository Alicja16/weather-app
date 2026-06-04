from datetime import datetime
import pprint
import requests
import os
import dotenv
from PIL import Image
from io import BytesIO
import customtkinter
from data import *

dotenv.load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
REQUEST_TIMEOUT = 10


def get_json(url):
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()

def get_parameter_value(api_item, parameter_name):
    param_path = Params[parameter_name][0]

    if len(param_path) == 1:
        value = api_item.get(param_path[0])
    else:
        value = api_item.get(param_path[0], {}).get(param_path[1])

    if value is None:
        value = 0

    return value


def check_coordinates(city_name: str, limit: int):
    url = f'http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit={limit}&appid={API_KEY}'
    try:
        response_json = get_json(url)
        list_of_responses = []
        for i in response_json:
            country = get_country_full_name(i.get("country"))
            location = [
                country,
                i.get("name"),
                i.get("state"),
                i.get("lat"),
                i.get("lon")
            ]
            list_of_responses.append(location)
        return list_of_responses

    except Exception as e:
        print(f"Location search error: {e}")
        return []


def get_country_full_name(country_code):
    if country_code is None:
        return None
    url = f"https://restcountries.com/v3.1/alpha/{country_code.upper()}"
    try:
        response_json = get_json(url)
        return response_json[0]["name"]["common"]

    except Exception as e:
        print(f"Country name error for {country_code}: {e}")
        return country_code



def download_weather_icon(icon_id, size=(50, 50)):
    try:
        url = f"https://openweathermap.org/img/wn/{icon_id}@2x.png"
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        img = img.resize(size)

        return img

    except Exception as e:
        print(f"Icon download error for {icon_id}: {e}")
        return None


def make_ctk_icon(pil_img):
    if pil_img is None:
        return None

    return customtkinter.CTkImage(
        light_image=pil_img,
        dark_image=pil_img,
        size=pil_img.size
    )


def preload_icons_for_result(result):
    icons = {}

    if result is None:
        return icons

    # główna ikona dla Current Weather
    main_icon_id = result.get("icon_id")
    if main_icon_id is not None:
        key = (main_icon_id, (100, 100))
        icons[key] = download_weather_icon(main_icon_id, size=(100, 100))

    # ikony w tabelach typu weather
    for values_group in result.get("values", []):
        for row in values_group:
            if len(row) > 2:
                icon_id = row[2]

                if isinstance(icon_id, str):
                    key = (icon_id, (50, 50))

                    if key not in icons:
                        icons[key] = download_weather_icon(icon_id, size=(50, 50))

    return icons



def get_current_weather(lat, lon, parameters: list):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    url_air = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    response_air = get_json(url_air)
    response_weather = get_json(url)

    img = None
    icon_id = None
    
    correct_value = []
    values_weather = []
    if "weather" in parameters:
        icon_id = response_weather.get('weather', [{}])[0].get('icon')
        values_weather.append(("weather", response_weather.get('weather', [{}])[0].get('description')))
    

    for p in parameters:
        if p not in ["air pollution", "weather"]:
            temp = Params[p][0]
            if len(temp) == 1: r = response_weather.get(temp[0])
            else: r = response_weather.get(temp[0], {}).get(temp[1])
            if r is None: r = 0
            values_weather.append((p, r))

    tabs = []
    if any(x != "air pollution" for x in parameters):
        tabs.append("Weather")
        correct_value.append(values_weather)

    quality_index = {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor"
    }
    values_air = []
    if "air pollution" in parameters:
        q_index = (response_air.get('list', [{}])[0].get('main', {}).get('aqi'))
        values_air.append(("Quality", quality_index[q_index]))
        components = response_air.get('list', [{}])[0].get('components')
        for c in components.items():
            values_air.append(c)
        tabs.append("Air Pollution")
        correct_value.append(values_air)

    print(correct_value)
    # result_window = templates.Result_ToplevelWindow(master, "Current Weather", tabs, correct_value, mode="Table", img=img)
    # result_window.im_primary_window()

    return {
        "title" : "Current Weather",
        "tabs" : tabs,
        "values" : correct_value,
        "mode" : "Table",
        "img": None,
        "icon_id": icon_id
    }


def get_hourly_forecast(lat, lon, parameters: list):
    url = f"https://pro.openweathermap.org/data/2.5/forecast/hourly?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = get_json(url)
    
    final_values = []

    if "weather" in parameters:
        weather = []
        w = response['list']
        for i in range(0,len(w),12):
            data = w[i].get('dt_txt')
            data = datetime.fromisoformat(data)
            desc = w[i].get('weather', [{}])[0].get('description')
            icon_id = w[i].get('weather', [{}])[0].get('icon')
            weather.append((data,desc,icon_id))
        final_values.append(weather)
    else: None

    for p in (x for x in parameters if x != "weather"):
        p_values = []
        for item in response.get("list", []):
            data = item.get("dt_txt")
            data = datetime.fromisoformat(data)
            value = get_parameter_value(item, p)
            p_values.append((data, value))
        final_values.append(p_values)

    print(f"{len(parameters)}, {len(final_values)}")

    return {
        "title" : "Hourly Forecast",
        "tabs" : parameters,
        "values" : final_values,
        "mode" : "Chart+Table",
        "img" : None
    }


def get_daily_parameter_value(api_item, parameter_name):
    if parameter_name == "temperature":
        value = api_item.get("temp", {}).get("day")

    elif parameter_name == "feels like (temp)":
        value = api_item.get("feels_like", {}).get("day")

    elif parameter_name == "pressure":
        value = api_item.get("pressure")

    elif parameter_name == "humidity":
        value = api_item.get("humidity")

    elif parameter_name == "wind speed":
        value = api_item.get("speed")

    elif parameter_name == "rain":
        value = api_item.get("rain")

    elif parameter_name == "snow":
        value = api_item.get("snow")

    elif parameter_name == "visibility":
        value = 0

    else:
        value = 0

    if value is None:
        value = 0

    return value
        


def get_daily_forecast(lat, lon, parameters: list, days: int = 16):
    url = f"https://api.openweathermap.org/data/2.5/forecast/daily?lat={lat}&lon={lon}&cnt={days}&appid={API_KEY}&units=metric"
    response = get_json(url)

    final_values = []

    if "weather" in parameters:
        weather = []

        for item in response.get("list", []):
            timestamp = item.get("dt")
            date = datetime.fromtimestamp(timestamp)
            desc = item.get("weather", [{}])[0].get("description")
            icon_id = item.get("weather", [{}])[0].get("icon")
            weather.append((date, desc, icon_id))
        final_values.append(weather)

    for p in (x for x in parameters if x != "weather"):
        p_values = []
        for item in response.get("list", []):
            timestamp = item.get("dt")
            date = datetime.fromtimestamp(timestamp)
            value = get_daily_parameter_value(item, p)
            p_values.append((date, value))
        final_values.append(p_values)

    return {
        "title": "Daily Forecast",
        "tabs": parameters,
        "values": final_values,
        "mode": "Chart+Table",
        "img": None
    }


def get_3_hourly_forecast(lat, lon, parameters: list, time_stamps: int = 40):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&cnt={time_stamps}&appid={API_KEY}&units=metric"
    response = get_json(url)

    final_values = []

    if "weather" in parameters:
        weather = []

        for item in response.get("list", []):
            data = item.get("dt_txt")
            data = datetime.fromisoformat(data)

            desc = item.get("weather", [{}])[0].get("description")
            icon_id = item.get("weather", [{}])[0].get("icon")

            weather.append((data, desc, icon_id))

        final_values.append(weather)

    for p in (x for x in parameters if x != "weather"):
        p_values = []
        for item in response.get("list", []):
            data = item.get("dt_txt")
            data = datetime.fromisoformat(data)
            value = get_parameter_value(item, p)
            p_values.append((data, value))
        final_values.append(p_values)

    return {
        "title": "3-Hour Forecast",
        "tabs": parameters,
        "values": final_values,
        "mode": "Chart+Table",
        "img": None
    }


def get_climatic_forecast(lat, lon, parameters: list):
    url = f"https://pro.openweathermap.org/data/2.5/forecast/climate?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = get_json(url)
    pprint.pprint(response)


def get_time_coords(lat, lon):
    url = f"https://timeapi.io/api/v1/time/current/coordinate?latitude={lat}&longitude={lon}"
    response = get_json(url)
    date = response["date"]
    time = response["time"]
    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S.%f")
    dt = dt.strftime("%d.%m.%Y %H:%M:%S")
    # pprint.pprint(response)
    return dt


