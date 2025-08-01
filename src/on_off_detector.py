import pandas as pd
import matplotlib.pyplot as plt
import mplcursors
import csv
import statistics
from pathlib import Path
from datetime import datetime
from itertools import zip_longest

# variables
date = ''
start_time = ''
end_time = ''
file_path = ''
    
# functions
def define_folder(column_name, output):
    global file_path
    
    # Makes the path of the folder and output file
    file_path = Path(f'{column_name}') / output
    # Creates the directory
    file_path.parent.mkdir(parents=True,exist_ok=True)

def on_off_detector(value, time, date_local, off_value):
    global date
    global start_time
    global end_time
    
    # Checks if start_time is empty or not
    if start_time != '':
        # If start time isn't empty check if end_time is empty and checks value against the provided value
        if end_time == '' and value < off_value:
            # If statement returns true, then both the date and time is recorded as end_time
            end_time = f'{date_local} {time}'
    # If empty, checks the value against the provided off value
    elif value > off_value:
        # Sets the start_time
        start_time = time
        # Records the date
        date = date_local
         
def read(csv_file,column_name, column_number, off_value):
    global date
    global start_time
    global end_time
    global file_path
    
    # CSV file is read with pandas' read_csv(), 
    # only the first column and indicated column is used, 
    # the first row is skipped due to headers
    df = pd.read_csv(f'{csv_file}', usecols=[0, column_number], header=1, names=['DateTime', f'{column_name}'])

    # The first column is converted to DateTime objects with a specific format
    df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce', format='%Y-%m-%d %H:%M:%S')
    # The date is taken put into a separate column
    df['date'] = df['DateTime'].dt.date
    # The time is taken and put into a separate column
    df['time'] = df['DateTime'].dt.time

    # The indicated device column is stripped of any non-numeric characters
    df[f'{column_name}'] = df[f'{column_name}'].astype(str).str.replace('[^0-9.-]', '', regex=True)
    # Then is converted into a numeric value
    df[f'{column_name}'] = pd.to_numeric(df[f'{column_name}'], errors='coerce')

    # A device specific folder and an output file is initialized
    define_folder(f'{column_name}', f'{column_name}_output.csv')
    file = open(file_path, 'w')
    
    # Off value calculation method testing
    off_value = off_value_calc(df[f'{column_name}'].tolist())
    print(off_value)
    
    for _, row in df.iterrows():
        # Time, date, and numeric value of each row is stored temporarily
        date_local= str(row['date'])
        time = str(row['time'])
        value = row[f'{column_name}']

        # Values are then passed to on_off_detector
        on_off_detector(value, time, date_local, off_value)
        
        # Checks if all values are filled
        if date != '' and start_time != '' and end_time != '':
            # If all values are filled, then they're formatted into a string and written to output file
            file.write(f'{date} {start_time},{end_time}\n')
            # Values are reset
            date = ''
            start_time = ''
            end_time = ''
    
    # File is closed, reading is done
    file.close()

def duration(column_name):
    global file_path
    
    df = pd.read_csv(f'{column_name}/{column_name}_output.csv', names=['start_time', 'end_time'])
    
    # Turns the start_time column into a datetime with only date
    # Used later to check if the on state goes into the day
    df['date'] = pd.to_datetime(df['start_time']).dt.date
    # Turns both start_time and end_time to datetimes
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    
    # Duration is found by subtracting end_time and start_time and put into a new column
    # The difference is then divided by Timedelta to get the duration in hours
    df['duration'] = (df['end_time'] - df['start_time']) / pd.Timedelta(hours=1)
    
    # Create an output file
    define_folder(f'{column_name}', f'{column_name}_duration.csv')
    file = open(file_path, 'w')
    
    # Writes duration into the output file
    for _, row in df.iterrows():
        
        duration = row['duration']
        
        # Checks if the on state goes into the next day
        # No other use aside from presenting it
        if(row['start_time'].date() != row['end_time'].date()):
            to_next_day = True
        else:
            to_next_day = False

        file.write(f'{row['date']},{duration},{to_next_day}\n')
    file.close()
    
    # Reads the output file
    df = pd.read_csv(f'{column_name}/{column_name}_duration.csv', usecols=[1], names = ['duration'])
    
    # Obtain a Series of all unique values and their frequency
    durations = df['duration'].value_counts()
    # Sorted before plotting
    durations = durations.sort_index()
    
    plt.subplot(2, 2, 1)
    durations.plot(kind='bar', edgecolor='black')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.xlabel('Duration (hrs)')
    plt.ylabel('Frequency')
    plt.title('Frequency of Duration')

