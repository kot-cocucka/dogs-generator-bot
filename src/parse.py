import sqlite3
import urllib

import requests
from bs4 import BeautifulSoup

urls = [
    "https://ru.wikipedia.org/wiki/Категория:Породы_собак,_признанные_Международной_кинологической_федерацией",
    "https://ru.wikipedia.org/w/index.php?title=%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:%D0%9F%D0%BE%D1%80%D0%BE%D0%B4%D1%8B_%D1%81%D0%BE%D0%B1%D0%B0%D0%BA,_%D0%BF%D1%80%D0%B8%D0%B7%D0%BD%D0%B0%D0%BD%D0%BD%D1%8B%D0%B5_%D0%9C%D0%B5%D0%B6%D0%B4%D1%83%D0%BD%D0%B0%D1%80%D0%BE%D0%B4%D0%BD%D0%BE%D0%B9_%D0%BA%D0%B8%D0%BD%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%BE%D0%B9_%D1%84%D0%B5%D0%B4%D0%B5%D1%80%D0%B0%D1%86%D0%B8%D0%B5%D0%B9&pagefrom=%D0%9F%D0%B0%D1%80%D1%81%D0%BE%D0%BD-%D1%80%D0%B0%D1%81%D1%81%D0%B5%D0%BB-%D1%82%D0%B5%D1%80%D1%8C%D0%B5%D1%80#mw-pages"
]

conn = sqlite3.connect("dog_breeds.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS breeds (id INTEGER PRIMARY KEY, name TEXT, url TEXT, total_generated INTEGER DEFAULT 0)")
for url in urls:
    response = requests.get(url)
    html = response.text

    soup = BeautifulSoup(html, "html.parser")

    dog_breeds = []
    for link in soup.find_all("a"):
        if link.get("title") and (
            urllib.parse.unquote_plus(link.get("href")).replace("/wiki/","").replace("_"," ") == link.get("title")):
            breed_name = link.text
            breed_url = "https://ru.wikipedia.org" + link.get("href")
            dog_breeds.append((breed_name, breed_url))
        else:
            print(f"skip {link.get('title')}")

    for breed in dog_breeds:
        cursor.execute("INSERT OR IGNORE INTO breeds (name, url) VALUES (?, ?)", breed)

conn.commit()
conn.close()

print("Породы собак успешно сохранены в базу данных с именами и ссылками, без дубликатов.")
