import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time


class Trip:
    def __init__(self, title, region, ship, price):
        self.title = title
        self.region = region
        self.ship = ship
        self.price = price

    def __repr__(self):
        return f"Trip(title={self.title!r}, region={self.region!r}, ship={self.ship!r}, price={self.price!r})"


def main():
    url = input("Enter the Carnival search URL for trips: ").strip()
    if not url:
        print("No URL provided. Exiting.")
        return
    fetch_accessible_cabins(url)


def fetch_accessible_cabins(url):
    # Set up Selenium with headless Chrome
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(5)  # Wait for JS to load (adjust as needed)
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, 'html.parser')
    # Find all trip tiles using data-testid attribute
    trip_tiles = soup.find_all('div', {'data-testid': 'tripTile'})
    if not trip_tiles:
        print("No trips found.")
        return
    trips = []
    for i, tile in enumerate(trip_tiles, 1):
        # Extract title, region, ship, and price if available
        # Title is a combination of several spans inside the h2
        title_h2 = tile.find('h2', {'data-testid': 'itinerary-title'})
        if title_h2:
            # Join all text nodes with spaces for readability
            title = ' '.join(title_h2.stripped_strings)
        else:
            title = None
        region = tile.find('span', {'data-testid': lambda v: v and v.startswith('cg-region_')})
        ship = tile.find('div', {'data-testid': lambda v: v and v.startswith('cg-ship_')})
        price = tile.find('div', {'data-testid': 'priceAmount'})
        trip = Trip(
            title=title,
            region=region.get_text(strip=True) if region else None,
            ship=ship.get_text(strip=True) if ship else None,
            price=price.get_text(strip=True) if price else None
        )
        trips.append(trip)
        print(f"Trip {i}:")
        if title:
            print(f"  Title: {title}")
        if region:
            print(f"  Region: {region.get_text(strip=True)}")
        if ship:
            print(f"  Ship: {ship.get_text(strip=True)}")
        if price:
            print(f"  Price: ${price.get_text(strip=True)}")
        print()
    return trips


if __name__ == "__main__":
    main()
