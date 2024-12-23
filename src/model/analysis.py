import pandas as pd


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
    # Now drop unnecessary Q1 and Q2 columns
    mergedResults = mergedResults.drop(["Q1", "Q2"], axis=1)

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

    # Some qualification time delta feature
    # Replace DNF (Did Not Finish) and DNS (Did Not Start) Q3 times
    # Drop unnecessary columns
    # Normalise data
    # Need to encode categorical data like driver names, team names, and race location

    print(qualificationResults.head())
    print(raceResults.head(25))
    print(teamDNFs.head(50))
    print(last5.head(50))
    print(mergedResults.head(50))


def main():
    dataProcessing()


main()

