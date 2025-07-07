import pandas as pd
import matplotlib.pyplot as plt
import mplcursors
import csv
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
    
    file_path = Path(f'{column_name}') / output
    file_path.parent.mkdir(parents=True,exist_ok=True)

def on_off_detector(value, time, date_local, off_value):
    global date
    global start_time
    global end_time
    
    if start_time != '':
        if end_time == '' and value < off_value:
            end_time = f'{date_local} {time}'
    elif value > off_value:
        start_time = time
        date = date_local
         
def read(csv_file,column_name, column_number, off_value):
    global date
    global start_time
    global end_time
    global file_path
    
    df = pd.read_csv(f'{csv_file}', usecols=[0, column_number], header=1, names=['DateTime', f'{column_name}'])

    df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce', format='%Y-%m-%d %H:%M:%S')
    df['date'] = df['DateTime'].dt.date
    df['time'] = df['DateTime'].dt.time

    df[f'{column_name}'] = df[f'{column_name}'].astype(str).str.replace('[^0-9.-]', '', regex=True)
    df[f'{column_name}'] = pd.to_numeric(df[f'{column_name}'], errors='coerce')

    define_folder(f'{column_name}', f'{column_name}_output.csv')
    file = open(file_path, 'w')
        
    for _, row in df.iterrows():
        date_local= str(row['date'])
        time = str(row['time'])
        value = row[f'{column_name}']

        on_off_detector(value, time, date_local, off_value)
        if date != '' and start_time != '' and end_time != '':
            file.write(f'{date} {start_time},{end_time}\n')
            date = ''
            start_time = ''
            end_time = ''
    file.close()

def duration(column_name):
    global file_path
    
    df = pd.read_csv(f'{column_name}/{column_name}_output.csv', names=['start_time', 'end_time'])
    df['date'] = pd.to_datetime(df['start_time']).dt.date
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    
    df['duration'] = (df['end_time'] - df['start_time']) / pd.Timedelta(hours=1)
    
    define_folder(f'{column_name}', f'{column_name}_duration.csv')
    file = open(file_path, 'w')
    
    for _, row in df.iterrows():
        
        duration = row['duration']
        
        if(row['start_time'].date() != row['end_time'].date()):
            to_next_day = True
        else:
            to_next_day = False

        file.write(f'{row['date']},{duration},{to_next_day}\n')
    file.close()
    
    df = pd.read_csv(f'{column_name}/{column_name}_duration.csv', usecols=[1], names = ['duration'])
    
    durations = df['duration'].value_counts()
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
    df['date'] = pd.to_datetime(df['start_time']).dt.date
    df['start_time'] = pd.to_datetime(df['start_time']).dt.time
    df['end_time'] = pd.to_datetime(df['end_time']).dt.time
    
    define_folder(f'{column_name}', f'{column_name}_day_occurence.csv')
    file = open(file_path, 'w')
    
    morning_time = datetime(2000, 1, 1, hour=4).time()
    midday_time = datetime(2000, 1, 1, hour=10).time()
    evening_time = datetime(2000, 1, 1, hour=16).time()
    late_night_time = datetime(2000, 1, 1, hour=22).time()
    
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
    file.write(f'morning,{morning}\nmidday,{midday}\nevening,{evening}\nlate_nigh,{late_night}') 
    file.close()
    
    df = pd.read_csv(f'{column_name}/{column_name}_day_occurence.csv', header=None, names=['time_of_day', 'occurences'])
    
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
    
    define_folder(f'{column_name}', f'{column_name}_day_occurence_hours.csv')
    file = open(file_path, 'w')

    file.write('morning,midday,evening,late_night\n')
    
    morning_time = datetime(2000, 1, 1, hour=4).time()
    midday_time = datetime(2000, 1, 1, hour=10).time()
    evening_time = datetime(2000, 1, 1, hour=16).time()
    late_night_time = datetime(2000, 1, 1, hour=22).time()
    
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
    
    df = pd.read_csv(f'{column_name}/{column_name}_day_occurence_hours.csv', header=1, names=['morning','midday','evening','late_night'])
    data = {
        'morning': df['morning'].mode().to_list(),
        'midday': df['midday'].mode().to_list(),
        'evening': df['evening'].mode().to_list(),
        'late_night': df['late_night'].mode().to_list(),
    }
    
    define_folder(f'{column_name}', f'{column_name}_day_occurence_mode.csv')
    file = open(file_path, 'w', newline='')
    writer = csv.writer(file)
            
    headers = list(data.keys())
    transposed_data = list(zip_longest(*data.values(), fillvalue=''))

    writer.writerow(headers)
    writer.writerows(transposed_data)
    
    x = []
    y = []

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
    
    full_range = pd.date_range(start=df1['start_time'].min(), end=df1['end_time'].max(), freq='15min')
    on_off_series = pd.Series(0, index=full_range)

    for _, row in df1.iterrows():
        on_off_series.loc[row['start_time']:row['end_time']] = 1

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

    time_index = pd.date_range(start=df1['start_time'].min(), end=df1['end_time'].max(), freq='15min')

    on_off = pd.DataFrame({'timestamp': time_index})
    on_off['date'] = on_off['timestamp'].dt.date
    on_off['time'] = on_off['timestamp'].dt.time
    on_off['state'] = 0

    for _, row in df1.iterrows():
        mask = (on_off['timestamp'] >= row['start_time']) & (on_off['timestamp'] <= row['end_time'])
        on_off.loc[mask, 'state'] = 1
        
    pivot = on_off.pivot(index='time', columns='date', values='state')


    pivot.plot(title='Overlapping On/Off Patterns',figsize=(12,6.75))
    plt.ylabel('State (0 = Off, 1 = On)')
    plt.xlabel('Time of Day')
    plt.grid(True)
    plt.legend().set_visible(False)

