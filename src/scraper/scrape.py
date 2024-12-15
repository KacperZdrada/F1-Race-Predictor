import requests
import time
from bs4 import BeautifulSoup


# Helper function to get beautiful soup object from URL
def getPageObject(url):
    # HTTP request to get URL
    page = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    })
    # Check if HTTP request successful
    if page.status_code != 200:
        raise Exception("Error fetching:", url, "\nError code:", page.status_code)
    else:
        # Return beautiful soup object
        return BeautifulSoup(page.content, "html.parser")


# Helper function to get dictionary of race names and their URLs from the main page
def getRaces(mainPage, year):
    # Get main results table
    yearResultsTable = mainPage.find("table", class_="f1-table f1-table-with-data w-full")
    # Get all hyperlinks from table
    urlList = yearResultsTable.find_all("a", class_="underline underline-offset-normal decoration-1 decoration-greyLight hover:decoration-brand-primary")
    # Change list into dictionary with race name as key, and hyperlink as value
    raceDict = {}
    for races in urlList:
        raceDict[races.text.strip()] = "https://www.formula1.com/en/results/"+str(year)+"/"+races.get("href")
    return raceDict


def main():
    try:
        print(getRaces(getPageObject("https://www.formula1.com/en/results/2024/races"), 2024))
    except Exception as e:
        print(e)

main()