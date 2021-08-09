# File: DesktopApplication.py
# Description: Professional Practice Week (CET235 - Internet of Things)
# Author: Yi Zhan Wong, University of Sunderland
# Date: May 2020

#  Import
from datetime import datetime

# Array for the readings for log.csv
readings = []

# Initialise variable for log.csv
file_name = "log.csv"

#  Open log.csv for reading
file = open(file_name, "r")

#  Make sure read file start from first line
is_first = True

#  Read every line in CSV file
for line in file:
    if is_first:
        is_first = False

        continue

    #  Spilt values between comma
    values = line.split(",")

    FMD = "%a %d-%m-%Y"  # format for date
    FMT = "%H:%M:%S"  # format for time

    #  Dictionary for reading the values from CSV file
    reading = dict(user=values[0],
                   date=values[1],
                   time=values[2],
                   temperature=float(values[3]),
                   humidity=float(values[4]))

    # Append reading to readings list
    readings.append(reading)

# Array to include dew point temperature named processed_readings
processed_readings = []
for reading in readings:
    # Formulae for the dew point temperature
    Td = float(reading["temperature"]) - ((100.0 - float(reading["humidity"])) / 5.0)
    # Rearrange the headers for processed_readings
    processed_reading = (
        reading["user"], reading["date"], reading["time"], reading["temperature"], reading["humidity"], Td)
    # Append processed_reading to processed_readings list
    processed_readings.append(processed_reading)

# Highest temperature reading recorded
highest = processed_readings[3]
for processed_reading in processed_readings:
    if processed_reading[3] > highest[3]:
        # Check each processed_reading to see if its temperature is higher than the current highest temperature,
        # if so then swap this as the newest high temperature
        # whole reading is selected
        highest = processed_reading

        # Select temperature value to display
        v1 = highest[3]

# Lowest dew point temperature reading recorded
lowest = processed_readings[5]
for processed_reading in processed_readings:
    if processed_reading[5] < lowest[5]:
        # Check each processed_reading to see if its dew point temperature is lower than the current lowest dew point
        # temperature,if so then swap this as the newest low dew point temperature
        # whole reading is selected
        lowest = processed_reading

        # Select dew point temperature value to display
        v2 = lowest[5]

sdate = processed_readings[0][1]  # start date
stime = processed_readings[0][2]  # start time
edate = processed_readings[-1][1]  # end date
etime = processed_readings[-1][2]  # end time

taken = 0  # Initialised time taken = 0
taken = datetime.strptime(etime, FMT) - datetime.strptime(stime, FMT)  # access time calculation

print()
print("Read from file name: {0}".format(file_name))  # display file name
print()
print("User: {0}".format(processed_readings[2][0]))
print("Start: ", sdate, stime)  # display start date and time
print("End: ", edate, etime)  # display end date and time
print("Access period: {0}".format(taken))  # display access period (format h:mm:ss)
print("Highest temperature: {0} C".format(v1))  # display highest temperature recorded
print("Lowest calculate dew point temperature: {0:.2f}".format(v2))  # display lowest dew point temperature recorded
print()
print("Readings from sensor:")  # display all readings include dew point temperature
for reading in processed_readings:
    # Display user id, date, time ,temperature, humidity and dew point temperature per second
    print("User: {0} "
          "Date: {1} "
          "Time: {2} "
          "Temperature: {3:.2f} "
          "Humidity: {4:.2f} "
          "Dew point temperature: {5:.2f}".format(reading[0], reading[1], reading[2], reading[3], reading[4],
                                                  reading[5]))

# Exit
print()
print("Finished")
