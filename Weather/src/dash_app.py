import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
from datetime import datetime

def create_dash_app(flask_app, weather_data):
    # Создаём Dash-приложение
    dash_app = dash.Dash(
        __name__,
        server=flask_app,
        url_base_pathname="/dashboard/"
    )

    dash_app.layout = html.Div([
        html.H1("Графики прогноза", style={"textAlign": "center"}),
        dcc.Dropdown(
            id='parameter-dropdown',
            options=[
                {'label': 'Минимальная температура', 'value': 'temperature_min'},
                {'label': 'Максимальная температура', 'value': 'temperature_max'},
                {'label': 'Скорость ветра', 'value': 'wind_speed'},
                {'label': 'Осадки', 'value': 'precipitation'},
            ],
            value='temperature_min',
            style={"width": "50%", "margin": "0 auto"}
        ),
        dcc.Graph(id='weather-graph')
    ])

    @dash_app.callback(
        Output('weather-graph', 'figure'),
        [Input('parameter-dropdown', 'value')]
    )
    def update_graph(selected_parameter):
        figure = go.Figure()

        # Проверяем, есть ли данные
        if not weather_data:
            print("[LOG] Weather data is empty.")
            figure.update_layout(
                title="Нет данных для отображения",
                xaxis_title="Дата",
                yaxis_title="Значение",
                hovermode="x unified"
            )
            return figure

        print(f"[LOG] Selected parameter: {selected_parameter}")
        print(f"[LOG] Weather data: {weather_data}")

        # Подготавливаем данные для графика
        for city_data in weather_data:
            city_name = city_data.get("city", "Unknown")
            try:
                print(f"[LOG] Processing city: {city_name}")
                print(f"[LOG] Forecasts for {city_name}: {city_data['forecasts']}")

                dates = [datetime.fromisoformat(forecast["date"]) for forecast in city_data["forecasts"]]
                values = [forecast.get(selected_parameter, 0) for forecast in city_data["forecasts"]]

                print(f"[LOG] Dates for {city_name}: {dates}")
                print(f"[LOG] Values for {city_name}: {values}")

                figure.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines+markers',
                    name=city_name
                ))
            except Exception as e:
                print(f"[ERROR] Failed to process data for {city_name}: {str(e)}")

        figure.update_layout(
            title=f"{selected_parameter.replace('_', ' ').capitalize()} по маршруту",
            xaxis={
                'title': 'Дата',
                'type': 'date',  # Ось времени
                'tickformat': '%d %b %Y'  # Формат дат
            },
            yaxis={
                'title': selected_parameter.replace('_', ' ').capitalize(),
            },
            hovermode='closest'
        )

        return figure

    return dash_app
