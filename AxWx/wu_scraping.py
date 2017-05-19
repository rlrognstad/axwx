
"""
Weather Underground Scraping Module

Code to scrape various datasets from wunderground's PWS network

"""

import csv
import time

from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests


def scrape_data_one_day(station_id, year, month, day):
    """
    Retrieve PWS data for given station and a given day
    :param station_id: string
        PWS station ID
    :param year: int
        year
    :param month: int
        month
    :param day: int
        day
    :return: pandas DataFrame with data for requested day

    Sample URL:
    https://www.wunderground.com/weatherstation/WXDailyHistory.asp?
    ID=KWAEDMON15&day=18&month=4&year=2017&graphspan=day&format=1

    """

    url = "https://www.wunderground.com/" \
          "weatherstation/WXDailyHistory.asp?ID=" \
          + station_id + "&day=" \
          + str(day) + "&month=" \
          + str(month) + "&year=" \
          + str(year) \
          + "&graphspan=day&format=1"

    content = requests.get(url).text
    content = content.replace("\n", "")
    content = content.replace("<br>", "\n")
    content = content.replace(",\n", "\n")

    data_csv_lines = csv.reader(content.split('\n'), delimiter=',')
    data_list = list(data_csv_lines)
    data_df = pd.DataFrame.from_records(data_list[1:-1], columns=data_list[0])

    return data_df


def scrape_data_multi_day(station_id, start_date, end_date,
                          delay=3, combined_df=None):
    """
    Retrieve PWS data for given station and a given date range
    :param station_id: string
        PWS station ID
    :param startdate: int (yyyymmdd)
        start date for data retrieval
    :param enddate: int (yyyymmdd)
        end date for data retrieval
    :param delay: int
        delay between requests to WU server (seconds)
    :return: pandas DataFrame with combined data for period requested
    """

    if combined_df is None:
        combined_df = pd.DataFrame()
    else:
        pass

    # parse out date components
    start_date_str = str(start_date)
    start_date_yyyy = int(start_date_str[0:4])
    start_date_mm = int(start_date_str[4:6])
    start_date_dd = int(start_date_str[6:8])
    end_date_str = str(end_date)
    end_date_yyyy = int(end_date_str[0:4])
    end_date_mm = int(end_date_str[4:6])
    end_date_dd = int(end_date_str[6:8])

    # create date range
    start_date_pd = pd.datetime(start_date_yyyy, start_date_mm, start_date_dd)
    end_date_pd = pd.datetime(end_date_yyyy, end_date_mm, end_date_dd)
    date_list = pd.date_range(start_date_pd, end_date_pd)

    for date in date_list:
        temp_yyyy = date.year
        temp_mm = date.month
        temp_dd = date.day
        print('retrieving data for ' + station_id + " on " +
              str(temp_yyyy) + "-" + str(temp_mm) + "-" + str(temp_dd))
        day_df = scrape_data_one_day(station_id=station_id, year=temp_yyyy,
                                     month=temp_mm, day=temp_dd)
        combined_df = combined_df.append(day_df, ignore_index=True)
        time.sleep(delay)

    return combined_df

# examples to run
# single_day = scrape_data_one_day(station_id="KWAEDMON15",
# year=2016, month=9, day=10)
# multi_day = scrape_data_multi_day("KWAEDMON15", 20170217, 20170219)


def scrape_station_info(state="WA"):

    """
    A script to scrape the station information published at the following URL:
    https://www.wunderground.com/weatherstation/ListStations.asp?
    selectedState=WA&selectedCountry=United+States&MR=1
    :param state: US State by which to subset WU Station table
    :return: numpy array with station info
    """
    url = "https://www.wunderground.com/" \
          "weatherstation/ListStations.asp?selectedState=" \
          + state + "&selectedCountry=United+States&MR=1"
    raw_site_content = requests.get(url).content
    soup = BeautifulSoup(raw_site_content, 'html.parser')

    list_stations_info = soup.find_all("tr")

    all_station_info = np.array(['id', 'neighborhood', 'city', 'type'])

    for i in range(1, len(list_stations_info)):  # start at 1 to omit headers

        station_info = str(list_stations_info[i]).splitlines()

        # pull out station info
        station_id = station_info[1].split('ID=')[1].split('"')[0]
        station_neighborhood = station_info[2].split('<td>')[1]
        station_neighborhood = station_neighborhood.split('\xa0')[0]
        station_city = station_info[3].split('<td>')[1].split('\xa0')[0]
        station_type = station_info[4].split('station-type">')[1]
        station_type = station_type.split('\xa0')[0]

        station_id = station_id.strip()
        station_neighborhood = station_neighborhood.strip()
        station_city = station_city.strip()
        station_type = station_type.strip()

        all_station_info = np.vstack([all_station_info,
                                      [station_id, station_neighborhood,
                                       station_city, station_type]])

    return all_station_info


# all_info = scrape_station_info()
# print(all_info[:,0][0:30])