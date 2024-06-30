import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime, timedelta
import pytz

# Discord Configuration
DISCORD_TOKEN = "####"
RAIN_ALARM_CHANNEL_ID = ####  # Replace with your channel ID

# AccuWeather Configuration
ACCUWEATHER_API_KEY = "####"
DEFAULT_LOCATIONS = {
    "Quận 1": "3554433",
    "Quận 2": "3554434",    
    "Quận 3": "3554435",
    "Quận 4": "3554436",
    "Quận 5": "3554437",
    "Quận 6": "3554438",
    "Quận 7": "3554439",
    "Quận 8": "3554440",
    "Quận 9": "3554441",
    "Quận 10": "3554442",
    "Quận 11": "3554443",
    "Quận 12": "3554444",
    "Bình Tân": "3554446",
    "Bình Chánh": "429728",
    "Bình Thạnh": "1696411",
    "Gò Vấp": "425682",
    "Phú Nhuận": "418146",
    "Tân Bình": "416036",
    "Thủ Đức": "414495",
    # Add more locations as needed
}

# Helper Functions
def get_weather_forecast(location_key):
    url = f"http://dataservice.accuweather.com/forecasts/v1/hourly/1hour/{location_key}?apikey={ACCUWEATHER_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data[0] if data else None

def will_it_rain(forecast, threshold=50):  # Default threshold is 30%
    return forecast.get("PrecipitationProbability", 0) > threshold if forecast else False

def format_time(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    vietnam_timezone = pytz.timezone('Asia/Ho_Chi_Minh')  # Set Vietnam timezone
    dt_vn = dt.astimezone(vietnam_timezone)
    return dt_vn.strftime("%Y-%m-%d %H:%M:%S")

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

@tasks.loop(hours=1)  # Check every hour
async def check_rain(location_name="Quận 7", location_key=None, check_count=1):  # Added parameters
    channel = bot.get_channel(RAIN_ALARM_CHANNEL_ID)
    if not channel:
        print(f"Error: Could not find channel with ID {RAIN_ALARM_CHANNEL_ID}")
        return

    if not location_key:
        location_key = DEFAULT_LOCATIONS.get(location_name)

    if location_key:
        forecast = get_weather_forecast(location_key)
        if will_it_rain(forecast):
            message = f"Rain alert at {location_name} at {format_time(forecast['EpochDateTime'])}!"
            try:
                await channel.send(message)
            except discord.errors.Forbidden:
                print(f"Error: Missing permissions in channel {RAIN_ALARM_CHANNEL_ID}")
    else:
        print(f"Error: Location '{location_name}' not found in DEFAULT_LOCATIONS.")

    # Stop the task if it has run for the specified number of times
    if check_count > 1:
        check_rain.change_interval(count=check_count - 1)  # Decrement the counter
    else:
        check_rain.cancel()  # Stop the task

# Slash Command for Rain Check
@bot.command(name="rain", description="Check for rain at a specific location for 10 hours")
async def rain(ctx, location_name: str):
    location_key = DEFAULT_LOCATIONS.get(location_name)
    if location_key:
        await ctx.respond(f"Checking for rain at {location_name} for the next 10 hours...")
        check_rain.change_interval(hours=1, count=10)  # Check every hour for 10 times
        check_rain.start(location_name, location_key)  # Start the task with the specified location
    else:
        await ctx.respond(f"Location '{location_name}' not found.")


# Start the bot and the rain check task
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

    check_rain.start()  # Start the background task

bot.run(DISCORD_TOKEN)