def day_occurence(column_name):
    global file_path
    
    # 4am to 10am
    morning = 0 
    # 10am to 4pm
    midday = 0
    # 4pm to 10pm
    evening = 0
    # 10pm to 4am
    late_night = 0
    
    df = pd.read_csv(f'{column_name}/{column_name}_output.csv', names=['start_time', 'end_time'])
    # Gets date from start_time 
    df['date'] = pd.to_datetime(df['start_time']).dt.date
    # Gets time from both start_time and end_time
    df['start_time'] = pd.to_datetime(df['start_time']).dt.time
    df['end_time'] = pd.to_datetime(df['end_time']).dt.time
    
    # Create output file
    define_folder(f'{column_name}', f'{column_name}_day_occurence.csv')
    file = open(file_path, 'w')
    
    # Set up time values
    morning_time = datetime(2000, 1, 1, hour=4).time()
    midday_time = datetime(2000, 1, 1, hour=10).time()
    evening_time = datetime(2000, 1, 1, hour=16).time()
    late_night_time = datetime(2000, 1, 1, hour=22).time()
    
    # Goes through each row of data and checks the start_time against the set time values
    # Records the start_time by adding to the counter of the respective time of day
    for _, row in df.iterrows():
        time = row['start_time']
        if time >= morning_time:
            if time >= midday_time:
                if time >= evening_time:
                    if time >= late_night_time:
                        late_night = late_night + 1
                    else:
                        evening = evening + 1
                else:
                    midday = midday + 1
            else: 
                morning = morning + 1
        else:
            late_night = late_night + 1
    
    # Writes to file the occurences for each time of day
    file.write(f'morning,{morning}\nmidday,{midday}\nevening,{evening}\nlate_night,{late_night}') 
    file.close()
    
    # Reads the output file
    df = pd.read_csv(f'{column_name}/{column_name}_day_occurence.csv', header=None, names=['time_of_day', 'occurences'])
    
    # Bar plot is used
    plt.subplot(2, 2, 2)
    plt.bar(df['time_of_day'], df['occurences'], edgecolor='black')
    plt.title('Occurences by Time of Day')
    plt.ylabel('Occurrences')
    plt.xlabel('Time of Day')
    plt.tight_layout()

def day_occurence_mode(column_name):
    global file_path
    
    df = pd.read_csv(f'{column_name}/{column_name}_output.csv', names=['start_time', 'end_time'])
    df['date'] = pd.to_datetime(df['start_time']).dt.date
    
    # Initate the times as just datetimes first
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    # Get duration
    df['duration'] = (df['end_time'] - df['start_time']) / pd.Timedelta(hours=1)
    # Duration obtained, strip the times to just time
    df['start_time'] = df['start_time'].dt.time
    df['end_time'] = df['end_time'].dt.time
    
    # Create output file
    define_folder(f'{column_name}', f'{column_name}_day_occurence_hours.csv')
    file = open(file_path, 'w')

    # Write headers
    file.write('morning,midday,evening,late_night\n')
    
    # Set time values
    morning_time = datetime(2000, 1, 1, hour=4).time()
    midday_time = datetime(2000, 1, 1, hour=10).time()
    evening_time = datetime(2000, 1, 1, hour=16).time()
    late_night_time = datetime(2000, 1, 1, hour=22).time()
    
    # Similar to day_occurence(), checks against set time values
    # However, this time, duration is recorded instead into the respective columns
    for _, row in df.iterrows():
        time = row['start_time']
        duration = row['duration']
        if time >= morning_time:
            if time >= midday_time:
                if time >= evening_time:
                    if time >= late_night_time:
                        file.write(',,,' + str(duration) + '\n')
                    else:
                        file.write(',,' + str(duration) + ',\n')
                else:
                    file.write(',' + str(duration) + ',,\n')
            else: 
                file.write(str(duration) + ',,,\n')
        else:
            file.write(',,,' + str(duration) + '\n')
            
    file.close()
    
    # Reads output file
    df = pd.read_csv(f'{column_name}/{column_name}_day_occurence_hours.csv', header=1, names=['morning','midday','evening','late_night'])
    # Create dictionary to get the mode(s) of each time of day
    # Mode(s) were obtained via the inbuilt mode() of DataFrames 
    data = {
        'morning': df['morning'].mode().to_list(),
        'midday': df['midday'].mode().to_list(),
        'evening': df['evening'].mode().to_list(),
        'late_night': df['late_night'].mode().to_list(),
    }
    
    # Create output file
    define_folder(f'{column_name}', f'{column_name}_day_occurence_mode.csv')
    file = open(file_path, 'w', newline='')
    # Using csv module this time to write the new data
    writer = csv.writer(file)
    
    # The keys of the data dict will be used as headers
    headers = list(data.keys())
    # The values and the associated header/key will are obtained
    transposed_data = list(zip_longest(*data.values(), fillvalue=''))

    # csv writer is used here to write them
    writer.writerow(headers)
    writer.writerows(transposed_data)
    
    x = []
    y = []

    # Values are associated with their respective keys for plotting
    for x_label, y_values in data.items():
        for y_val in y_values:
            x.append(x_label)
            y.append(y_val)
    
    plt.subplot(2,2,3)
    plt.scatter(x,y)
    plt.xlabel('Time of Day')
    plt.ylabel('Common Duration (hrs)')
    plt.title('Common Durations by Time of Day')
    plt.tight_layout()
    
