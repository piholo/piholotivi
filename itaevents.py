import xml.etree.ElementTree as ET
import random
import uuid
import json
import os
import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import time

# Constants
NUM_CHANNELS = 10000
DADDY_JSON_FILE = "daddyliveSchedule.json"
M3U8_OUTPUT_FILE = "filtered_events.m3u8"
EPG_OUTPUT_FILE = "filtered_events.xml"
LOGO = "https://raw.githubusercontent.com/cribbiox/eventi/refs/heads/main/ddsport.png"

mStartTime = 0
mStopTime = 0

# Filter keywords - eventi da includere (case insensitive)
EVENT_KEYWORDS = [
    "italy", 
    "atp", 
    "tennis", 
    "formula uno", 
    "f1", 
    "motogp", 
    "moto gp", 
    "volley"
]

# Headers for requests
Referer = "https://ilovetoplay.xyz/"
Origin = "https://ilovetoplay.xyz"
key_url = "https%3A%2F%2Fkey2.keylocking.ru%2F"

headers = {
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

def get_stream_link(dlhd_id, max_retries=3):
    """Get the stream link for a channel ID with retry mechanism"""
    print(f"Getting stream link for channel ID: {dlhd_id}...")

    base_timeout = 10  # Base timeout in seconds

    for attempt in range(max_retries):
        try:
            # Use timeout for all requests
            response = requests.get(
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

                response_key = requests.get(
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
                    stream_url = f"https://{server_key}new.iosplayer.ru/{server_key}/premium{dlhd_id}/mono.m3u8"
                    print(f"Stream URL retrieved for channel ID: {dlhd_id}")
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

# Remove existing files to ensure regeneration
for file in [M3U8_OUTPUT_FILE, EPG_OUTPUT_FILE, DADDY_JSON_FILE]:
    if os.path.exists(file):
        os.remove(file)

def generate_unique_ids(count, seed=42):
    """Generate unique IDs for channels"""
    random.seed(seed)
    return [str(uuid.UUID(int=random.getrandbits(128))) for _ in range(count)]

def loadJSON(filepath):
    """Load JSON data from a file"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def createSingleChannelEPGData(UniqueID, tvgName):
    """Create XML element for a channel in EPG"""
    xmlChannel = ET.Element('channel', id=UniqueID)
    xmlDisplayName = ET.SubElement(xmlChannel, 'display-name')
    xmlIcon = ET.SubElement(xmlChannel, 'icon', src=LOGO)

    xmlDisplayName.text = tvgName
    return xmlChannel

def createSingleEPGData(startTime, stopTime, UniqueID, channelName, description):
    """Create XML element for a programme in EPG"""
    programme = ET.Element('programme', start=f"{startTime} +0000", stop=f"{stopTime} +0000", channel=UniqueID)

    title = ET.SubElement(programme, 'title')
    desc = ET.SubElement(programme, 'desc')

    title.text = channelName
    desc.text = description

    return programme

def fetch_schedule_json(url):
    """Fetch JSON data from a URL"""
    try:
        print(f"Downloading schedule data from {url}...")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        with open(DADDY_JSON_FILE, 'wb') as file:
            file.write(response.content)
        
        print(f"Schedule data downloaded successfully to {DADDY_JSON_FILE}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading schedule: {e}")
        return False

def contains_keyword(event_name):
    """Check if event name contains any of the specified keywords (case insensitive)"""
    event_name_lower = event_name.lower()
    for keyword in EVENT_KEYWORDS:
        if keyword.lower() in event_name_lower:
            return True
    return False

def process_filtered_events():
    """Process only events that match specified keywords"""
    global channelCount, mStartTime, mStopTime
    processed_events = 0
    filtered_events = 0
    
    # Debug counters
    total_events = 0
    matched_by_keyword = {keyword: 0 for keyword in EVENT_KEYWORDS}
    
    # Initialize M3U8 file with header
    with open(M3U8_OUTPUT_FILE, 'w', encoding='utf-8') as file:
        file.write('#EXTM3U url-tvg="http://epg-guide.com/it.gz"\n\n')
    
    # Process events
    for day, day_data in dadjson.items():
        try:
            for sport_key, sport_events in day_data.items():
                for game in sport_events:
                    total_events += 1
                    event_name = game.get("event", "")
                    
                    # Check if event matches any keyword
                    if not contains_keyword(event_name):
                        continue
                    
                    # Count matches by keyword for reporting
                    for keyword in EVENT_KEYWORDS:
                        if keyword.lower() in event_name.lower():
                            matched_by_keyword[keyword] += 1
                    
                    filtered_events += 1
                    
                    for channel in game.get("channels", []):
                        try:
                            # Remove the "Schedule Time UK GMT" part and split the remaining string
                            clean_day = day.replace(" - Schedule Time UK GMT", "")
                            
                            # Remove ordinal suffixes (st, nd, rd, th)
                            clean_day = clean_day.replace("st ", " ").replace("nd ", " ").replace("rd ", " ").replace("th ", " ")
                            
                            # Split the cleaned string
                            day_parts = clean_day.split()
                            
                            if len(day_parts) >= 4:  # Make sure we have enough parts
                                day_num = day_parts[1]
                                month_name = day_parts[2]
                                year = day_parts[3]
                                
                                # Get time from game data
                                time_str = game.get("time", "00:00")
                                
                                # Convert time from UK to CET (add 1 hour)
                                time_parts = time_str.split(":")
                                if len(time_parts) == 2:
                                    hour = int(time_parts[0])
                                    minute = time_parts[1]
                                    # Add one hour to UK time
                                    hour_cet = (hour + 1) % 24
                                    # Ensure hour has two digits
                                    hour_cet_str = f"{hour_cet:02d}"
                                    # New time_str with CET time
                                    time_str_cet = f"{hour_cet_str}:{minute}"
                                else:
                                    # If time format is incorrect, keep original
                                    time_str_cet = time_str
                                
                                # Convert month name to number
                                month_map = {
                                    "January": "01", "February": "02", "March": "03", "April": "04",
                                    "May": "05", "June": "06", "July": "07", "August": "08",
                                    "September": "09", "October": "10", "November": "11", "December": "12"
                                }
                                month_num = month_map.get(month_name, "01")  # Default to January if not found
                                
                                # Ensure day has leading zero if needed
                                if len(day_num) == 1:
                                    day_num = f"0{day_num}"
                                
                                # Extract last two digits of year
                                year_short = year[2:4]  
                                
                                # Format as requested: "01/03/25 - 10:10" with CET time
                                formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_cet}"
                                
                                # Create proper datetime objects for EPG
                                date_str = f"{year}-{month_num}-{day_num} {time_str}:00"
                                start_date_utc = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                                
                                # Convert to Amsterdam timezone
                                amsterdam_timezone = pytz.timezone("Europe/Amsterdam")
                                start_date_amsterdam = start_date_utc.replace(tzinfo=pytz.UTC).astimezone(amsterdam_timezone)
                                
                                # Format for EPG
                                mStartTime = start_date_amsterdam.strftime("%Y%m%d%H%M%S")
                                mStopTime = (start_date_
