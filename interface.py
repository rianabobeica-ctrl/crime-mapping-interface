"""
Run Interface - UK Police API Crime Data Search
"""


import pickle
import requests
import csv
#used for task 1-7

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
#used for task 8


# TASK 1 - User Input Functions



def get_neighbourhoods():
    neighbourhoods = []
    print("Enter neighbourhood names (press ENTER with no input to finish):")
    while True:
        name = input("Neighbourhood name: ").strip()
        if name == "":
            if neighbourhoods:
                break
            else:
                print("Please enter at least one neighbourhood.")
                continue
        neighbourhoods.append(name)
    return neighbourhoods


def get_year():
    while True:
        year = input("Enter year (YYYY): ").strip()
        if year.isdigit() and len(year) == 4:
            return year
        print("Invalid year format. Please enter a 4-digit year (e.g., 2025).")


def get_month():
    month_map = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12"
    }
    while True:
        month = input("Enter month (MM or month name): ").strip().lower()
        if month.isdigit():
            month = month.zfill(2)
            if 1 <= int(month) <= 12:
                return month
        if month in month_map:
            return month_map[month]
        print("Invalid month. Please enter a number (1–12), MM format, or month name.")


def get_crime_category():
    valid_categories = [
        "anti-social-behaviour", "burglary", "criminal-damage-arson", "drugs",
        "other-theft", "possession-of-weapons", "public-order", "robbery",
        "shoplifting", "theft-from-the-person", "vehicle-crime", "violent-crime",
        "other-crime"
    ]
    print("\nAvailable crime categories:")
    for category in valid_categories:
        print(f"- {category}")
    while True:
        category = input("Enter crime category: ").strip().lower()
        if category in valid_categories:
            return category
        print("Invalid crime category. Please choose from the list above.")
#I tried to not use AI when doing the code,only when i had errors I asked it what is wrong
#and then I figured out the mistakes



# TASK 2 - Get Neighbourhood IDs


def get_neighbourhood_ids(user_inputs):
    """
  Given a list of neighbourhood names, retrieve their unique identifiers
  from the Metropolitan Police API.
  """


    try:
        response = requests.get("https://data.police.uk/api/metropolitan/neighbourhoods")
        response.raise_for_status()
        neighbourhoods = response.json()
    except requests.RequestException as e:
        print(f"Error retrieving neighbourhood data: {e}")
        return {}


    dict_nid = {}
    #Creake lookup table
    api_lookup = {item["name"].lower(): item["id"] for item in neighbourhoods}


    for name in user_inputs:
        key = name.lower()
        if key in api_lookup:
            print(f"{name}: found")
            dict_nid[name] = api_lookup[key]
        else:
            print(f"{name}: NOT found")
    return dict_nid



# TASK 3 - Get Neighbourhood Boundaries


def get_neighbourhood_boundaries(dict_nid):
    dict_boundaries = {}
    for name, nid in dict_nid.items():
        url = f"https://data.police.uk/api/metropolitan/{nid}/boundary"
        try:
            response = requests.get(url)
            response.raise_for_status()
            boundary_data = response.json()
            coords = [(point["latitude"], point["longitude"]) for point in boundary_data]
            dict_boundaries[name] = coords
            print(f"{name}: boundary retrieved")
        except requests.RequestException as e:
            print(f"{name}: FAILED to retrieve boundary ({e})")
            dict_boundaries[name] = None
    return dict_boundaries




# TASK 5 - Get Crime Data


#AI helped me with this part i dint know how to filter it because it clashed with previous tasks
def get_crime_data_filtered(dict_polygons, year, month, category):
    results = []
    for neighbourhood, polygon in dict_polygons.items():
        url = f"https://data.police.uk/api/crimes-street/{category}?poly={polygon}&date={year}-{month}"
        try:
            response = requests.get(url)
            crimes = response.json()
            for crime in crimes:
                latitude = crime["location"]["latitude"]
                longitude = crime["location"]["longitude"]
                results.append([neighbourhood, category, latitude, longitude])
                
             # Used AI to help with the error handling and closing this part off
        except requests.RequestException:
            print(f"Error retrieving crime data for {neighbourhood}")
    return results




# TASK 6 - Output CSV


def write_results_to_csv(results, filename="crime_results.csv"):
    if not results:
        print("No results to write.")
        return
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Neighbourhood", "Category", "Latitude", "Longitude"])
            for row in results:
                writer.writerow(row)
        print(f"CSV file '{filename}' created successfully.")
    except IOError as e:  #Use AI for errors because i knew i had to include them but i didn't knew how
        print(f"Error writing CSV file: {e}")
        
# TASK 7 - Search
        
def run_search_and_save(neighbourhoods, year, month, category):
    """
    Run a search for a crime category in given neighbourhoods,
    save the results to a CSV file, and return the filename.
    """
    # 1. Get neighbourhood IDs
    dict_nid = get_neighbourhood_ids(neighbourhoods)
    
    # 2. Get boundaries
    dict_boundaries = get_neighbourhood_boundaries(dict_nid)
    
    # 3. Build polygons
    #I struggled with polygons so AI was used here to explain polygons in general and how to apply them here
    dict_polygons = {}
    for name, coords in dict_boundaries.items():
        if coords is None or len(coords) == 0:
            continue
        latitudes = [float(lat) for lat, lon in coords]
        longitudes = [float(lon) for lat, lon in coords]
        min_lat = str(min(latitudes))
        max_lat = str(max(latitudes))
        min_lon = str(min(longitudes))
        max_lon = str(max(longitudes))
        topleft = max_lat + "," + min_lon
        topright = max_lat + "," + max_lon
        bottomright = min_lat + "," + max_lon
        bottomleft = min_lat + "," + min_lon
        polygon = topleft + ":" + topright + ":" + bottomright + ":" + bottomleft
        dict_polygons[name] = polygon


    # 4. Get crime data
    results = get_crime_data_filtered(dict_polygons, year, month, category)
    
    # 5. Save CSV
    filename = f"{category}_{year}_{month}.csv"
    write_results_to_csv(results, filename)
    
    print(f"{category.capitalize()} data saved to {filename}\n")
    return filename
        
