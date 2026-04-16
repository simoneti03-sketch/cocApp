import cloudscraper
from bs4 import BeautifulSoup

def dump_th18():
    url = "https://clashofclans.fandom.com/wiki/User_blog:Yehor4k2007/Required_Upgrades_for_each_Town_Hall_Level_(Minimal_Requirements_to_upgrade_a_Town_Hall)"
    scraper = cloudscraper.create_scraper()
    r = scraper.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    for table in soup.find_all('table'):
        if 'Town Hall Level 18' in table.get_text():
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                print([c.get_text(strip=True) for c in cols])

if __name__ == "__main__":
    dump_th18()
