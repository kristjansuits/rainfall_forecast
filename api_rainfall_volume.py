import requests
import time
import csv
import pandas as pd

# Set your OpenWeatherMap API key
api_key = 'c5124908eda328c67c34098af01d111c'

# Set latitude and longitude for your location
latitude = 59.497
longitude = 24.842

# Define file path for saving the CSV
csv_file = 'weather_df.csv'


# Create a function to fetch and process weather data
def fetch_weather_data():
    # Create an empty list to store weather data
    weather_data = []

    # Make the API request for 3-hour forecasts for the next 5 days
    url = f'https://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={api_key}'
    response = requests.get(url)

    if response.status_code == 200:
        weather_json = response.json()

        # Extract and process the forecast data
        prev_precipitation_time = None
        for forecast in weather_json['list']:
            forecast_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(forecast['dt']))
            temperature_C = forecast['main']['temp'] - 273.15  # Convert from Kelvin to Celsius
            humidity_percent = forecast['main']['humidity']
            precipitation_mm = forecast['rain']['3h'] if 'rain' in forecast else 0

            # Calculate time difference between this row and the previous one
            if prev_precipitation_time is not None:
                time_diff = (pd.to_datetime(forecast_datetime) - pd.to_datetime(
                    prev_precipitation_time)).total_seconds() / 3600.0
            else:
                time_diff = 0  # Set to 0 for the first row

            # Calculate precipitation volume for this row
            precipitation_volume = precipitation_mm * time_diff

            # Create a dictionary with keys matching the CSV columns
            new_row = {
                'ForecastDateTime': forecast_datetime,
                'Temperature_C': temperature_C,
                'Humidity_percent': humidity_percent,
                'Precipitation_mm': precipitation_mm,
                'Status': 'Successful',  # Set status to "Successful" for successful retrieval
                'TimeDifference_hr': time_diff,  # Add time difference column
                'PrecipitationVolume_mm': precipitation_volume  # Add precipitation volume column
            }

            # Add the extracted data to the list
            weather_data.append(new_row)

            # Update prev_precipitation_time for the next iteration
            prev_precipitation_time = forecast_datetime
    else:
        print('Error: Unable to retrieve weather data')

        # If retrieval is unsuccessful, set status to "Error"
        weather_data.append({'Status': 'Error'})

    return weather_data


# Initialize a variable to keep track of the last retrieval time
last_retrieval_time = time.time()

# Create a flag to check if rainfall over 1mm is anticipated
rainfall_anticipated = False

while True:
    # Fetch weather data
    weather_data = fetch_weather_data()

    # Check if rainfall over 1mm is anticipated in the next forecast
    if any(row['Precipitation_mm'] > 1 for row in weather_data):
        rainfall_anticipated = True
        print('Rainfall over 1mm anticipated. Retrieving data in 3 hours.')
    else:
        rainfall_anticipated = False
        print('No significant rainfall anticipated. Retrieving data in 3 hours.')

    # Save the data to the CSV file
    with open(csv_file, 'w', newline='') as csvfile:
        fieldnames = ['ForecastDateTime', 'Temperature_C', 'Humidity_percent', 'Precipitation_mm', 'Status',
                      'TimeDifference_hr', 'PrecipitationVolume_mm']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(weather_data)

    # Wait for 3 hours before the next retrieval
    time.sleep(3 * 60 * 60)  # Sleep for 3 hours

    # Check if rainfall is anticipated; if not, exit the loop
    if not rainfall_anticipated:
        print('No significant rainfall anticipated. Exiting.')
        break
