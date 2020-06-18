#!/usr/bin/env python3
# -*- coding: utf-8 -*-


### This is a separate module from main.py to make it harder to accidentally overwrite the data in influx
### The idea is that the user should review the output from the modeling process before running this script
### to write the data to influxdb
### Constants can be adjusted if the database name, end-use measurement, host address, filename, etc changes.


from datetime import datetime

import pandas as pd
import influxdb

if influxdb.__version__=="5.3.0":
    print("There may be issues with this version of influxdb-python. If you encounter problems try downgrading to 5.2.3 or checking if there is a newer version than 5.3.0.")

## Constants
##--------------
model_output_file_location = 'predicted_end_use_labels.csv'
host_address = '206.12.92.81'
host_port = '8086'
database_name = 'SKYSPARK'
eu_measurement = 'END_USE'

##---------------

prompt = "input path + filename or leave blank for default of "+model_output_file_location
filename_input = input(prompt)
if len(filename_input)>0:
    model_output_file_location=filename_input

username=input("input username:")
password = input("input password:")


#Connect to localdb and test connection by seeing if any databases exist
client = influxdb.DataFrameClient(host=host_address,port=host_port, username=username,password=password,database=database_name)

try:
    client.ping()
except:
    raise Exception("Can not connect to InfluxDB. Is your network connection ok?")

#Load the output from the model into a dataframe
output = pd.read_csv(model_output_file_location)
if 'uniqueID' not in output.columns:
    output.rename(columns={'uniqueId':'uniqueID'}, inplace=True)
if len(output['uniqueID'].unique())<len(output):
    raise Exception("There are duplicated uniqueID's in the data, correct the output file and run again.")


#Add a constant timestamp value and make it the index (influxdb-python expects a timestamp as the index)
#By making it a constant value, it will be simple to overwrite the points in the influxdb 
#  when there is an update.

TIMESTAMP=pd.to_datetime("2020-01-01")
output['time'] = TIMESTAMP
output.set_index(['time'], inplace=True)

#Write new points to the database using influxdb.DataframeClient().write_points()
#Note that all the uniqueId is a tag and the endUseLabel is a field.
#Since there can only be one point for every unique combo of timestamp+tag+field, if the
# uniqueID already exists in the database, the endUseLabel field's value will simply be
# overwritten with the new value. 

#Check that connection exists:
prompt = "Enter 'y' to write all " + str(len(output))+" points to the influx database."
if input(prompt)=='y':
    try:    
        if (client.write_points(dataframe=output,measurement=eu_measurement,protocol='line', 
                    tag_columns=["uniqueID"], field_columns=['endUseLabel'])!=True):
            print("There was some unknown with the write command problem")
        else:
            print("Writes were successful")
    except influxdb.exceptions.InfluxDBClientError:
        print("\n**Authorization error*** No data written. Check username and password!\n")
else:
    print("User cancelled operation")
    exit()
    




