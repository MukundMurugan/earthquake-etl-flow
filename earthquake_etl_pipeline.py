import prefect
from prefect import task, flow
import requests
import pandas as pd
import pytz
from datetime import datetime

@task
def fetch_earthquake_data(url):
    response = requests.get(url)
    data = response.json()
    
    features = data['features']
    earthquakes = []
    for feature in features:
        properties = feature['properties']
        geometry = feature['geometry']
        utc_time = pd.to_datetime(properties['time'], unit='ms')
        local_time = utc_time.tz_localize('UTC').tz_convert(pytz.timezone('America/Los_Angeles'))  # Convert to local timezone
        earthquakes.append({
            "place": properties['place'],
            "magnitude": properties['mag'],
            "time_utc": utc_time,
            "time_local": local_time,
            "latitude": geometry['coordinates'][1],
            "longitude": geometry['coordinates'][0]
        })
    
    return pd.DataFrame(earthquakes)

@task
def fetch_realtime_data():
    realtime_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
    return fetch_earthquake_data(realtime_url)

@task
def fetch_historical_data():
    historical_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"
    return fetch_earthquake_data(historical_url)

@flow
def earthquake_etl_flow():
    realtime_earthquake_data = fetch_realtime_data()
    historical_earthquake_data = fetch_historical_data()
    
    return realtime_earthquake_data, historical_earthquake_data
from prefect.deployments import Deployment

deployment = Deployment.build_from_flow(
    earthquake_etl_flow,
    name="Earthquake ETL Flow",
    schedule="0 * * * *", 
)

deployment.apply()
earthquake_etl_flow.submit()

