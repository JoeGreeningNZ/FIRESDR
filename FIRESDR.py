#FIRESDR Smart Paging - Created By Joe Greening - F§P
import os
from subprocess import call
import pyttsx3
import time
import holidays
from datetime import datetime
import alsaaudio 
from chump import Application
from abbr import *

station_callsign = "SILV90"

#Initialise Variables
fire_keyword = "#F"
active = True
current_call = ""
station_firecalls = []
count = 0
tts = ""
msg = ""
prevday = ""
boxfound = False
box = ""
cycle_count = 0

capcodes = {'1140499': 'SDAL1',
            '1920722': 'SDAL2',
            '1117995': 'SDAL3',
            '1920204': 'SDALFRU'
            }
            
jobs = {"PURPLE",
        "RED",
        "ORANGE",
        "GREEN"
        }

ambo = []

typeabbr = {'MIN': 'MINOR INCIDENT',
            'STRU': 'STRUCTURE INCIDENT',
            'MEDFR': 'MEDICAL FIRST RESPONSE',
            'MED ': 'MEDICAL ',
            'RESC': 'RESCUE',
            'VEG': 'VEGETATION FIRE',
            'NAT1': 'NATURAL EVENT - PRIORITY 1',
            'NAT2': 'NATURAL EVENT - PRIORITY 2',
            'HAZ ': 'HAZARDOUS SUBSTANCE INCIDENT ',
            'HAZGAS': 'HAZARDOUS GAS INCIDENT',
            }

roadabbr = {' RD': ' ROAD ',
            ' AV': ' AVENUE ',
            ' PL': ' PLACE ',
            ' CL': ' CLOSE ',
            ' CT': ' COURT ',
            ' CR': ' CRESENT ',
            ' DR': ' DRIVE ',
            ' EXP': ' EXPRESSWAY ',
            ' HWY': ' HIGHWAY ',
            ' GR': ' GROVE ',
            ' HTS': ' HEIGHTS ',
            ' LN': ' LANE ',
            ' ST': ' STREET ',
            ' WAY': ' WAY ',
            ' TCE': ' TERRACE ',
            ' MWY': ' MOTORWAY ',
            ' PDE': ' PARADE ',
            ' CNR': ' CORNER ',
            ' ESP': ' ESPLANADE ',
            ' LA': 'LANE'
            }

#Initalise Turnout Audio
m = alsaaudio.Mixer()

#Initialise TTS engine
engine = pyttsx3.init()
volume = engine.getProperty('volume')
engine.setProperty('volume', volume)
rate = engine.getProperty('rate')
engine.setProperty('rate', rate-35)


def yw_check():
    #Initialise Variables for Yellow Watch.
    yw_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    yw_start = '07:05:00'
    yw_end = '17:25:00'
    prev_check = ""
    yw_active = False
    yw_holidays = []
    #Sort Holidays for Yellow Watch
    for holiday in holidays.NZ(years=[2022]).items():
        if ((holiday[0]).weekday()) <= 5:
            yw_holidays.append(holiday[0].strftime('%d-%m-%y'))
    currday = datetime.today().strftime('%A') # Monday
    currdate = datetime.today().strftime('%D-%M-%Y') # 00/00/0000
    currtime = datetime.now().strftime("%H:%M:%S") # 00:00:00   
    if (currdate in yw_holidays):
        return "\033[1;31;40mOff Duty - Public Holiday"
    elif (currday not in yw_days):
        return "\033[1;31;40mOff Duty - Weekend"
    elif (yw_start <= currtime <= yw_end):
        return "\033[1;32;40mOn Duty"
    else:
        return "\033[1;31;40mOff Duty - Outside YW Hours"

# Color Mapping
# Red - Turnout - \033[1;31;40m
# Yellow - Standby - \033[1;33;40m
# Green - Message - \033[1;32;40m
# Cyan - System - \033[1;36;40m
# Magenta - Error - \033[1;35;40m
# White - Shell - \033[1;37;40m

def newscr(clear=20):
    if clear == 0:
        os.system("clear")
    else:
        for i in range(clear):
            print("")
    return

