import pandas as pd
from sklearn.preprocessing import StandardScaler

def dataProcessing():
    # Read both results files and transform into pandas dataframe
    qualificationResults = pd.read_csv("../scraper/qualiResults.csv", encoding="cp1252")
    raceResults = pd.read_csv("../scraper/raceResults.csv", encoding="cp1252")
    # Merge the two dataframes into one (matching where every driver qualified and finished
    # Drop the unnecessary column of car numbers
    mergedResults = (pd
                     .merge(qualificationResults, raceResults, on=["Race", "Year", "Driver", "Car Number", "Team"], suffixes=(" Quali", " Race"))
                     .drop("Car Number", axis=1))
    # Fill Null Q2 results with Q1 times
    mergedResults["Q2"] = mergedResults["Q2"].fillna(mergedResults["Q1"])
    # Fill Null Q3 results with Q2 times
    mergedResults["Q3"] = mergedResults["Q3"].fillna(mergedResults["Q2"])

    # Replace every NC (Not Classfied), DQ (disqualified), RT (Retired), EX (Excluded) position with 26 (lower than any
    # possible position
    mergedResults["Position Race"] = (mergedResults["Position Race"]
                                      .replace("NC", 26)
                                      .replace("DQ", 26)
                                      .replace("RT", 26)
                                      .replace("EX", 26)
                                      .astype(int))
    mergedResults["Position Quali"] = (mergedResults["Position Quali"]
                                       .replace("NC", 26)
                                       .replace("DQ", 26)
                                       .replace("RT", 26)
                                       .replace("EX", 26)
                                       .astype(int))

    # Add binary column for win or no win
    mergedResults["Win"] = mergedResults["Position Race"].apply(lambda x: 1 if x == 1 else 0)

    # Add binary column for race DNF and cumulative team DNFs for a season (up to previous race)
    mergedResults["Race DNF"] = mergedResults["Time"].apply(lambda x: 1 if (x == "DNF" or x == "DNS") else 0)

    # Add column for race number
    mergedResults["Race Number"] = mergedResults.groupby(["Year", "Race"], sort=False).ngroup() + 1

    # Create a new dataframe to store the total amount of DNFs for each team per race
    teamDNFs = mergedResults.groupby(["Year", "Race Number", "Team"]).agg({"Race DNF": "sum"})

    # Add a new column that tracks the cumulative DNFs for each team through the season (excluding current race)
    teamDNFs["Team Season DNF"] = teamDNFs.groupby(["Year", "Team"])["Race DNF"].cumsum() - teamDNFs["Race DNF"]
    teamDNFs = teamDNFs.drop("Race DNF", axis=1)
    # Merge this data with existing dataframe
    mergedResults = mergedResults.merge(teamDNFs, on=["Race Number", "Team"])

    # Add column for cumulative number of driver points excluding the current race
    mergedResults["Season Points"] = (mergedResults.groupby(["Year", "Driver"])["Points"]
                                      .cumsum() - mergedResults["Points"])

    # Create a new dataframe to store the average position for each driver for past 5 races
    last5 = mergedResults[["Year", "Race Number", "Driver", "Position Race"]].copy()
    last5 = last5.sort_values(by=["Driver", "Year", "Race Number"])

    # Create new column to hold the average
    last5["Last 5 Race"] = (last5.groupby("Driver")["Position Race"]
                            # Create rolling window of size 6 excluding current row (so window of size 5)
                            .rolling(window=6, min_periods=1, closed="left")
                            .mean()
                            # Fill the first entry with 0 (as no mean here because row is excluded)
                            .fillna(0)
                            .reset_index(level=0, drop=True))

    # Drop unnecessary columns
    last5 = last5.drop(["Position Race", "Year"], axis=1)

    mergedResults = mergedResults.merge(last5, on=["Driver", "Race Number"])

    # Loop over Q1, Q2, and Q3
    for i in range(1,4):

        # Replace DNF (Did Not Finish) and DNS (Did Not Start) times and any other null values
        mergedResults["Q"+str(i)] = (mergedResults["Q"+str(i)]
                               .replace("DNF", "99999:99.999")
                               .replace("DNS", "99999:99.999")
                               .replace("DEL", "99999:99.999")
                               .fillna("99999:99.999")
                               )

        # Convert all string times into float datatype
        mergedResults["Q"+str(i)] = mergedResults["Q"+str(i)].apply(lambda x: stringTimetoInt(x))

    # Find the single fastest individual time across all three qualifying sessions for each driver
    mergedResults["Fastest Individual Time"] = mergedResults[["Q1", "Q2", "Q3"]].min(axis=1)

    # Find the single fastest individual time across all three qualifying sessions and all drivers
    mergedResults["Fastest Quali Time"] = (mergedResults.groupby(["Year", "Race Number"])["Fastest Individual Time"]
                                           .transform("min"))

    # Create a new column that has the delta between each driver's fastest qualifying time and the overall
    # qualification fastest time
    mergedResults["Quali Delta"] = mergedResults["Fastest Individual Time"] - mergedResults["Fastest Quali Time"]

    # Drop unnecessary columns
    mergedResults = mergedResults.drop(["Q1", "Q2", "Time", "Laps Quali", "Laps Race"], axis=1)

    # Change team names to standard (ignoring engines, sponsors, etc. in names)
    mergedResults["Team"] = mergedResults["Team"].apply(lambda team: updateTeamNames(team))

    # Normalise data
    scaler = StandardScaler()
    mergedResults[["Quali Delta"]] = scaler.fit_transform(mergedResults[["Quali Delta"]])

    # One-hot encode categorical data like driver names, team names, and race location
    mergedResults = pd.get_dummies(mergedResults, columns=["Driver", "Team", "Race"], drop_first=True)

    print(qualificationResults.head())
    print(raceResults.head(25))
    print(teamDNFs.head(50))
    print(last5.head(50))
    print(mergedResults.head(50))
    return mergedResults


