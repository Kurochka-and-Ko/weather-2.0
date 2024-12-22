import folium

def generate_map(cities):
    """Создаёт интерактивную карту маршрута."""
    route_map = folium.Map(location=[cities[0]["lat"], cities[0]["lon"]], zoom_start=6)

    for city in cities:
        folium.Marker(
            location=[city["lat"], city["lon"]],
            popup=f"{city['city']}: Макс. {city['forecasts'][0]['temperature_max']} °C, Мин. {city['forecasts'][0]['temperature_min']} °C",
            icon=folium.Icon(color="blue")
        ).add_to(route_map)

    folium.PolyLine(
        locations=[[city["lat"], city["lon"]] for city in cities],
        color="blue",
        weight=3
    ).add_to(route_map)

    return route_map
