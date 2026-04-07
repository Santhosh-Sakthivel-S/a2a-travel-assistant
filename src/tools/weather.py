import requests
from strands import tool
from src.config.settings import settings, logger

@tool
def fetch_weather(location: str) -> str:
    """Fetch the current weather for a specific location using OpenWeatherMap API."""
    if not settings.OPENWEATHER_API_KEY:
        logger.error("OPENWEATHER_API_KEY is missing.")
        return f"System Error: Cannot fetch weather for {location} due to missing API key."

    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={settings.OPENWEATHER_API_KEY}&units=metric"
    
    try:
        logger.info(f"Fetching weather data for: {location}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return f"Current weather in {location}: {temp}°C, {desc}."
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API request failed for {location}: {e}")
        return f"Could not fetch weather for {location}. Please proceed with general planning."