def occurence_by_day_of_week(column_name):
    global file_path
    
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
    df['start_time'] = pd.to_datetime(df['start_time']).dt.day_name()
    
    for _, row in df.iterrows():
        key = row['start_time']
        data.update({key: data.get(key) + 1})

    define_folder(f'{column_name}', f'{column_name}_occurence_by_day_of_week.csv')
    file = open(file_path, 'w')
    
    for key in data:
        file.write(f'{key},{data.get(key)}\n')
    
    plt.subplot(2,2,1)    
    plt.bar(list(data.keys()), list(data.values()))
    plt.xticks(rotation=45)
    plt.xlabel('Days of Week')
    plt.ylabel('Occurence')
    plt.title('Occurence by Days of Week')

def duration_by_day_of_week(column_name):
    global file_path
    
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
    
    headers = list(data.keys())
    transposed_data = list(zip_longest(*data.values(), fillvalue=''))

    writer.writerow(headers)
    writer.writerows(transposed_data)
    file.close()
    x = []
    y = []

    for x_label, y_values in data.items():
        for y_val in y_values:
            x.append(x_label)
            y.append(y_val)
    
    plt.subplot(2,2,2)
    plt.scatter(x,y)
    plt.xlabel('Day of Week')
    plt.ylabel('Duration (hrs)')
    plt.title('Durations by Day of Week')
    plt.tight_layout()
    
def mode_by_day_of_week(column_name):
    global file_path
    
    df = pd.read_csv(f'{column_name}/{column_name}_duration_by_day_of_week.csv', header=1, names=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
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

    for x_label, y_values in data.items():
        for y_val in y_values:
            x.append(x_label)
            y.append(y_val)
    
    plt.subplot(2,2,3)
    plt.scatter(x,y)
    plt.xlabel('Day of Week')
    plt.ylabel('Common Duration (hrs)')
    plt.title('Common Durations by Day of Week')
    plt.tight_layout()
    
def mean_by_day_of_week(column_name):
    global file_path
    
    df = pd.read_csv(f'{column_name}/{column_name}_duration_by_day_of_week.csv', header=1, names=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
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
    
    plt.subplot(2,2,4)
    plt.bar(x, y, edgecolor='black')
    plt.xlabel('Day of Week')
    plt.ylabel('Average Duration (hrs)')
    plt.title('Average Durations by Day of Week')
    plt.tight_layout()

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