# Helper function to convert qualifying time from "minute:second.millisecond" format into total seconds
def stringTimetoInt(time):
    try:
        minutes, rest = time.split(':')
    except ValueError:
        # If a value error has occurred, then the issue is that .split() returned one argument instead of two
        # This only happens when the input time is of the form "second.milliseconds" if the time was below a minute
        # Hence, set minutes to 0, and the rest of the string, which is of the form "second.milliseconds" as the original
        # input string
        minutes = 0
        rest = time
    seconds, milliseconds = rest.split('.')
    return (int(minutes) * 60) + int(seconds) + (int(milliseconds)/1000)

# Helper functions to convert any team name to standard name (so as to exclude engine/sponsorship/rebrand changes as
# being seperate new teams)
def updateTeamNames(team):
    try:
        return teamDict[team]
    except KeyError:
        # If key error, that means input team is not in the dictionary and so is in standard form already
        return team


# Dictionary containing translation to standard team names
teamDict = {
    "AlphaTauri Honda RBPT": "Racing Bulls",
    "Lotus Renault": "Alpine",
    "Toro Rosso Ferrari": "Racing Bulls",
    "Williams Toyota": "Williams",
    "Williams Cosworth": "Williams",
    "RBR Ferrari": "Red Bull",
    "Lotus Mercedes": "Alpine",
    "AlphaTauri Honda":	"Racing Bulls",
    "Alpine Renault": "Alpine",
    "McLaren Mercedes":	"McLaren",
    "RBR Renault": "Red Bull",
    "Red Bull Racing TAG Heuer": "Red Bull",
    "Renault": "Alpine",
    "Haas Ferrari": "Haas",
    "Lotus Cosworth": "Alpine",
    "Red Bull Racing RBPT": "Red Bull",
    "Scuderia Toro Rosso Honda": "Racing Bulls",
    "Kick Sauber Ferrari": "Sauber",
    "McLaren Renault": "McLaren",
    "Force India Mercedes": "Aston Martin",
    "Williams Mercedes": "Williams",
    "McLaren Honda": "McLaren",
    "Red Bull Racing Honda": "Red Bull",
    "Aston Martin Mercedes": "Aston Martin",
    "Toro Rosso": "Racing Bulls",
    "Alfa Romeo Ferrari": "Sauber",
    "Aston Martin Aramco Mercedes": "Aston Martin",
    "AlphaTauri RBPT": "Racing Bulls",
    "Red Bull Racing Honda RBPT": "Red Bull",
    "RB Honda RBPT": "Red Bull",
    "Sauber BMW": "Sauber",
    "STR Ferrari": "STR",
    "Red Bull Racing Renault": "Red Bull",
    "STR Renault": "STR",
    "STR Cosworth":	"STR",
    "Racing Point BWT Mercedes": "Aston Martin",
    "Alfa Romeo Racing Ferrari": "Sauber",
    "Red Bull Renault": "Red Bull",
    "Williams Renault":	"Williams",
    "Force India Ferrari": "Aston Martin",
    "Sauber Ferrari": "Sauber"
}

def machineLearningTraining(df):
    return

def main():
    machineLearningTraining(dataProcessing())

main()

