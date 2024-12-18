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
    mergedResults["Race DNF"] = mergedResults["Time"].apply(lambda x: 1 if x == "DNF" else 0)

    # FOLLOWING CODE BROKEN ATM (need to figure out sorting)
    #mergedResults = mergedResults.sort_values(by=['Year', 'Team', 'Race'])
    mergedResults["Team Season DNF"] = (mergedResults.groupby(["Year", "Team"])["Race DNF"]
                                        .cumsum()
                                        .shift(1, fill_value=0))
    mergedResults["Season Points"] = (mergedResults.groupby(["Year", "Driver"])["Points"]
                                      .cumsum()
                                      .shift(1, fill_value=0))
    mergedResults = mergedResults.reset_index().sort_values(by="index")
    
    # Replace DNF (Did Not Finish) and DNS (Did Not Start) Q3 times
    # Need to encode categorical data like driver names, team names, and race location

    print(qualificationResults.head())
    print(raceResults.head(25))
    print(mergedResults.head(50))


def main():
    dataProcessing()


main()

