import requests
from bs4 import BeautifulSoup


def main():
    url = input("Enter the Carnival search URL for trips: ").strip()
    if not url:
        print("No URL provided. Exiting.")
        return
    fetch_accessible_cabins(url)

def fetch_accessible_cabins(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    # TODO: Update the selector to match the actual accessible cabins info
    cabins = soup.find_all('div', class_='accessible-cabin')
    for cabin in cabins:
        print(cabin.get_text(strip=True))

if __name__ == "__main__":
    main()