#Define Turnout Actions and Proccesses for Smart Paging through Pushover and External Speakers.
def turnout(stage, msg, tts):
    #stage = 0 # Uncomment for Testing !!!!!
    #FIRESDR Smart Paging (Application)
    app = Application('a37fksysrfhmnuaczz58qaxqj4qb4o')
    #FIRESDR Smart Paging Members (Delivery Group)
    user = app.get_user('g89nanv98y2znbrt2xn2i8zpitv4ay')
    if stage != 0:
        if stage == 1:
            call(["aplay","/home/pi/FIRESDR/tone.wav"])
        if stage == 2:
            call(["aplay", "/home/pi/FIRESDR/tone.wav"])
            call(["aplay", "/home/pi/FIRESDR/tone.wav"])
        if stage == 3:
            call(["aplay", "/home/pi/FIRESDR/tone.wav"])
            call(["aplay", "/home/pi/FIRESDR/tone.wav"])
            call(["aplay", "/home/pi/FIRESDR/tone.wav"])
        if stage == 4:
            #call(["aplay", "/home/pi/FIRESDR/atone.wav"])
            app = Application('aky9uwfvxy8z44seg5c7tz46h4e77m')
            #AMBOSDR Smart Paging Members (Delivery Group)
            user = app.get_user('gecot6dnrn51xbdiuws6q3y6wex3of')
            message = user.send_message(msg,priority=0) #*************************** Comment both lines for Testing Ensure is Reset ***************************
            response = (message.is_sent, message.id, str(message.sent_at))
        else:
            message = user.send_message(msg,priority=1) #*************************** Comment both lines for Testing Ensure is Reset ***************************
            response = (message.is_sent, message.id, str(message.sent_at))
            engine.say(tts) # Same here
            engine.runAndWait() # and Here
    if boxfound:
        #FIRESDR Smart Paging (Application)
        app = Application('a37fksysrfhmnuaczz58qaxqj4qb4o')
        #FIRESDR Smart Paging Members (Delivery Group)
        user = app.get_user('g89nanv98y2znbrt2xn2i8zpitv4ay')
        message = user.send_message(box,priority=1) #*************************** Comment both lines for Testing Ensure is Reset ***************************
        response = (message.is_sent, message.id, str(message.sent_at))
