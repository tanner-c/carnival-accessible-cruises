# Carnival Accessible Cabin Crawler

Carnival's website makes it difficult to search for accessible cabins on their cruises. This tool automates the process by crawling through each cruise in a search and checking if accessible cabins are available.

## Purpose

This project was created to help users quickly identify cruises with accessible cabins, saving time and effort compared to manually searching on Carnival's website.

## How to Run

1. Install dependencies (preferably in a virtual environment):

   ```fish
   pip install -r requirements.txt
   ```

2. Run the crawler script:

   ```fish
   python crawler.py
   ```

3. When prompted, enter a Carnival search URL that lists cruises (e.g., from their search page).

The script will automatically expand all available dates for each cruise and display the cruise details. The next step is to enhance the tool to check for accessible cabin availability for each cruise.

---

**Note:** This tool is for personal/educational use. Please respect Carnival's terms of service and robots.txt when scraping their website.
