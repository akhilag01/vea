# using beautiful soup and requests
# go to https://blog.feedspot.com/rss_directory/a/ then /b/ then /c/ etc
# for each page find all the td elements with class "cat-col-1" and get the href within

import requests
import requests.exceptions
from bs4 import BeautifulSoup
import json


def get_rss_links():
    rss_links = []
    for letter in range(ord("a"), ord("z") + 1):
        letter = chr(letter)
        print(letter)
        url = f"https://blog.feedspot.com/rss_directory/{letter}/"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        for td in soup.find_all("td", class_="cat-col-1"):
            rss_links.append(td.find("a")["href"])
    return rss_links


# get rss links from https://blog.feedspot.com/usa_news_rss_feeds/
# within the page, find all the a links with the "ext" class and no other classes
# and get the href attribute


def has_only_ext_class(tag):
    return tag.has_attr("class") and tag["class"] == ["ext"]

# given a list of urls, save as a file
def save_urls(urls, filename):
    with open(filename, "w") as f:
        for url in urls:
            f.write(url)
            f.write("\n")


def get_image_url(description):
    soup = BeautifulSoup(description, "html.parser")
    img = soup.find("img")
    if img and img.has_attr("src"):
        return img["src"]
    return None

def rss_data_from_url(url):
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(f"Error accessing URL {url}: {str(e)}")
        return None
    
    soup = BeautifulSoup(r.text, "lxml-xml")
    data = []
    for item in soup.find_all("item"):
        description = ""
        if item.description:
            description = item.description.text
        if description.startswith("<"):
            description = BeautifulSoup(description, "html.parser").text
        description = description.encode("unicode_escape").decode("utf-8")

        image_url = get_image_url(item.description.text if item.description else "")

        data.append(
            {
                "title": item.title.text if item.title else "",
                "description": description,
                "link": item.link.text if item.link else "",
                "pubDate": item.pubDate.text if item.pubDate else "",
                "image_url": image_url,
            }
        )
    return {
        "title": soup.title.text if soup.title else "",
        "link": soup.link.text if soup.link else "",
        "items": data,
    }



def read_rss_links_from_file(filename):
    with open(filename, "r") as f:
        links = [line.strip() for line in f.readlines()]
    return links



if __name__ == "__main__":
    links = read_rss_links_from_file("scrapers/RSS/us_news_rss_links.txt")

    all_rss_data = []

    for link in links:  # process all links in the list
        if link.startswith("http://") or link.startswith("https://"):
            print(f"Processing URL: {link}")
            rss_data = rss_data_from_url(link)
            if rss_data:
                all_rss_data.append(rss_data)
        else:
            print(f"Skipping invalid URL: {link}")

    with open("data_sources/us.json", "w") as f:
        json.dump(all_rss_data, f)
