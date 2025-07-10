import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

logger = logging.getLogger(__name__)

class HotelService:
    def __init__(self):
        self.price_cache = {}
        self.cache_file = 'data/hotel_prices_cache.json'
        self._load_cache()
        
        self.driver = None
    
    def _load_cache(self):
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.price_cache = json.load(f)
                logger.info(f"Hotel-Cache geladen: {len(self.price_cache)} Einträge")
        except Exception as e:
            logger.error(f"Fehler beim Laden des Hotel-Caches: {e}")
            self.price_cache = {}
    
    def _save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.price_cache, f, ensure_ascii=False, indent=2)
            logger.info(f"Hotel-Cache gespeichert: {len(self.price_cache)} Einträge")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Hotel-Caches: {e}")
    
    def _get_cache_key(self, location: str, check_in: str, check_out: str, guests: int) -> str:
        return f"{location}_{check_in}_{check_out}_{guests}"

    def search_hotels(self, location: str, check_in: Optional[str] = None, 
                     check_out: Optional[str] = None, guests: int = 1, 
                     budget: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            if not check_in:
                check_in = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            if not check_out:
                check_out = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
            
            cache_key = self._get_cache_key(location, check_in, check_out, guests)
            
            if cache_key in self.price_cache:
                cached_data = self.price_cache[cache_key]
                logger.info(f"Hotels aus Cache geladen für {location}")
                
                if isinstance(cached_data, dict) and 'hotels' in cached_data:
                    cached_hotels = cached_data['hotels']
                    logger.info(f"Altes Cache-Format erkannt: {len(cached_hotels)} Hotels")
                else:
                    cached_hotels = cached_data
                    logger.info(f"Neues Cache-Format erkannt: {len(cached_hotels)} Hotels")
                
                hotels = cached_hotels
                if budget:
                    hotels = [h for h in hotels if h.get('price', 0) <= budget]
                hotels.sort(key=lambda x: x.get('price', 0))
                
                return hotels
            
            logger.info(f"Starte Selenium-Webscraping für Hotels in {location}")
            
            hotels = self._search_hotels_with_selenium(location, check_in, check_out, guests)
            
            logger.info(f"Hotels gefunden: {len(hotels)} Hotels")
            
            if budget:
                hotels = [h for h in hotels if h.get('price', 0) <= budget]
                logger.info(f"Nach Budget-Filter: {len(hotels)} Hotels")
            
            hotels.sort(key=lambda x: x.get('price', 0))
            
            if hotels:
                self.price_cache[cache_key] = hotels
                self._save_cache()
                logger.info(f"Hotels in Cache gespeichert: {len(hotels)} Hotels")
            
            logger.info(f"{len(hotels)} Hotels gefunden für {location} (sortiert nach Preis)")
            return hotels
            
        except Exception as e:
            logger.error(f"Fehler bei der Hotelsuche: {e}")
            return []

    def get_hotel_summary(self, hotels: List[Dict[str, Any]], location: str = "", check_in: str = None, check_out: str = None, guests: int = 1) -> str:
        if not hotels:
            return "Keine gut bewerteten Hotels gefunden."
        
        hotels_sorted = sorted(hotels, key=lambda x: x.get('price', 0))
        
        search_info = ""
        if check_in and check_out:
            try:
                from datetime import datetime
                check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
                check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
                check_in_formatted = check_in_date.strftime("%d.%m.%Y")
                check_out_formatted = check_out_date.strftime("%d.%m.%Y")
                search_info = f"Zeitraum: {check_in_formatted} bis {check_out_formatted}\n Personen: {guests}\n\n"
            except:
                search_info = f"Zeitraum: {check_in} bis {check_out}\n Personen: {guests}\n\n"
        
        location_encoded = location.replace(' ', '+')
        main_source_link = f"Datenquelle: https://www.google.com/travel/hotels?q={location_encoded}\n\n"
        
        hotels_to_show = min(5, len(hotels_sorted))
        summary = f"{search_info}{main_source_link}Gefunden: {hotels_to_show} gut bewertete Hotels (sortiert nach Preis)\n\n"
        
        for i, hotel in enumerate(hotels_sorted[:5], 1):
            name = hotel.get('name', 'Unbekanntes Hotel')
            price = hotel.get('price', 0)
            address = hotel.get('address', '')
            amenities = hotel.get('amenities', [])
            
            summary += f"{i}. {name}\n"
            summary += f"   Preis: {price:.0f} EUR pro Nacht\n"
            
            summary += "\n"
        
        return summary 
    
    def get_cached_prices(self, location: str) -> List[Dict[str, Any]]:
        cached_hotels = []
        for cache_key, cache_data in self.price_cache.items():
            if location.lower() in cache_key.lower():
                cached_hotels.extend(cache_data.get('hotels', []))
        return cached_hotels
    
    def clear_cache(self):
        self.price_cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        logger.info("Hotel-Cache gelöscht")

    def _setup_selenium_driver(self):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--window-size=1920,1080')
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Selenium WebDriver erfolgreich eingerichtet")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Einrichten des Selenium WebDrivers: {e}")
            return False
    
    def _close_selenium_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("Selenium WebDriver geschlossen")
            except Exception as e:
                logger.error(f"Fehler beim Schließen des WebDrivers: {e}")
    
    def _human_like_delay(self, min_seconds=1, max_seconds=3):
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def _scroll_page(self):
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            self._human_like_delay(1, 2)
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._human_like_delay(1, 2)
            
            self.driver.execute_script("window.scrollTo(0, 0);")
            self._human_like_delay(1, 2)
            
        except Exception as e:
            logger.warning(f"Fehler beim Scrollen: {e}")
    
    def _click_element_safely(self, element, description=""):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self._human_like_delay(0.5, 1)
            
            element.click()
            self._human_like_delay(1, 2)
            
            logger.info(f"Erfolgreich geklickt: {description}")
            return True
            
        except Exception as e:
            logger.warning(f"Fehler beim Klicken auf {description}: {e}")
            return False
    

    
    def _accept_cookies(self):
        try:
            if not self.driver:
                return False
            possible_selectors = [
                "button[aria-label*='Alle akzeptieren']",
                "button[aria-label*='Accept all']",
                "button[aria-label*='Zustimmen']",
                "button[aria-label*='Ich stimme zu']",
                "button[aria-label*='Agree']",
                "button[aria-label*='Akzeptieren']",
                "button[role='button'] span:contains('Alle akzeptieren')",
                "button:contains('Alle akzeptieren')",
                "button:contains('Accept all')",
                "div[role='dialog'] button",
            ]
            for selector in possible_selectors:
                try:
                    cookie_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if cookie_btn:
                        self._click_element_safely(cookie_btn, "Cookie-Banner")
                        logger.info(f"Cookie-Banner akzeptiert mit Selektor: {selector}")
                        self._human_like_delay(1, 2)
                        return True
                except Exception:
                    continue
            logger.info("Kein Cookie-Banner gefunden oder bereits akzeptiert.")
            return False
        except Exception as e:
            logger.warning(f"Fehler beim Akzeptieren des Cookie-Banners: {e}")
            return False

    def _search_hotels_with_selenium(self, location: str, check_in: str, check_out: str, guests: int) -> List[Dict[str, Any]]:
        try:
            if not self._setup_selenium_driver():
                return []
            
            self.driver.get("https://www.google.com/travel/hotels")
            self._human_like_delay(2, 4)
            
            self._accept_cookies()
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            try:
                WebDriverWait(self.driver, 5).until_not(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, ".VfPpkd-RLmnJb"))
                )
                logger.info("Overlay '.VfPpkd-RLmnJb' ist verschwunden.")
            except Exception:
                logger.info("Kein Overlay '.VfPpkd-RLmnJb' sichtbar oder bereits verschwunden.")
            
            try:
                logger.info("Suche alle sichtbaren Suchfelder mit CSS-Selektor input[placeholder*='Unterkunft'] ...")
                search_boxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[placeholder*="Unterkunft"]')
                if not search_boxes:
                    logger.info("Kein Feld mit placeholder*='Unterkunft' gefunden, fallback auf placeholder*='Hotel'.")
                    search_boxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[placeholder*="Hotel"]')
                search_box = None
                for box in search_boxes:
                    if box.is_displayed():
                        search_box = box
                        logger.info(f"Aktives Suchfeld gewählt: value='{box.get_attribute('value')}', placeholder='{box.get_attribute('placeholder')}', autofocus={box.get_attribute('autofocus')}")
                        break
                if not search_box:
                    inputs = self.driver.find_elements(By.TAG_NAME, 'input')
                    for i, inp in enumerate(inputs):
                        logger.info(f"Input {i}: value='{inp.get_attribute('value')}', placeholder='{inp.get_attribute('placeholder')}', aria-label='{inp.get_attribute('aria-label')}', jsname='{inp.get_attribute('jsname')}', autofocus='{inp.get_attribute('autofocus')}', displayed={inp.is_displayed()}")
                    logger.error("Kein aktives Suchfeld gefunden! Abbruch.")
                    return []
                try:
                    clear_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Löschen"]')
                    if clear_btn.is_displayed():
                        clear_btn.click()
                        logger.info("Löschen-Button erfolgreich geklickt.")
                        self._human_like_delay(0.2, 0.5)
                except Exception as e:
                    logger.info(f"Löschen-Button nicht gefunden oder nicht klickbar: {e}")
                
                search_query = f"hotel {location}"
                actions = ActionChains(self.driver)
                actions.move_to_element(search_box).click().perform()
                self._human_like_delay(0.2, 0.5)
                for char in search_query:
                    actions.send_keys(char)
                    actions.pause(random.uniform(0.1, 0.25))
                actions.perform()
                search_box.send_keys(Keys.ENTER)
                self._human_like_delay(2, 3)
                
                vorschlaege = self.driver.find_elements(By.CSS_SELECTOR, 'li[data-suggestion]')
                alle_suggestions = [v.get_attribute('data-suggestion') for v in vorschlaege]
                logger.info(f"Gefundene Vorschläge: {alle_suggestions}")
                li_elem = None
                for v in vorschlaege:
                    if v.get_attribute('data-suggestion') == search_query:
                        li_elem = v
                        logger.info(f"Exakter Vorschlag gefunden: {search_query}")
                        break
                if not li_elem:
                    for v in vorschlaege:
                        suggestion = v.get_attribute('data-suggestion') or ''
                        if 'hotel' in suggestion.lower() and location.lower() in suggestion.lower():
                            li_elem = v
                            logger.info(f"Dynamischer Vorschlag gewählt: {suggestion}")
                            break
                if li_elem:
                    try:
                        self._click_element_safely(li_elem, f"Vorschlag '{li_elem.get_attribute('data-suggestion')}'")
                        self._human_like_delay(2, 3)
                    except Exception as e:
                        logger.warning(f"Vorschlag gefunden, aber nicht anklickbar: {e}")
                        logger.info(f"Drücke Enter nach Eintippen von: {search_query}")
                        search_box.send_keys(Keys.ENTER)
                        self._human_like_delay(2, 3)
                else:
                    logger.warning(f"Kein passender Vorschlag gefunden. Drücke Enter nach Eintippen von: {search_query}")
                    search_box.send_keys(Keys.ENTER)
                    self._human_like_delay(2, 3)
            except Exception as e:
                logger.error(f"Suchfeld NICHT gefunden oder nicht anklickbar! Exception: {e}")
            
            self._human_like_delay(3, 5)
            
            self._scroll_page()
            
            for _ in range(5):
                self.driver.execute_script("window.scrollBy(0, 600);")
                self._human_like_delay(0.5, 1.2)
            
            hotels = []
            seen_hotels = set()
            a_elements = self.driver.find_elements(By.CSS_SELECTOR, "a.W8vlAc.lRagtb[aria-label]")
            logger.info(f"Gefunden: {len(a_elements)} <a>-Elemente mit Klasse 'W8vlAc lRagtb' und aria-label")
            
            for i, a in enumerate(a_elements):
                try:
                    aria_label = a.get_attribute('aria-label')
                    logger.info(f"Verarbeite aria-label {i+1}: '{aria_label}'")
                    match = re.search(r'Preise ab ([\d.,]+)\s*([\$€₺]|TRY)\s+für\s+(.+?)(?:\s+DEAL|\s+TOLLER|\s*$)', aria_label)
                    if not match:
                        match = re.search(r'([\d.,]+)\s*([\$€₺]|TRY).*?für\s+(.+?)(?:\s+DEAL|\s+TOLLER|\s*$)', aria_label)
                    
                    if match:
                        price_str = match.group(1)
                        currency = match.group(2)
                        name = match.group(3).strip()
                        
                        if currency == '₺' or currency == 'TRY':
                            price_str = price_str.replace('.', '').replace(',', '.')
                        else:
                            price_str = price_str.replace(',', '.')
                        
                        price = float(price_str)
                        
                        if currency == '$':
                            price = price * 0.85
                        elif currency == '₺' or currency == 'TRY':
                            price = price * 0.035
                        
                        if name in seen_hotels:
                            logger.info(f"Hotel bereits gesehen, überspringe: {name}")
                            continue
                        
                        seen_hotels.add(name)
                        
                        hotels.append({
                            'name': name,
                            'price': price
                        })
                        logger.info(f"Hotel extrahiert (aria-label): {name} | {price} €")
                    else:
                        logger.warning(f"Regex-Match fehlgeschlagen für aria-label: '{aria_label}'")
                except Exception as e:
                    logger.warning(f"Fehler beim Extrahieren aus aria-label: {e}")
            

            
            if hotels:
                logger.info(f"{len(hotels)} Hotels erfolgreich aus aria-label extrahiert.")
                return hotels

            logger.warning("Keine Hotels aus aria-label extrahiert.")
            return []
            
        except Exception as e:
            logger.error(f"Fehler bei Selenium-Hotelsuche: {e}")
            return []
        
        finally:
            self._close_selenium_driver()