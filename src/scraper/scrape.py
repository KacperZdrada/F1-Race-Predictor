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


# Helper function to get list of results

# List structured as follows:
#  i%4==0  |   i%4==1   | i%4==2 | i%4==3      (where i is the index)
# Position | Car Number | Driver | Team

# Scraped qualifying table is structured as follows:
#    0     |     1      |    2   |   3  |  4 |  5 |  6 |  7
# Position | Car Number | Driver | Team | Q1 | Q2 | Q3 | laps

# Scraped race table is structured as follows:
#    0     |     1      |    2   |   3  |  4   |  5   |   6
# Position | Car Number | Driver | Team | Laps | Time | Points
def getResults(url, startEntriesSkipped = 7, usefulColumns = 4, columnsSkipped = 4, qualifying = False):
    if qualifying:
        # Change the URL from the race result page to the qualifying result page
        url = url.replace("race-result", "qualifying")
        # Need to skip 8 headers, and 4 columns in the case of the qualifying results table
        startEntriesSkipped = 8
        columnsSkipped = 5

    qualifyingPage = getPageObject(url)
    # Find all p elements in the results table
    qualifyingResults = qualifyingPage.find("table", class_="f1-table f1-table-with-data w-full").find_all('p')

    # Loop through all the p elements taking only data that is needed

    data = []
    counter = startEntriesSkipped  # Initialise counter to skip headers
    counter2 = 0  # Second counter used to keep track of when columns need to be skipped
    while counter < len(qualifyingResults):
        entry = qualifyingResults[counter].text.replace("\xa0", " ")

        if counter2 == 2:
            # Remove driver code from name
            entry = entry[:-3]

        data.append(entry)

        counter2 += 1
        if counter2 == usefulColumns:
            counter2 = 0
            counter += columnsSkipped  # Skip unnecessary columns
        else:
            counter += 1
    return data


def main():
    try:
        races2024 = getRaces(getPageObject("https://www.formula1.com/en/results/2024/races"), 2024)
        for race in races2024:
            qualiResults = getResults(races2024[race], qualifying=True)
            raceResults = getResults(races2024[race])
            print(race)
            print(qualiResults)
            print(raceResults)

    except Exception as e:
        print(e)

main()