import atexit
import time
from typing import List, Set, Tuple

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class Trip:
    """Represents a cruise trip result."""

    def __init__(self, title: str, region: str, ship: str, price: str):
        self.title = title
        self.region = region
        self.ship = ship
        self.price = price

    def __repr__(self):
        return f"Trip(title={self.title!r}, region={self.region!r}, ship={self.ship!r}, price={self.price!r})"


driver = None  # Global Selenium driver


def close_driver():
    """Ensure the Selenium driver is closed on exit."""
    global driver
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass
        driver = None


atexit.register(close_driver)


def parse_trips(trip_tiles) -> List[Trip]:
    """Parse trip tiles into a list of Trip objects."""
    trips = []
    for tile in trip_tiles:
        title_h2 = tile.find('h2', {'data-testid': 'itinerary-title'})
        title = ' '.join(title_h2.stripped_strings) if title_h2 else None
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
    return trips


def fetch_trips(url: str) -> None:
    """Fetch and display trips from the Carnival search page, supporting 'load more'."""
    global driver
    if not url.startswith("https://www.carnival.com/"):
        print("Invalid URL. Please provide a valid Carnival search URL.")
        return
    # Set up Selenium with headless Chrome
    options = Options()
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(5)  # Wait for JS to load
    seen_trips: Set[Tuple[str, str, str, str]] = set()
    trip_counter = 1
    while True:
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        trip_tiles = soup.find_all('div', {'data-testid': 'tripTile'})
        if not trip_tiles:
            print("No trips found.")
            return
        trips = parse_trips(trip_tiles)
        new_trips = []
        for trip in trips:
            trip_id = (trip.title, trip.region, trip.ship, trip.price)
            if trip_id not in seen_trips:
                seen_trips.add(trip_id)
                new_trips.append(trip)
        if not new_trips:
            print("No new trips found.")
        for trip in new_trips:
            print(f"Trip {trip_counter}:")
            if trip.title:
                print(f"  Title: {trip.title}")
            if trip.region:
                print(f"  Region: {trip.region}")
            if trip.ship:
                print(f"  Ship: {trip.ship}")
            if trip.price:
                print(f"  Price: {trip.price}")
            print("-" * 40)
            trip_counter += 1
        # Check for load more button
        load_more_available = False
        try:
            load_more_btn = driver.find_element('xpath', "//button[@data-testid='loadMoreResults']")
            if load_more_btn.is_displayed() and load_more_btn.is_enabled():
                load_more_available = True
        except Exception:
            pass
        # Prompt user for next action
        if load_more_available:
            user_input = input("Load more results? (y/n), or enter a trip number or range (e.g. 3 or 2-5) to inspect for accessible cabins: ").strip().lower()
            if user_input == 'y':
                load_more_btn.click()
                time.sleep(1)
                continue
        else:
            user_input = input("Enter a trip number or range (e.g. 3 or 2-5) to inspect for accessible cabins, or press Enter to exit: ").strip().lower()
        if user_input.isdigit():
            inspect_trip_for_accessible_cabins(int(user_input), trips)
            break
        elif '-' in user_input:
            parts = user_input.split('-')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                start = int(parts[0])
                end = int(parts[1])
                for idx in range(start, end + 1):
                    inspect_trip_for_accessible_cabins(idx, trips)
                break
        else:
            break


def main() -> None:
    """Entrypoint for the script."""
    try:
        url = input("Enter the Carnival search URL for trips: ").strip()
        if not url:
            print("No URL provided. Exiting.")
            return
        fetch_trips(url)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")


def is_trip_accessible() -> bool:
    """
    Attempt to click the 'Continue to Specials' button on the cabins panel.
    Returns True if the button was found and clicked, False otherwise.
    """
    global driver
    try:
        # Wait for the Continue button to be clickable
        continue_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='cabinsPanel2021Continue']"))
        )
        continue_btn.click()
        return True
    except (TimeoutException, WebDriverException):
        return False


# Placeholder for accessible cabin inspection

