import requests
import json
import re
import os

BASE_URL = "https://vavoo.to"
OUTPUT_FILE = "channels_world.m3u8"

# Keep these for categorization purposes
CATEGORY_KEYWORDS = {
    "Sport": ["sport", "dazn", "eurosport", "sky sport", "rai sport", "sport", "dazn", "tennis", "moto", "f1", "golf", "sportitalia", "sport italia", "solo calcio", "solocalcio"],
    "Film": ["primafila", "cinema", "movie", "film", "serie", "hbo", "fox"],
    "Notizie": ["news", "tg", "rai news", "sky tg", "tgcom"],
    "Intrattenimento": ["rai", "mediaset", "italia", "focus", "real time"],
    "Bambini": ["cartoon", "boing", "nick", "disney", "baby", "boing", "cartoon", "k2", "discovery k2", "nick", "super", "frisbee"],
    "Documentari": ["discovery", "geo", "history", "nat geo", "nature", "arte", "documentary"],
    "Musica": ["mtv", "vh1", "radio", "music"]
}

CATEGORY_KEYWORDS2 = {
    "Sky": ["sky cin", "tv 8", "fox", "comedy central", "animal planet", "nat geo", "tv8", "sky atl", "sky uno", "sky prima", "sky serie", "sky arte", "sky docum", "sky natu", "cielo", "history", "sky tg"],
    "Rai Tv": ["rai"],
    "Mediaset": ["mediaset", "canale 5", "rete 4", "italia", "focus", "tg com 24", "tgcom 24", "premium crime", "iris", "mediaset iris", "cine 34", "27 twenty seven", "27 twentyseven"],
    "Discovery": ["discovery", "real time", "investigation", "top crime", "wwe", "hgtv", "nove", "dmax", "food network", "warner tv"],
    "Rakuten": ["rakuten"]
}

# Channel logos dictionary kept intact
CHANNEL_LOGOS = {
    "sky uno": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-uno-it.png",
    "rai 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/rai-1-it.png",
    "comedy central": "https://yt3.googleusercontent.com/FPzu1EWCI54fIh2j9JEp0NOzwoeugjL4sZTQCdoxoQY1U4QHyKx2L3wPSw27IueuZGchIxtKfv8=s900-c-k-c0x00ffffff-no-rj"
}

def clean_channel_name(name):
    """Pulisce e modifica il nome del canale aggiungendo (V)."""
    name = re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)
    return f"{name} (V)"

def normalize_tvg_id(name):
    """Normalizza il tvg-id con solo la prima lettera maiuscola."""
    return " ".join(word.capitalize() for word in name.replace("(V)", "").strip().split())

def assign_category(name):
    """Assegna la categoria in base ai due dizionari."""
    name_lower = name.lower()
    category1 = next((category for category, keywords in CATEGORY_KEYWORDS.items() if any(keyword in name_lower for keyword in keywords)), "")
    category2 = next((category for category, keywords in CATEGORY_KEYWORDS2.items() if any(keyword in name_lower for keyword in keywords)), "")
    categories = ";".join(filter(None, [category1, category2]))
    return categories if categories else "Altro"

def extract_user_agent():
    return "VAVOO/2.6"

def fetch_channels():
    """Scarica i dati JSON dai canali di Vavoo."""
    try:
        response = requests.get(f"{BASE_URL}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download: {e}")
        return []

def filter_channels(channels):
    """Include tutti i canali senza filtro di nazionalità."""
    results = []
    seen = {}

    for ch in channels:
        # Rimosso il filtro sul country per includere tutti i canali
        clean_name = clean_channel_name(ch["name"])
        category = assign_category(clean_name)
        count = seen.get(clean_name, 0) + 1
        seen[clean_name] = count
        if count > 1:
            clean_name = f"{clean_name} ({count})"

        results.append((clean_name, f"{BASE_URL}/play/{ch['id']}/index.m3u8", category))

    return results

def save_m3u8(channels):
    """Salva i canali in un file M3U8."""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write('#EXTM3U url-tvg="http://epg-guide.com/it.gz"\n\n')
        user_agent = extract_user_agent()
        for name, url, category in channels:
            tvg_id = normalize_tvg_id(name)
            tvg_id_clean = re.sub(r"\s*\(\d+\)$", "", tvg_id)  # Rimuove numeri tra parentesi solo per tvg-id
            base_tvg_id = tvg_id.lower()  # Questo serve per cercare il logo nel dizionario

            logo = CHANNEL_LOGOS.get(base_tvg_id, "")

            f.write(f'#EXTINF:-1 tvg-id="{tvg_id_clean}" tvg-name="{tvg_id}" tvg-logo="{logo}" group-title="{category}",{name}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={user_agent}\n')
            f.write(f'#EXTVLCOPT:http-referrer={BASE_URL}/\n')
            f.write(f"{url}\n\n")

def main():
    channels = fetch_channels()
    filtered_channels = filter_channels(channels)
    save_m3u8(filtered_channels)
    print(f"File {OUTPUT_FILE} creato con successo!")

if __name__ == "__main__":
    main()
