import json
import numpy
import os
import fnmatch


jacquard_powermodel = {
                'Adv State' : 0 , 
                'Idle State' : 3 ,
                'Standby State' : 0 ,
                'Sleep State' : 21,
                'Brushin' : 10 ,
                'Brushout' : 10 ,
                'Double Tap' : 3 ,
                'Cover' : 0 ,
                'Calls' : 1 ,
                'Text' : 10,
                'Illuminate' : 1 ,
                'Find my phone' : 1

            }



def findrange(givenlist,chunksize) :

    """
        This is the core function of the power measurement program.This func calucates 
        the upper and lower cut off values of the current drawn curve and returns the avg
        current drwan and duration of the time in seconds for a given activity say brushin
    """
    for index in range(len(givenlist)):
	   window = givenlist[index:index + chunksize]
	   if all(items > 1000 for items in window) :
	       return index




def read_currentdata(filename) :

    """
        This function gets the txt file  saved by the labview program as input,parses the current
        readings and returns a list with all positive readings

    """

    with open(filename) as f:
        currentconsumed = f.readlines()
        currentconsumed = [eachNewline.strip() for eachNewline in currentconsumed]
        currentconsumed = [float(eachStringvalue) for eachStringvalue in currentconsumed]
        currentconsumed = [items for items in currentconsumed if items >= 0]
        return currentconsumed

		




def calc_Avgcurrent_and_duration_pergesture(inputfile) :


    """
        This function takes inut filename name as arguments and 
        returns a dictionary with current drawn by a gesture in muA and the duration in 
        seconds. 
    """
    lower_index = findrange(read_currentdata(inputfile),22)
    upper_index = len(read_currentdata(inputfile)) -  findrange(read_currentdata(inputfile)[::-1],22)
    average_current_milliamps = round(numpy.mean(read_currentdata(inputfile)[lower_index:upper_index]),2)
    average_time = round(len(read_currentdata(inputfile)[lower_index:upper_index])/10000.00,2)
    result_dict = {'AvgCurrentdrawninMuAmps' : average_current_milliamps,'DurationinSeconds': average_time} 
    return result_dict


# def filenameparser(filename):

#     """
#         The function returns filename without extension from 
#         the path provided 
#     """

#     basename = os.path.basename(filename)
#     return os.path.splitext(basename)[0]




def get_datafiles_per_platform(directory,platform):
    if platform == 'android' :
        android = [file for file in os.listdir(directory) if fnmatch.fnmatch(file,'*Android*')]
        return android
    if platform == 'ios' :
        ios = [file for file in os.listdir(directory) if fnmatch.fnmatch(file,'*IOS*')]
        return ios



def calc_batterylife(platform) :

    """
        The Platform is Android or IOS
    """


    battery_life = muAmpH_Idlestate + muAmpH_Standbystate + muAMpH_AdvState + muAmpH_Sleeptate + muAmpH_CallNotification + muAmpH_TxtNotification + muAmpH_Brushin 


def calc_currdrawnperday_pergesture_muAmpH(powermodel,gesture,inputfile):
    avgCurrent_in_muAmps = calc_Avgcurrent_and_duration_pergesture(inputfile)['AvgCurrentdrawninMuAmps']
    duration_peractivity_inSecs = calc_Avgcurrent_and_duration_pergesture(inputfile)['DurationinSeconds']
    numberof_gestures_perday = powermodel[gesture]
    durationofActivity_perday_inSeconds = numberof_gestures_perday * duration_peractivity_inSecs
    currentdrawn_pergesture_perday_muAmpsHrs =  (avgCurrent_in_muAmps * durationofActivity_perday_inSeconds )/3600
    return (numberof_gestures_perday,avgCurrent_in_muAmps,duration_peractivity_inSecs,round(currentdrawn_pergesture_perday_muAmpsHrs,2))






def calc_currentconsumedperday_perPlatform_muAmpH(directory,platform):
    gestures = [('Brushin','*Brushin*'),
                ('Brushout','*Brushout*'),
                ('Double Tap','*Double*'),
                ('Cover','*Cover*'),
                ('Calls','*Call*'),
                ('Text','*Text*'),
                ('Illuminate','*Illuminate*'),
                ('Find my Phone','*Find*')
                ]


    for items in gestures:
        head,tail = items 
        gesture = head
        file_list = [file for file in get_datafiles_per_platform(directory,platform) if fnmatch.fnmatch(file,tail)]
        for files in file_list :
            inputfile1 = os.path.join(directory,files)
            outputfile1 = os.path.join(directory,'Powermeasurement_Resultfile.txt')

            res_tup = {'platform': platform, gesture : (calc_currdrawnperday_pergesture_muAmpH(jacquard_powermodel,gesture,inputfile1))}

            with open(outputfile1,"a") as out:
                out.write(json.dumps(res_tup) + ('\n'))


def calc_powerconsumed(directory):
    platforms = ('android','ios')
    for item in platforms :
        calc_currentconsumedperday_perPlatform_muAmpH(directory,item)    











if __name__ == '__main__' :
    calc_powerconsumed("../PowerReadings/")
    
    