def day_occurence_mean(column_name):
    global file_path
    
    df = pd.read_csv(f'{column_name}/{column_name}_output.csv', names=['start_time', 'end_time'])
    df['date'] = pd.to_datetime(df['start_time']).dt.date
    
    # Initate the times as just datetimes first
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    # Get duration
    df['duration'] = (df['end_time'] - df['start_time']) / pd.Timedelta(hours=1)
    # Duration obtained, strip the times to just time
    df['start_time'] = df['start_time'].dt.time
    df['end_time'] = df['end_time'].dt.time
    
    # Similar to mode, however, this time for finding and presenting the mean
    df = pd.read_csv(f'{column_name}/{column_name}_day_occurence_hours.csv', header=1, names=['morning','midday','evening','late_night'])
    data = {
        'morning': df['morning'].mean(),
        'midday': df['midday'].mean(),
        'evening': df['evening'].mean(),
        'late_night': df['late_night'].mean(),
    }
    
    define_folder(f'{column_name}', f'{column_name}_day_occurence_mean.csv')
    file = open(file_path, 'w')
    
    for x_label, y_value in data.items():
        file.write(f'{x_label},{y_value}\n')
    
    file.close()
        
    x = []
    y = []

    for x_label, y_values in data.items():
        x.append(x_label)
        y.append(y_values)
    
    # A bar plot instead of scatter like mode
    plt.subplot(2,2,4)
    plt.bar(x,y, edgecolor='black')
    plt.xlabel('Time of Day')
    plt.ylabel('Average Duration (hrs)')
    plt.title('Average Durations by Time of Day')
    plt.tight_layout()

def non_overlapping_plot(column_name):
    global file_path
    
    df1 = pd.read_csv(f'{column_name}/{column_name}_output.csv', header=None, names=['start_time', 'end_time'])

    df1['start_time'] = pd.to_datetime(df1['start_time'])
    df1['end_time'] = pd.to_datetime(df1['end_time'])
    
    # Take data, and format it
    full_range = pd.date_range(start=df1['start_time'].min(), end=df1['end_time'].max(), freq='15min')
    # Turn it into a series
    on_off_series = pd.Series(0, index=full_range)

    # Set the value when the device is on to 1
    for _, row in df1.iterrows():
        on_off_series.loc[row['start_time']:row['end_time']] = 1

    # Plot
    on_off_series.plot(drawstyle='steps-post', title='On/Off State', figsize=(12,6.75))
    plt.ylabel('State (0 = Off, 1 = On)')
    plt.xlabel('Time')
    plt.grid(True)
    plt.tight_layout()
    
