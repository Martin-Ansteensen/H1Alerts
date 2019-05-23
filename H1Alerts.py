#!/usr/bin/env python3

import requests
from requests import ConnectTimeout, Timeout
import json
import time
import datetime
import os
from datetime import timedelta  

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(__location__+"/config.json") as config_file:
    jsonData = json.load(config_file)
offlineServers = {}
try:
    with open(__location__+"/servers.json") as servers_file:
        offlineServers = json.load(servers_file)
except (json.decoder.JSONDecodeError):
    pass

servers = jsonData["servers"]
timeoutMargin = jsonData["settings"]["timeoutMargin"] #Margin before the server is counted as offline due to timeout
offlineMargin = jsonData["settings"]["offlineMargin"] #How long the server has to be offline before the it is posted in mattermost
mattermostUrl = jsonData["settings"]["mattermostUrl"] #Url to the chat where it is posting messages
requests.packages.urllib3.disable_warnings()

def connectServer(server, timeout = timeoutMargin):
    print("\n"+servers[server]["url"])
    try:
        request = requests.get(servers[server]["url"], verify=False, timeout=timeout)
    except(ConnectTimeout, requests.exceptions.ReadTimeout):
        # Could not establish connections for timeout seconds, return Timeout for no connection established
        print("The server is offline")
        servers[server]["status"] = 0
        return "Timeout"
    except(requests.exceptions.ConnectionError):
        # Could not establish connections for timeout seconds, return Timeout for no connection established
        print("The server is offline")
        servers[server]["status"] = 0
        return "ConnectError"
    if request.status_code == 403:
        print("The server is offline")
        servers[server]["status"] = 0
        return "403 Acess forbidden"
    else:
        # Connection successfull, return status code
        print("The server is online")
        servers[server]["status"]= 1
        return request.status_code
# 0=Offline 1= Online 2= Not checked yet

#for check in timeoutMargin, checkTwo, checkThree:
for server in servers:
    print(connectServer(server, timeoutMargin))
 

message = "\n" + "These servers are offline: "

for s in servers:
    if servers[s]["status"] == 1:   #Is the server online
        if s in offlineServers:     #Is it in register, then delete it's files and continue
            del offlineServers[s]
            continue
        else:         #The server is online and everything is fine
            continue     
    #Is it not in the register? 
    if not s in offlineServers: 
        error = connectServer(s, 1) #It's error code
        firstOffline = datetime.datetime.now()  #Time it became offline 
        offlineServers[s] = {"error":error, "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} #Makes a dic for the server in the register
        oneMinuteAgo = datetime.datetime.now()-timedelta(seconds = offlineMargin ) #One minute ago
        timeOffline = datetime.datetime.now()-firstOffline
        if firstOffline > oneMinuteAgo: #Has the server been offline for more than a minute
            print(str(s)+ "printes ikke i chatten fordi den ikke har vært nede i 60 sekunder. Foreløpig nedetid: " + str(timeOffline) + " sekunder") 
            continue
        else: #The server is not registered but have been offline for more than a minute
            message += "\n" + str(s) + " - "+servers[s]["url"]+ " - " + error +" since " + offlineServers[s]["time"]
            continue
    
    else:   #The server is offline and is registered in offlineServers
        firstOffline = datetime.datetime.strptime(offlineServers[s]["time"], '%Y-%m-%d %H:%M') #Gets the value when it first went offline
        error = connectServer(s, 1)
        message += "\n" + str(s) + " - " +servers[s]["url"]+ " - " + error +" since " + offlineServers[s]["time"]
    
print(message)
alert = requests.post(url= mattermostUrl, data='{"text": "### Offline servers! \n'+str(message)+'"}')

with open("servers.json", "w") as outfile:
    json.dump(offlineServers, outfile)