#TASK 8
#used AI to help me work out which libraries where needed 
#i was getting errors when trying to run about things not being defined correctrly, i couldnt work out what was wrong so ai helped me to intergrate the code throughout.
def kde(neighbourhood, csv_file):
    #CSV
    df = pd.read_csv(csv_file)

    # filter the neighbourhood to use 
    df = df[df["Neighbourhood"] == neighbourhood]

    if df.empty:
        print(f"No data for {neighbourhood} in {csv_file}")
        return

    # find the coordinates
    lat = df["Latitude"].astype(float).values
    lon = df["Longitude"].astype(float).values

    #make the calculation
    xy = np.vstack([lon, lat])
    kde_func = gaussian_kde(xy)

    # plotting the map
    xmin, xmax = lon.min(), lon.max()
    ymin, ymax = lat.min(), lat.max()

    xx, yy = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
    positions = np.vstack([xx.ravel(), yy.ravel()])
    density = np.reshape(kde_func(positions).T, xx.shape)

    plt.figure(figsize=(8, 6))
    plt.imshow(
        np.rot90(density),
        cmap="hot",
        extent=[xmin, xmax, ymin, ymax]
    )
    plt.scatter(lon, lat, s=5, c="blue", alpha=0.3)
    plt.title(f"KDE Crime Map – {neighbourhood}")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    #isave
    output_name = f"kde_{neighbourhood.replace(' ', '_')}_{csv_file.replace('.csv','')}.png"
    plt.savefig(output_name, dpi=300)
    plt.close()

    print(f"KDE map saved: {output_name}")





# MAIN EXECUTION
# -----------------------------
if __name__ == "__main__": #This is the "controller" part of the function
#This part controls the flow and decides:
#In what order to use the tools
#What variables to pass
#What actions should happen next


    # TASK 1: Get user input
    neighbourhoods = get_neighbourhoods()
    year = get_year()
    month = get_month()
    category = get_crime_category()


    search_parameters = {
        "neighbourhoods": neighbourhoods,
        "year": year,
        "month": month,
        "category": category
    }


    with open("search_parameters.pkl", "wb") as file:
        pickle.dump(search_parameters, file)
    print("\nSearch parameters saved successfully.")


    # TASK 2: Get IDs
    dict_nid = get_neighbourhood_ids(neighbourhoods)
    print("\nNeighbourhood identifier dictionary:")
    print(dict_nid)


    # TASK 3: Get boundaries
    dict_boundaries = get_neighbourhood_boundaries(dict_nid)
    print("\nBoundary coordinate dictionary created.")


    # TASK 4: Build bounding box polygons
    dict_polygons = {}
    #Use of AI here as I was confused as to whether the code would run and it helped me figure it out as the code wouldn't run otherwise 


    for name, coords in dict_boundaries.items():
        if coords is None or len(coords) == 0:
            continue
        latitudes = [float(lat) for lat, lon in coords]
        longitudes = [float(lon) for lat, lon in coords]
        min_lat, max_lat = str(min(latitudes)), str(max(latitudes))
        min_lon, max_lon = str(min(longitudes)), str(max(longitudes))
        
        #Create the bounding box vertices as strings making all the combinations of lat and long
        topleft = max_lat + "," + min_lon
        topright = max_lat + "," + max_lon
        bottomright = min_lat + "," + max_lon
        bottomleft = min_lat + "," + min_lon
        
        #Concatenate these 4 pairs into one new variable polygon
        polygon = topleft + ":" + topright + ":" + bottomright + ":" + bottomleft
        dict_polygons[name] = polygon
        print(f"{name}: bounding box created")


    # TASK 5: Retrieve crime data
    results = get_crime_data_filtered(dict_polygons, year, month, category)
    print(f"\nTotal crimes collected: {len(results)}")


    # TASK 6: Save CSV
    save = input("Do you want to save results to CSV? (y/n): ").strip().lower()
    if save == "y":
        write_results_to_csv(results)
    else:
        print("CSV not saved.")
        
  
    # TASK 7: Neighbourhoods to search
neighbourhoods = [
    "King's Cross",
    "Victoria",
    "Camden Town",
    "London Fields",
    "Bloomsbury",
    "Marylebone"
]
year = "2025"
month = "09"


    # Run robbery search
robbery_file = run_search_and_save(neighbourhoods, year, month, "robbery")


    # Run burglary search
burglary_file = run_search_and_save(neighbourhoods, year, month, "burglary")


print("Six CSV files created.")
    
    #TASK 8-KDE maps
    #when doing task 8 i realised we had made a mistake of only using 2 neighbourhoods so i had to adjust other tasks. ai helped me when certain names weren't working and told me its about the way the API calls them. 
   
print("\nGenerating KDE maps...")

# neighbourhoods (same 6 from earlier tasks)
neighbourhoods = [
    "King's Cross",
    "Victoria",
    "Camden Town",
    "London Fields",
    "Bloomsbury",
    "Marylebone"
]

# crime CSV files created in task 7
crime_files = [
    "robbery_2025_09.csv",
    "burglary_2025_09.csv"
]

# generate KDE maps
for csv_file in crime_files:
    for n in neighbourhoods:
        kde(n, csv_file)

print("all KDE maps created.")
