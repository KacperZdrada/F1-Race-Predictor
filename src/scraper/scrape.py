import requests
import time
from bs4 import BeautifulSoup


# Helper function to get beautiful soup object from URL
def getPageObject(url):
    print("Scraping:", url)
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

# Helper function that returns list of parameters needed by the getResults function for qualifying depending on year
# This is because results are structured differently on the website for these years
# List of structure [url-ending, startEntriesSkipped, usefulColumns, columnsSkipped]
def getQualiScrapingParameters(year):
    if year >= 1950 and year <= 1982:
        return ["starting-grid", 5]
    elif year >= 1983 and year<=2005:
        return ["qualifying/0", 6]
    else:
        return ["qualifying", 8, "Race,Year,Position,Car Number,Driver,Team,Q1,Q2,Q3,Laps"]

# Helper function to get list of results
# Scraped qualifying table is structured as follows:
#    0     |     1      |    2   |   3  |  4 |  5 |  6 |  7
# Position | Car Number | Driver | Team | Q1 | Q2 | Q3 | laps

# Scraped race table is structured as follows:
#    0     |     1      |    2   |   3  |  4   |  5   |   6
# Position | Car Number | Driver | Team | Laps | Time | Points
def getResults(url, parameters):
    qualifyingPage = getPageObject(url)
    # Find all p elements in the results table
    qualifyingResults = qualifyingPage.find("table", class_="f1-table f1-table-with-data w-full").find_all('p')

    # Loop through all the p elements taking only data that is needed
    data = []
    counter = parameters[1]  # Initialise counter to skip headers
    counter2 = 0  # Second counter used to keep track of when columns need to be skipped
    while counter < len(qualifyingResults):
        entry = qualifyingResults[counter].text.replace("\xa0", " ")

        if counter % parameters[1] == 2:
            # Remove driver code from name
            entry = entry[:-3]

        data.append(entry)

        counter += 1
    return data


# Helper function to take list of structure
#  i%4==0  |   i%4==1   | i%4==2 | i%4==3      (where i is the index)
# Position | Car Number | Driver | Team
# And write it to a .csv file with following structure
#  Race, Year, Position, Car Number, Driver, Team
def writeResults(filename, data, race, year, parameters):
    # Append data to csv file
    file = open(filename, "a")

    for row in range(0, int(len(data)/parameters[1])):
        # Concatenate where the race took place and the year
        entry = str(race)+","+str(year)
        # Concatenate each position, car number, driver, team
        for subentry in range(0, parameters[1]):
            entry = entry+","+str(data[(row*parameters[1])+subentry])
        # Start new row
        file.write(entry+"\n")
    file.close()


# Helper function that adds headers to the files containing scraped data
def scrapeFilePrep(filename, headers):
    file = open(filename, "w")
    file.write(headers+'\n')
    file.close()


def main():
    try:
        scrapeFilePrep("qualiResults.csv", "Race,Year,Position,Car Number,Driver,Team,Q1,Q2,Q3,Laps")
        scrapeFilePrep("raceResults.csv", "Race,Year,Position,Car Number,Driver,Team,Points")
        for year in range(2006, 2025):
            races = getRaces(getPageObject("https://www.formula1.com/en/results/"+str(year)+"/races"), year)
            for race in races:
                time.sleep(1)
                qualiResults = getResults(races[race].replace("race-result","qualifying"), getQualiScrapingParameters(year))
                time.sleep(1)
                raceResults = getResults(races[race], ["", 7])
                writeResults("qualiResults.csv", qualiResults, race, year, ["", 8])
                writeResults("raceResults.csv", raceResults, race, year, ["", 7])

    except Exception as e:
        print(e)


main()
