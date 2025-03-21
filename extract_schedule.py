from playwright.sync_api import sync_playwright
import time
import os
import json
from datetime import datetime

def extract_schedule_container():
    url = "https://daddylive.mp/"
    html_output = "main_schedule_container.html"
    json_output = "schedule_data.json"
    
    print(f"Accesso alla pagina {url} per estrarre il main-schedule-container...")
    
    with sync_playwright() as p:
        # Lancia un browser Chromium in background
        browser = p.chromium.launch(headless=True)
        
        # Configura il contesto con un user agent realistico
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Crea una nuova pagina
        page = context.new_page()
        
        try:
            # Naviga alla URL
            print("Navigazione alla pagina...")
            page.goto(url)
            
            # Attendi per il caricamento dinamico del contenuto
            print("Attesa per il caricamento completo...")
            page.wait_for_timeout(10000)  # 10 secondi
            
            # Estrai il contenuto HTML
            schedule_content = page.evaluate("""() => {
                const container = document.getElementById('main-schedule-container');
                return container ? container.outerHTML : '';
            }""")
            
            if not schedule_content:
                print("AVVISO: main-schedule-container trovato ma è vuoto o non presente!")
                return False
            
            # Salva l'HTML
            with open(html_output, "w", encoding="utf-8") as f:
                f.write(schedule_content)
                
            print(f"Contenuto HTML salvato in {html_output} ({len(schedule_content)} caratteri)")
            
            # Opzionale: estrai i dati in formato JSON per ulteriore elaborazione
            schedule_data = page.evaluate("""() => {
                try {
                    const matches = [];
                    const items = document.querySelectorAll('.item');
                    
                    items.forEach(item => {
                        // Adatta questo selettore in base alla struttura effettiva della pagina
                        const time = item.querySelector('.time')?.textContent.trim() || '';
                        const teams = item.querySelector('.teams')?.textContent.trim() || '';
                        const league = item.querySelector('.league')?.textContent.trim() || '';
                        
                        matches.push({
                            time,
                            teams,
                            league,
                            timestamp: new Date().toISOString()
                        });
                    });
                    
                    return matches;
                } catch (e) {
                    return { error: e.toString() };
                }
            }""")
            
            # Salva i dati JSON
            with open(json_output, "w", encoding="utf-8") as f:
                json.dump({
                    "lastUpdated": datetime.now().isoformat(),
                    "data": schedule_data
                }, f, indent=2)
            
            print(f"Dati JSON salvati in {json_output}")
            
            # Cattura screenshot per debug
            page.screenshot(path="schedule_screenshot.png")
            
            # Chiudi il browser
            browser.close()
            
            return True
            
        except Exception as e:
            print(f"ERRORE: {str(e)}")
            # Cattura uno screenshot in caso di errore per debug
            try:
                page.screenshot(path="error_screenshot.png")
                print("Screenshot dell'errore salvato in error_screenshot.png")
            except:
                pass
            return False

if __name__ == "__main__":
    success = extract_schedule_container()
    # Imposta il codice di uscita in base al successo dell'operazione
    # Utile per i sistemi CI che controllano i codici di uscita
    if not success:
        exit(1)