def main():
    prev_check = False
    cycle_count = 0
    #Main Program Start
    time.sleep(5)
    print("")
    print("\033[1;36;40mFIRESDR - Filter Started")
    print("")
    print("\033[1;36;40mCallsign: ", station_callsign)
    print("")
    print("\033[1;37;40m*******************************************************")
    print("")
    yw_check() #Initalise Yellow Watch Check
    while active: #Pager Analysis Loop and Detection Logic System
        m.setvolume(45) #Set Volume
        if cycle_count > 35: #Check for number of analysis cycles before creating summary display
            newscr(0)
            print("")
            print("\033[1;37;40m*******************************************************")
            print("")
            call_count = 0
            ambo_count = 0
            for i in station_firecalls:
                call_count += 1
            for i in ambo:
                ambo_count += 1
            print("\033[1;36;40mFIRESDR Smart Paging - Callsign: ", station_callsign)
            print("")
            if call_count < 6:
                print("Call History - Fire Count: " + str(call_count) + " - Ambo Count: " + str(ambo_count))
                print("")
                for i in station_firecalls:
                    print("\033[1;37;40m" + i)
            elif call_count >= 6:
                print("Call History (Last 6 Calls)- Total Count: " + str(call_count))
                print("")
                history_count = 0
                for i in reversed(station_firecalls):
                    if history_count <  6:
                        print("\033[1;37;40m" + i)
                        history_count += 1
            print("\033[1;37;40m*******************************************************")
            cycle_count = 0
        
        if yw_check() is not prev_check:     #Yellow Watch Check String 
            print("\033[1;33;40mYellow Watch: " + yw_check())
            print(" ")
            print("\033[1;37;40m*******************************************************")
            print("")
            prev_check = yw_check()
    
        #Yellow Watch Check Bool
        if "On Duty" in yw_check():
            yw_active = True
        else:
            yw_active = False

        # Open Raw Data from RTL_FM and MULTIMON-NG
        try:
            raw = open('raw.txt', 'r')
            #raw = open('Testing/raw.txt', 'r') # Testing
        except:
            print("Error: Ensure RTL_FM Raw Data is being piped")
        # Main Data Handling
        file = []
        for i in raw:
            file.append(i)
        try:
            modes = file.pop(0)
        except:
            print("Waiting for Data")
        #AMBOSDR
        for i in file:
            tts = ""
            msg = ""
            boxfound = False
            if "POCSAG" in i:
                msg_capcode = i.split("  ",1)[0].split("Address: ")[-1]
                msg_data = i.split("   ")[-1]
                for capcode,unit in capcodes.items():
                    if msg_capcode == capcode:
                        for job in jobs:
                            if (job in msg_data) and (msg_data not in ambo) and (("Unit:"+unit) not in msg_data):
                                ambo.append(msg_data)
                                msg_data_tidy = msg_data.replace("; Flat/Unit:","")
                                if "<ETX>" in msg_data_tidy:
                                    msg_data_tidy = msg_data_tidy.replace("<ETX>","")
                                if "/" in msg_data_tidy:
                                    msg_data_tidy = msg_data_tidy.replace("/","")
                                for code,value in ccc.items():
                                    if code in msg_data_tidy:
                                        msg_data_tidy = msg_data_tidy.replace(code,value)
                                msg = ("Ambulance PreAlert - Standby! - " + msg_data_tidy)
                                tts = msg
                                print("\033[1;33;40m" + (str(datetime.now()).split('.',1)[-2]) +" Ambulance PreAlert - Standby! - " + msg_data_tidy)
                                print("\033[0;37;40m ")
                                turnout(4,msg,tts)
                                
        #FIRESDR
        for i in file:
            tts = ""
            msg = "" 
            if station_callsign in i:
                metadata = i.split("(")[0]
                if "FLEX" in metadata:
                    method = metadata.split("|")[0]
                    tom = metadata.split("|")[1]
                    capcode = metadata.split("|")[4]
                    metadata_str = tom + ", " + method + ", " + capcode
                    #print(metadata_str)
                current_call = ("(" + (i.split("(",1))[-1])
                count = station_firecalls.count(current_call)   
                if count == 0:
                    cycle_count = 0
                    icad = ("#F" + (current_call.split("#F",1)[-1]))
                    icad_raw = (current_call.split("#F",1)[-1])
                    if icad == ("#F" + current_call):
                        station_firecalls.append(current_call)
                        tts = "Partial Message. Standby. "
                        msg = "Partial Message - Standby"
                        turnout(0)
                        print("\033[1;33;40m" + (str(datetime.now()).split('.',1)[-2]) +" Partial Message - Standby!")
                        print("\033[0;37;40m ")
                    if icad != ("#F" + current_call):
                        station_firecalls.append(current_call)
                        if "PURPLE" in current_call:
                            tts += "PURPLE. PURPLE. PURPLE"
                            call(["aplay", "/home/pi/FIRESDR/etone.wav"])
                            print("")
                        if " FIRE" in current_call:
                            tts += "FIRE. FIRE. FIRE"
                            call(["aplay", "/home/pi/FIRESDR/etone.wav"])
                            print("") 
                        if "PERSONS REPORTED" in current_call:
                            tts += "PERSONS REPORTED. PERSONS REPORTED. PERSONS REPORTED"
                            call(["aplay", "/home/pi/FIRESDR/etone.wav"])
                            print("") 
                        #tts += "Fire Call Detected. "
                        #msg += ("Fire Call Detected - " + icad + "\n")
                        incident = current_call.split(")")[1].split()[0]
                        for key, value in typeabbr.items():
                            incident = incident.replace(key, value)
                            current_call = current_call.replace(key + " ", value + " ")
                        for key, value in roadabbr.items():
                            current_call = current_call.replace((key + " "), value)
                            current_call = current_call.replace((key + "/"), value)
                            current_call = current_call.replace((key + ")"), value)
                        tts += ("   " + incident + ".   ")
                        msg += (incident + "\n")
                        print("\033[1;31;40m" + (str(datetime.now()).split('.',1)[-2]) + " - FireCall Detected - " + icad)
                        print("\033[0;37;40m ")
                        print(current_call.upper())
                        if "(BOX" in current_call.upper():
                            boxstart = "(BOX" + current_call.upper().split("(BOX")[-1]
                            box = boxstart.split(")")[0] + ")"
                            boxfound = True
                            print(str(boxfound))
                        else:
                            boxfound = False
                            box = ""
                        #print(box + " " + str(boxfound))
                        try:
                            with open("log.txt", "a") as logfile:
                                logfile.write((metadata_str) + " - - - " + (str(datetime.now()).split('.',1)[-2]) + " - - - " + current_call.upper())
                        except:
                            print("Error: Logfile not found - ")
                        count901 = current_call.count("SILV901,") + current_call.count("SILV901)")
                        count907 = current_call.count("SILV907,") + current_call.count("SILV907)")
                        count9011 = current_call.count("SILV9011,") + current_call.count("SILV9011)")
                        #print(str(count901) + " " + str(count907) + " " + str(count9011))
                        time.sleep(1)
                        print("\033[0;32;40m")
                        turnoutsize = count901 + count907 + count9011
                        if count901 > 0:
                            tts += "SILVERDALE 9 0 1. "
                            msg += "SILVEDALE 901 \n"
                            print("SILVERDALE 901")
                            print("")
                        if count907 > 0:
                            tts += "SILVERDALE 9 0 7. "
                            msg += "SILVEDALE 907 \n"
                            print("SILVERDALE 907")
                            print("")
                        if count9011 > 0:
                            tts += "SILVERDALE 9 0 1 1. "
                            msg += "SILVEDALE 9011 \n"
                            print("SILVERDALE 9011")
                            print("")
                        frag0 = (current_call.split(')',1)[-1])
                        if "#F" in frag0:
                            if "(x" in  frag0:
                                frag1 = (frag0.split('(x')[-2])
                            if "(x" not in frag0:
                                frag1 = (frag0.split('#F')[-2])
                        frag2 = (frag1.replace("(",""))
                        frag3 = (frag2.replace(")",""))
                        frag4 = (frag3.replace("/"," AND "))
                        frag5 = (frag4.replace("XStr","CROSS STREET WITH "))
                        frag6 = (frag5.replace(" ","  "))
                        frag7 = (frag6.replace(".","..."))
                        tts += frag7
                        msg += "\n\n(" + frag5 + ")"
                        turnout(turnoutsize,msg,tts)
                        time.sleep(2)
                    print("\033[0;37;40m")
                    print("*******************************************************")
                    print("")
        raw.close()
        time.sleep(1.5)
        cycle_count += 1
    
if __name__ == '__main__':
    main()
    print("*** MAIN PROGRAM EXITED ***")
            