def overlapping_plot (column_name):
    global file_path
    
    df1 = pd.read_csv(f'{column_name}/{column_name}_output.csv', header=None, names=['start_time', 'end_time'])

    df1['start_time'] = pd.to_datetime(df1['start_time'])
    df1['end_time'] = pd.to_datetime(df1['end_time'])

    # Format
    time_index = pd.date_range(start=df1['start_time'].min(), end=df1['end_time'].max(), freq='15min')

    # Turn it into a dataframe
    on_off = pd.DataFrame({'timestamp': time_index})
    # Separate the date and time
    on_off['date'] = on_off['timestamp'].dt.date
    on_off['time'] = on_off['timestamp'].dt.time
    # Initate state
    on_off['state'] = 0

    # Change areas of state to 1 if on
    for _, row in df1.iterrows():
        mask = (on_off['timestamp'] >= row['start_time']) & (on_off['timestamp'] <= row['end_time'])
        on_off.loc[mask, 'state'] = 1
    
    # Pivot, make mulitple lines of data
    pivot = on_off.pivot(index='time', columns='date', values='state')

    # Plot
    pivot.plot(title='Overlapping On/Off Patterns',figsize=(12,6.75))
    plt.ylabel('State (0 = Off, 1 = On)')
    plt.xlabel('Time of Day')
    plt.grid(True)
    plt.legend().set_visible(False)

def occurence_by_day_of_week(column_name):
    global file_path
    
    # Set up dict
    data = {
        'Monday': 0,
        'Tuesday': 0,
        'Wednesday': 0,
        'Thursday': 0,
        'Friday': 0,
        'Saturday': 0,
        'Sunday': 0,
    }
    
    df = pd.read_csv(f'{column_name}/{column_name}_output.csv', names=['start_time', 'end_time'])
    # By using day_name(), we can get the name of day and use it to update the data dict
    df['start_time'] = pd.to_datetime(df['start_time']).dt.day_name()
    
    # Using the string from day_name() and usage of get(key), it can update the data dict
    for _, row in df.iterrows():
        key = row['start_time']
        data.update({key: data.get(key) + 1})

    define_folder(f'{column_name}', f'{column_name}_occurence_by_day_of_week.csv')
    file = open(file_path, 'w')
    
    for key in data:
        file.write(f'{key},{data.get(key)}\n')
    
    # bar plot
    plt.subplot(2,2,1)    
    plt.bar(list(data.keys()), list(data.values()))
    plt.xticks(rotation=30)
    plt.xlabel('Days of Week')
    plt.ylabel('Occurence')
    plt.title('Occurence by Days of Week')

def duration_by_day_of_week(column_name):
    global file_path
    
    # Similar to previous function, this time, the duration is appended to the list
    data = {
        'Monday': [],
        'Tuesday': [],
        'Wednesday': [],
        'Thursday': [],
        'Friday': [],
        'Saturday': [],
        'Sunday': [] 
    } 
    
    df = pd.read_csv(f'{column_name}/{column_name}_duration.csv', names=['date', 'duration', 'to_next_day'])
    df['date'] = pd.to_datetime(df['date']).dt.day_name()
    
    define_folder(f'{column_name}', f'{column_name}_duration_by_day_of_week.csv')
    file = open(file_path, 'w', newline='')
    
    writer = csv.writer(file)
    
    for _, row in df.iterrows():
        day = row['date']
        duration = row['duration']
        data[day].append(duration)
    
    # headers and data is transposed
    headers = list(data.keys())
    transposed_data = list(zip_longest(*data.values(), fillvalue=''))

    # csv writer is used
    writer.writerow(headers)
    writer.writerows(transposed_data)
    file.close()
    
    x = []
    y = []

    for x_label, y_values in data.items():
        for y_val in y_values:
            x.append(x_label)
            y.append(y_val)
    
    # Scatter plot was considered best to show, though quantity is an issue
    # Would need individual graphs for each day
    plt.subplot(2,2,2)
    plt.scatter(x,y)
    plt.xlabel('Day of Week')
    plt.ylabel('Duration (hrs)')
    plt.title('Durations by Day of Week')
    plt.tight_layout()
    
