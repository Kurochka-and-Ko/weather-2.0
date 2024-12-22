from flask import  request
import requests
from map_generator import generate_map
from flask import Flask, render_template
from dash_app import create_dash_app

app = Flask(__name__)
# Глобальная переменная для данных
weather_data = []

# Интеграция Dash
dash_app = create_dash_app(app, weather_data)

API_KEY = "na6tqTk3ur5GA488wJh8L4gQZlRsyQN7"

def get_additional_weather_details(location_key):
    """Получает данные о ветре и вероятности осадков."""
    try:
        url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
        params = {"apikey": API_KEY, "details": True}
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            print(f"[ERROR] Additional details API error: {response.status_code}")
            return {"error": f"Ошибка API дополнительных данных: {response.status_code}"}

        data = response.json()
        print(f"[LOG] Additional details response: {data}")

        if not data:
            return {"error": "Дополнительные данные не найдены"}

        return {
            "precipitation_probability": data[0].get("PrecipitationSummary", {}).get("Precipitation", {}).get("Metric", {}).get("Value", 0),
            "wind_speed": data[0].get("Wind", {}).get("Speed", {}).get("Metric", {}).get("Value", 0)
        }
    except Exception as e:
        print(f"[ERROR] Failed to fetch additional details: {str(e)}")
        return {"error": f"Ошибка: {str(e)}"}

def get_weather_forecast(city, days=1):
    try:
        # Получение location_key
        location_url = f"http://dataservice.accuweather.com/locations/v1/cities/search"
        location_params = {"apikey": API_KEY, "q": city}
        location_response = requests.get(location_url, params=location_params, timeout=10)

        if location_response.status_code != 200:
            return {"error": f"Ошибка API локации: {location_response.status_code}"}

        location_data = location_response.json()
        if not location_data:
            return {"error": f"Город '{city}' не найден"}

        location_key = location_data[0]["Key"]
        latitude = location_data[0]["GeoPosition"]["Latitude"]
        longitude = location_data[0]["GeoPosition"]["Longitude"]

        # Прогноз на 1 или 5 дней
        forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/{days}day/{location_key}"
        forecast_params = {"apikey": API_KEY, "metric": True}
        forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)

        if forecast_response.status_code != 200:
            return {"error": f"Ошибка API прогноза: {forecast_response.status_code}"}

        forecast_data = forecast_response.json()
        daily_forecasts = []

        for day in forecast_data["DailyForecasts"]:
            additional_details = get_additional_weather_details(location_key)

            daily_forecasts.append({
                "date": day["Date"],
                "temperature_min": day["Temperature"]["Minimum"]["Value"],
                "temperature_max": day["Temperature"]["Maximum"]["Value"],
                "precipitation": additional_details.get("precipitation_probability", 0),
                "wind_speed": additional_details.get("wind_speed", 0),
                "day_description": day.get("Day", {}).get("IconPhrase", ""),
                "night_description": day.get("Night", {}).get("IconPhrase", "")
            })

        return {
            "city": city,
            "lat": latitude,
            "lon": longitude,
            "forecasts": daily_forecasts
        }

    except Exception as e:
        print(f"[ERROR] Failed to fetch forecast for {city}: {str(e)}")
        return {"error": f"Ошибка: {str(e)}"}

@app.route('/results', methods=['POST'])
def results():
    global weather_data

    start_city = request.form.get('start_city')
    end_city = request.form.get('end_city')
    stop_cities = request.form.getlist('stop_city[]')
    days = int(request.form.get('days', 1))

    if not start_city or not end_city:
        return render_template('index.html', error="Введите начальный и конечный города!")

    cities = [start_city] + stop_cities + [end_city]

    # Список для накопления данных
    weather_data.clear()
    for city in cities:
        forecast = get_weather_forecast(city, days)
        if "error" in forecast:
            return render_template('index.html', error=f"Ошибка для города '{city}': {forecast['error']}")
        weather_data.append(forecast)

    # Генерация карты маршрута
    route_map = generate_map(weather_data)
    route_map.save("static/route_map.html")

    return render_template('route_result.html', forecasts=weather_data)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_city = request.form.get('start_city')
        end_city = request.form.get('end_city')
        stop_cities = request.form.getlist('stop_city[]')
        days = int(request.form.get('days', 1))

        if not start_city or not end_city:
            return render_template('index.html', error="Пожалуйста, заполните начальный и конечный города!")

        cities = [start_city] + stop_cities + [end_city]
        forecasts = []

        for city in cities:
            forecast = get_weather_forecast(city, days)
            if "error" in forecast:
                return render_template('index.html', error=f"Ошибка для города '{city}': {forecast['error']}")

            forecasts.append(forecast)

        # Генерация карты
        route_map = generate_map(forecasts)
        route_map.save("static/route_map.html")

        return render_template('route_result.html', forecasts=forecasts, days=days)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
