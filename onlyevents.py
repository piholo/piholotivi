import random
import uuid
import fetcher
import json
import os
import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import time
# Costanti
NUM_CHANNELS = 10000
DADDY_JSON_FILE = "daddyliveSchedule.json"
M3U8_OUTPUT_FILE = "onlyevents.m3u8"
LOGO = "https://raw.githubusercontent.com/cribbiox/eventi/refs/heads/main/ddsport.png"

mStartTime = 0
mStopTime = 0

# Headers and related constants from the first code block (assuming these are needed for requests)
Referer = "https://ilovetoplay.xyz/"
Origin = "https://ilovetoplay.xyz"
key_url = "https%3A%2F%2Fkey2.keylocking.ru%2F"

headers = { # **Define base headers *without* Referer and Origin**
    "Accept": "*/*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,ru;q=0.5",
    "Priority": "u=1, i",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "Sec-Ch-UA-Mobile": "?0",
    "Sec-Ch-UA-Platform": "Windows",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Storage-Access": "active",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}
# Simulated client and credentials - Replace with your actual client and credentials if needed
client = requests # Using requests as a synchronous client

def get_stream_link(dlhd_id, event_name="", channel_name="", max_retries=3):
    print(f"Getting stream link for channel ID: {dlhd_id} - {event_name} on {channel_name}...")

    base_timeout = 10  # Base timeout in seconds

    for attempt in range(max_retries):
        try:
            # Use timeout for all requests
            response = client.get(
                f"https://daddylive.mp/embed/stream-{dlhd_id}.php",
                headers=headers,
                timeout=base_timeout
            )
            response.raise_for_status()
            response.encoding = 'utf-8'

            response_text = response.text
            if not response_text:
                print(f"Warning: Empty response received for channel ID: {dlhd_id} (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    # Calculate exponential backoff with jitter
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    continue
                return None

            soup = BeautifulSoup(response_text, 'html.parser')
            iframe = soup.find('iframe', id='thatframe')

            if iframe is None:
                print(f"Debug: iframe with id 'thatframe' NOT FOUND for channel ID {dlhd_id} (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    continue
                return None

            if iframe and iframe.get('src'):
                real_link = iframe.get('src')
                parent_site_domain = real_link.split('/premiumtv')[0]
                server_key_link = (f'{parent_site_domain}/server_lookup.php?channel_id=premium{dlhd_id}')
                server_key_headers = headers.copy()
                server_key_headers["Referer"] = f"https://newembedplay.xyz/premiumtv/daddylivehd.php?id={dlhd_id}"
                server_key_headers["Origin"] = "https://newembedplay.xyz"
                server_key_headers["Sec-Fetch-Site"] = "same-origin"

                response_key = client.get(
                    server_key_link,
                    headers=server_key_headers,
                    allow_redirects=False,
                    timeout=base_timeout
                )

                # Add adaptive delay between requests
                time.sleep(random.uniform(1, 3))
                response_key.raise_for_status()

                try:
                    server_key_data = response_key.json()
                except json.JSONDecodeError:
                    print(f"JSON Decode Error for channel ID {dlhd_id}: Invalid JSON response: {response_key.text[:100]}...")
                    if attempt < max_retries - 1:
                        sleep_time = (2 ** attempt) + random.uniform(0, 1)
                        print(f"Retrying in {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                        continue
                    return None

                if 'server_key' in server_key_data:
                    server_key = server_key_data['server_key']
                    stream_url = f"https://{server_key}new.newkso.ru/{server_key}/premium{dlhd_id}/mono.m3u8"
                    print(f"Stream URL retrieved for channel ID: {dlhd_id} - {event_name} on {channel_name}")
                    return stream_url
                else:
                    print(f"Error: 'server_key' not found in JSON response from {server_key_link} (attempt {attempt+1}/{max_retries})")
                    if attempt < max_retries - 1:
                        sleep_time = (2 ** attempt) + random.uniform(0, 1)
                        print(f"Retrying in {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                        continue
                    return None
            else:
                print(f"Error: iframe with id 'thatframe' found, but 'src' attribute is missing for channel ID {dlhd_id} (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    continue
                return None

        except requests.exceptions.Timeout:
            print(f"Timeout error for channel ID {dlhd_id} (attempt {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                continue
            return None

        except requests.exceptions.RequestException as e:
            print(f"Request Exception for channel ID {dlhd_id} (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                continue
            return None

        except Exception as e:
            print(f"General Exception for channel ID {dlhd_id} (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                continue
            return None

    return None  # If we get here, all retries failed

# Rimuove i file esistenti per garantirne la rigenerazione
for file in [M3U8_OUTPUT_FILE]: # daddyLiveChannelsFileName kept for file removal consistency, but not used  tolto (, DADDY_JSON_FILE)
    if os.path.exists(file):
        os.remove(file)

# Funzioni prima parte dello script
def generate_unique_ids(count, seed=42):
    random.seed(seed)
    return [str(uuid.UUID(int=random.getrandbits(128))) for _ in range(count)]

def loadJSON(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)


def addChannelsByLeagueSport():
    global channelCount
    processed_schedule_channels = 0  # Counter for schedule channels

    # Define categories to exclude - these must match exact category names in JSON
    excluded_categories = [
        "TV Shows", "Cricket", "Aussie rules", "Snooker", "Baseball",
        "Biathlon", "Cross Country", "Horse Racing", "Ice Hockey",
        "Waterpolo", "Golf", "Darts", "Cycling",
        "TV Shows</span>", "Cricket</span>", "Aussie rules</span>", "Snooker</span>", "Baseball</span>",
        "Biathlon</span>", "Cross Country</span>", "Horse Racing</span>", "Ice Hockey</span>",
        "Waterpolo</span>", "Golf</span>", "Darts</span>", "Cycling</span>", "Handball</span>", "Squash</span>"
    ]

    # Debug counters
    total_events = 0
    skipped_events = 0
    category_stats = {}  # To track how many events per category

    # First pass to gather category statistics
    for day, day_data in dadjson.items():
        try:
            for sport_key, sport_events in day_data.items():
                # Clean the sport key by removing HTML tags
                clean_sport_key = sport_key.replace("</span>", "").replace("<span>", "").strip()

               #sport_key = sport_key.replace("</span>", "").replace("<span>", "").strip()
                if clean_sport_key not in category_stats:
                    category_stats[clean_sport_key] = 0
                category_stats[clean_sport_key] += len(sport_events)
        except (KeyError, TypeError):
            pass  # Skip problematic days

    # Print category statistics
    print("\n=== Available Categories ===")
    for category, count in sorted(category_stats.items()):
        excluded = "EXCLUDED" if category in excluded_categories else ""
        print(f"{category}: {count} events {excluded}")
    print("===========================\n")

    # Second pass to process events
    for day, day_data in dadjson.items():
        try:
            for sport_key, sport_events in day_data.items():
                # Clean the sport key by removing HTML tags
                #sport_key = sport_key.replace("</span>", "").replace("<span>", "").strip()
                clean_sport_key = sport_key.replace("</span>", "").replace("<span>", "").strip()

                total_events += len(sport_events)

                # Skip only exact category matches
                if clean_sport_key in excluded_categories:
                    skipped_events += len(sport_events)
                    continue

                for game in sport_events:
                    for channel in game.get("channels", []):
                        try:
                            # Clean and format day
                            clean_day = day.replace(" - Schedule Time UK GMT", "").replace("st ", " ").replace("nd ", " ").replace("rd ", " ").replace("th ", " ")
                            day_parts = clean_day.split()
                            
                            # Handle various date formats
                            if len(day_parts) >= 4:
                                # Standard format: Weekday Month Day Year
                                day_num = day_parts[1]
                                month_name = day_parts[2]
                                year = day_parts[3]
                            elif len(day_parts) == 3:
                                # Format: Weekday Day Year or Day Month Year
                                if day_parts[1].isdigit() and day_parts[2].isdigit() and len(day_parts[2]) == 4:
                                    # Weekday Day Year (missing month)
                                    day_num = day_parts[1]
                                    # Get current month for Rome timezone
                                    rome_tz = pytz.timezone('Europe/Rome')
                                    current_month = datetime.datetime.now(rome_tz).strftime('%B')
                                    month_name = current_month
                                    year = day_parts[2]
                                else:
                                    # Assume Day Month Year
                                    day_num = day_parts[0]
                                    month_name = day_parts[1]
                                    year = day_parts[2]
                            else:
                                # Use current date from Rome timezone
                                rome_tz = pytz.timezone('Europe/Rome')
                                now = datetime.datetime.now(rome_tz)
                                day_num = now.strftime('%d')
                                month_name = now.strftime('%B')
                                year = now.strftime('%Y')
                                print(f"Using current Rome date for: {clean_day}")
                            
                            # Get time from game data
                            time_str = game.get("time", "00:00")
                            
                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month_num = month_map.get(month_name, "01")
                            
                            # Ensure day has leading zero if needed
                            if len(str(day_num)) == 1:
                                day_num = f"0{day_num}"
                            
                            # Create formatted date time
                            year_short = str(year)[-2:]
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            
                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            # Fallback to current Rome time
                            rome_tz = pytz.timezone('Europe/Rome')
                            now = datetime.datetime.now(rome_tz)
                            day_num = now.strftime('%d')
                            month_num = now.strftime('%m')
                            year_short = now.strftime('%y')
                            time_str_rome = now.strftime('%H:%M')
                            formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_rome}"
                            print(f"Using fallback Rome date/time: {formatted_date_time}")

                            # Get time from game data
                            time_str = game.get("time", "00:00")

                            # Convert time to Rome timezone (CET/CEST)
                            rome_tz = pytz.timezone('Europe/Rome')
                            uk_tz = pytz.timezone('Europe/London')
                            
                            # Parse the time
                            time_parts = time_str.split(":")
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Create datetime objects
                                now = datetime.datetime.now()
                                uk_time = uk_tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute))
                                rome_time = uk_time.astimezone(rome_tz)
                                
                                # Format for display
                                time_str_rome = rome_time.strftime("%H:%M")
                            else:
                                # If time format is invalid, use current Rome time
                                now_rome = datetime.datetime.now(rome_tz)
                                time_str_rome = now_rome.strftime("%H:%M")
                            
                            # Month map for conversion
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August
