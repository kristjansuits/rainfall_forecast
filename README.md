library(httr)
library(jsonlite)
library(dplyr)

# Set your OpenWeatherMap API key
api_key <- 'c5124908eda328c67c34098af01d111c'

# Set latitude and longitude for your location
latitude <- 59.497
longitude <- 24.842

# Define file path for saving the CSV
csv_file <- 'weather_df.csv'

# Create a function to fetch and process weather data
fetch_weather_data <- function() {
  # Create an empty data frame to store weather data
  weather_df <- data.frame(
    ForecastDateTime = character(0),
    Temperature_C = numeric(0),
    Humidity_percent = numeric(0),
    Precipitation_mm = numeric(0),
    Status = character(0),  # New column for status
    TimeDifference_hr = numeric(0),  # New column for time difference in hours
    PrecipitationVolume_mm = numeric(0)  # New column for precipitation volume
  )

  # Make the API request for 3-hour forecasts for the next 5 days
  url <- sprintf(
    'https://api.openweathermap.org/data/2.5/forecast?lat=%s&lon=%s&appid=%s',
    latitude, longitude, api_key
  )
  response <- GET(url)

  if (http_type(response) == 'application/json') {
    weather_data <- content(response, 'parsed')

    # Extract and process the forecast data
    prev_precipitation_time <- NULL
    for (forecast in weather_data$list) {
      forecast_datetime <- as.POSIXct(forecast$dt, origin = '1970-01-01', tz = 'UTC')
      temperature_C <- forecast$main$temp - 273.15  # Convert from Kelvin to Celsius
      humidity_percent <- forecast$main$humidity
      precipitation_mm <- ifelse(is.null(forecast$rain), 0, forecast$rain['3h'])

      # Calculate time difference between this row and the previous one
      if (!is.null(prev_precipitation_time)) {
        time_diff <- as.numeric(difftime(forecast_datetime, prev_precipitation_time, units = 'hours'))
      } else {
        time_diff <- 0  # Set to 0 for the first row
      }
      
      # Ensure that precipitation_mm and time_diff are numeric
      precipitation_mm <- as.numeric(precipitation_mm)
      time_diff <- as.numeric(time_diff)
      
      # Calculate precipitation volume for this row
      precipitation_volume <- precipitation_mm * time_diff
      
      # Create a new row with column names matching weather_df
      new_row <- data.frame(
        ForecastDateTime = forecast_datetime,
        Temperature_C = temperature_C,
        Humidity_percent = humidity_percent,
        Precipitation_mm = precipitation_mm,
        Status = "Successful",  # Set status to "Successful" for successful retrieval
        TimeDifference_hr = time_diff,  # Add time difference column
        PrecipitationVolume_mm = precipitation_volume  # Add precipitation volume column
      )

      # Ensure column names of new_row match those of weather_df
      colnames(new_row) <- colnames(weather_df)

      # Add the extracted data to the data frame
      weather_df <- rbind(weather_df, new_row)
      
      # Update prev_precipitation_time for the next iteration
      prev_precipitation_time <- forecast_datetime
    }
  } else {
    cat('Error: Unable to retrieve weather data\n')

    # If retrieval is unsuccessful, set status to "Error"
    weather_df$Status <- "Error"
  }

  return(weather_df)
}

# Initialize a variable to keep track of the last retrieval time
last_retrieval_time <- Sys.time()

# Create a flag to check if rainfall over 1mm is anticipated
rainfall_anticipated <- FALSE

while (TRUE) {
  # Fetch weather data
  weather_data <- fetch_weather_data()
  
  # Check if rainfall over 1mm is anticipated in the next forecast
  if (any(weather_data$Precipitation_mm > 1)) {
    rainfall_anticipated <- TRUE
    cat('Rainfall over 1mm anticipated. Retrieving data in 3 hours.\n')
  } else {
    rainfall_anticipated <- FALSE
    cat('No significant rainfall anticipated. Retrieving data in 3 hours.\n')
  }

  # Save the data frame to the CSV file
  write.csv(weather_data, csv_file, row.names = FALSE)

  # Wait for 3 hours before the next retrieval
  Sys.sleep(3 * 60 * 60)  # Sleep for 3 hours

  # Check if rainfall is anticipated; if not, exit the loop
  if (!rainfall_anticipated) {
    cat('No significant rainfall anticipated. Exiting.\n')
    break
  }
}