def inspect_trip_for_accessible_cabins(trip_number: int, trips: list):
    """Inspect a trip for accessible cabin availability."""
    global driver
    if 1 <= trip_number <= len(trips):
        trip = trips[trip_number - 1]
        print(f"\n[Inspecting Trip {trip_number} for accessible cabins]")
        print(f"  Title: {trip.title}")

        # Find the trip tile for this trip
        try:
            # First, try to find the show dates button for this trip
            show_dates_buttons = driver.find_elements('xpath', "//button[contains(@data-testid, 'showDates_')]")
            if trip_number <= len(show_dates_buttons):
                show_button = show_dates_buttons[trip_number - 1]
                print("  Clicking 'Show Dates' button to check available sailing dates...")

                # Check if dates are already expanded
                is_expanded = show_button.get_attribute('aria-expanded')
                if is_expanded != 'true':
                    show_button.click()
                    time.sleep(2)  # Wait for dates to expand

                # Now look for accessible cabin options
                print("  Checking for accessible cabin availability...")

                # Check for the available dates section
                dates_section = driver.find_elements('xpath', "//div[contains(@class, 'dates-cell-style__Date')]")
                if dates_section:
                    print(f"  Found {len(dates_section)} available sailing dates")

                    # Find all "START BOOKING" buttons for different sailing dates
                    booking_buttons = driver.find_elements('xpath', "//a[@data-testid='selectSailingDateButton']")
                    if booking_buttons:
                        print(f"  Found {len(booking_buttons)} booking options")

                        # Extract booking URLs and iterate through each sailing date
                        buttons = driver.find_elements(By.XPATH, "//a[@data-testid='selectSailingDateButton']")
                        booking_urls = [btn.get_attribute('href') for btn in buttons]
                        for idx, url in enumerate(booking_urls):
                            # Re-fetch date elements to avoid stale references
                            dates = driver.find_elements(By.XPATH, "//div[contains(@class, 'dates-cell-style__Days')]")
                            date_info = dates[idx].text if idx < len(dates) else 'unknown date'
                            print(f"\n  Checking sailing {idx+1}/{len(booking_urls)} ({date_info})...")
                            # Navigate to booking URL and attempt to pull accessible cabin options
                            driver.get(url)
                            time.sleep(2)
                            cabin_available = False
                            if is_trip_accessible():
                                try:
                                    # Click 'Accessible Room Needed' checkbox
                                    checkbox = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[data-testid='accessibilityToggleButton.0Collapse']"))
                                    )
                                    if checkbox.get_attribute('aria-checked') != 'true':
                                        checkbox.click()
                                    # Select 'Fully Accessible Cabin' option
                                    full_option = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Fully Accessible Cabin')]"))
                                    )
                                    full_option.click()
                                    # Click 'Continue to Room type'
                                    qualifiers_continue = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='qualifiersPanelNextLink']"))
                                    )
                                    qualifiers_continue.click()
                                    # Click the accessibility acknowledgement confirm button
                                    confirm_btn = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='accessibilityConfirmationContinueButton']"))
                                    )
                                    confirm_btn.click()
                                    # Wait for possible error message or next page load
                                    time.sleep(2)
                                    # Check for booking error container
                                    error_elem = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='bookingErrorContainer']")
                                    if error_elem:
                                        cabin_available = False
                                    else:
                                        cabin_available = True
                                except Exception as e:
                                    print(f"  Error selecting accessible options: {e}")
                            print(f"  Accessible cabin available? {cabin_available}")
                            if cabin_available:
                                try:
                                    # Wait for the room types slider to appear
                                    slider = WebDriverWait(driver, 5).until(
                                        lambda d: d.find_element(By.CSS_SELECTOR, "div[data-testid='meta2022SliderContainer']")
                                    )
                                    # Extract each accessible room option
                                    options = slider.find_elements(By.CSS_SELECTOR, "div[data-testid='metaButton2022'] button")
                                    print("    Accessible room types and prices:")
                                    for opt in options:
                                        name = opt.find_element(By.CSS_SELECTOR, "div[data-testid='metaLabel']").text
                                        price = opt.find_element(By.CSS_SELECTOR, "div[data-testid='fromPriceLabel']").text
                                        print(f"      {name}: {price}")
                                    # Print the current booking page URL
                                    print(f"    Page URL: {driver.current_url}")
                                except Exception:
                                    print("    No room slider found or failed to extract prices")
                            # Navigate back to trip list: go back twice to exit booking flow
                            driver.back()
                            time.sleep(1)
                            driver.back()
                            time.sleep(1)
                            show_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, f"(//button[contains(@data-testid,'showDates_')])[{trip_number}]") )
                            )
                            if show_button.get_attribute('aria-expanded') != 'true':
                                show_button.click()
                                WebDriverWait(driver, 10).until(lambda d: show_button.get_attribute('aria-expanded') == 'true')
                    else:
                        print("  No booking buttons found")
                else:
                    print("  No sailing dates found or dates section not available")
            else:
                print("  Could not find 'Show Dates' button for this trip")
        except Exception as e:
            print(f"  Error inspecting trip: {e}")
    else:
        print(f"Trip number {trip_number} is out of range.")


# --- Entrypoint ---
if __name__ == "__main__":
    main()