def mode_by_day_of_week(column_name):
    global file_path
    
    # Processed data from duration_by_day_of_week() is read
    df = pd.read_csv(f'{column_name}/{column_name}_duration_by_day_of_week.csv', header=1, names=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
    # Used inbuilt mode function from pandas / dataframe
    data = {
        'Monday': df['Monday'].mode().to_list(),
        'Tuesday': df['Tuesday'].mode().to_list(),
        'Wednesday': df['Wednesday'].mode().to_list(),
        'Thursday': df['Thursday'].mode().to_list(),
        'Friday': df['Friday'].mode().to_list(),
        'Saturday': df['Saturday'].mode().to_list(),
        'Sunday': df['Sunday'].mode().to_list()
    }
    
    x = []
    y = []

    # Create coordinates
    for x_label, y_values in data.items():
        for y_val in y_values:
            x.append(x_label)
            y.append(y_val)
    
    # Scatter plot
    plt.subplot(2,2,3)
    plt.scatter(x,y)
    plt.xlabel('Day of Week')
    plt.ylabel('Common Duration (hrs)')
    plt.title('Common Durations by Day of Week')
    plt.tight_layout()
    
def mean_by_day_of_week(column_name):
    global file_path
    
    # Same as mode_by_day_of_week(), read data from duration_by_day_of_week()
    df = pd.read_csv(f'{column_name}/{column_name}_duration_by_day_of_week.csv', header=1, names=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
    # This time use inbuilt mean()
    data = {
        'Monday': df['Monday'].mean(),
        'Tuesday': df['Tuesday'].mean(),
        'Wednesday': df['Wednesday'].mean(),
        'Thursday': df['Thursday'].mean(),
        'Friday': df['Friday'].mean(),
        'Saturday': df['Saturday'].mean(),
        'Sunday': df['Sunday'].mean()
    }
    
    define_folder(f'{column_name}', f'{column_name}_mean_by_day_of_week.csv')
    file = open(file_path, 'w')
    
    for x_label, y_value in data.items():
        file.write(f'{x_label},{y_value}\n')
    
    file.close()
        
    x = []
    y = []

    for x_label, y_values in data.items():
        x.append(x_label)
        y.append(y_values)
    
    # Bar plot
    plt.subplot(2,2,4)
    plt.bar(x, y, edgecolor='black')
    plt.xlabel('Day of Week')
    plt.ylabel('Average Duration (hrs)')
    plt.title('Average Durations by Day of Week')
    plt.tight_layout()

# Experimental method to calculate off values
def off_value_calc(list):
    # Initialize count and sum
    count = 0
    sum = 0
    mode = statistics.mode(list)

    # Get max and min values
    temp_max = max(list)
    temp_min = min(list)
    test = temp_max
    
    # Add the difference to the sum
    sum = sum + (temp_max - temp_min)
    count = count + 1
    
    # Remove the min and max    
    list.remove(temp_max)
    list.remove(temp_min)
    
    # Get new min and max
    temp_max = max(list)
    temp_min = min(list)
    
    # Set while loop to repeat previous statements until the average exceeds the difference
    # (temp_max - temp_min) < (sum / count)
    while((temp_max - temp_min) < (sum / count) and len(list) > 2):
        try:
            list.remove(temp_max)
            list.remove(temp_min)
            sum = sum + (temp_max - temp_min)
            count = count + 1
        except ValueError:
            temp_max = max(list)
            temp_min = min(list)

        # try:
        #     list.remove(temp_max)
        # except ValueError:
        #     print()
        
        # try:
        #     list.remove(temp_min)
        # except ValueError:
        #     print()
        
        # temp_max = max(list)
        # temp_min = min(list) 
    
    # Return the average as off value  
    # return pow(sum / count)
    return (sum / count)

# main processes

def main(device, column_number, off_value):
    read('NewProfiles.csv',device,column_number,off_value)

    non_overlapping_plot(device) 
    overlapping_plot(device)

    plt.figure(figsize=(12,6.75))
    duration(device)
    day_occurence(device)
    day_occurence_mode(device)
    day_occurence_mean(device)
    
    plt.figure(figsize=(12,6.75))
    occurence_by_day_of_week(device)
    duration_by_day_of_week(device)
    mode_by_day_of_week(device)
    mean_by_day_of_week(device)

    mplcursors.cursor(hover=True)
    plt.show()
    
# main('car', 1, 0.005)
# main('dishwasher', 2, 0.01)
# main('kitchen', 3, 0.005)
# main('microwave', 4, 0.005)
# main('range', 5, 0.005)
# main('bathroom', 6, 0.25)
# main('bedroom', 7, 0.9)
# main('living_room', 8, 0.01)
# main('clothes_washer', 9, 0.005)

# Testing experimental method
read('NewProfiles.csv','car',1,0.005)
read('NewProfiles.csv','dishwasher',2,0.01)
read('NewProfiles.csv','kitchen',3,0.005)
read('NewProfiles.csv','microwave',4,0.005)
read('NewProfiles.csv','range',5,0.005)
read('NewProfiles.csv','bathroom',6,0.25)
read('NewProfiles.csv','bedroom',7,0.9)