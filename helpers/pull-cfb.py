import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_cfb_results_sportsref(year, output_file):
    url = f"https://www.sports-reference.com/cfb/years/{year}-schedule.html"
    print(f"Scraping {url}")
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    table = soup.find("table", id="schedule")
    if not table:
        print("No table found.")
        return

    rank_pattern = re.compile(r"^\(\d+\)\s*")  # matches "(number)" at start

    for row in table.find("tbody").find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue

        data = {cell["data-stat"]: cell.get_text(strip=True) for cell in cells if cell.has_attr("data-stat")}

        # Skip future games (no scores yet)
        if not data.get("winner_points") or not data.get("loser_points"):
            continue

        winner = data.get("winner_school_name", "")
        loser = data.get("loser_school_name", "")

        # Remove rank prefix like "(5) Alabama"
        winner = rank_pattern.sub("", winner)
        loser = rank_pattern.sub("", loser)

        if winner and loser:
            results.append({"winner": winner, "loser": loser})

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(results)} completed games to {output_file}")

if __name__ == "__main__":
    year = input("Enter year: ")
    output_file = f"data/cfb_{year}.json"
    scrape_cfb_results_sportsref(year=int(year), output_file=output_file)
