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

    # Replace every NC (Not Classfied) and DQ (disqualified) position with 26
    mergedResults["Position Race"] = mergedResults["Position Race"].replace("NC", 26).replace("DQ", 26)
    mergedResults["Position Quali"] = mergedResults["Position Quali"].replace("NC", 26).replace("DQ", 26)

    # Replace DNF (Did Not Finish) and DNS (Did Not Start) Q3 times
    # Need to encode categorical data like driver names, team names, and race location

    print(qualificationResults.head())
    print(raceResults.head())
    print(mergedResults.head())


def main():
    dataProcessing()


main()

