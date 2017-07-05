// foundation for message-sending implementation is tutorial from Alex Le, https://alexanderle.com/blog/2011/send-sms-python.html


import pandas as pd
import smtplib
import schedule
import time

# will store patient IDs as keys; dates recorded thus far for patients as list values
dateDic = {}
# will store patient IDs as keys; new BG readings as list values
BGdic = {}
# cell phone carriers are keys. appropriate MMS gateway domains are values.
carrierGatewayDict = {"Alltel":"@mms.alltelwireless.com", "AT&T":"mms.att.net", "Boost":"@myboostmobile.com",
                          "Cricket":"@mms.cricketwireless.net", "MetroPCS":"@mymetropcs.com", "Project Fi":"@msg.fi.google.com",
                          "Sprint":"@pm.sprint.com", "T-Mobile":"@tmomail.net", "U.S. Cellular":"@mms.uscc.net",
                          "Verizon":"@vzwpix.com","Virgin":"@vmpix.com"}
# will store patient IDs as keys; physician phone numbers as values
docDic = {}
# read in file that contains patient IDs w/ corresponding BG readings & dates
bgCSV = pd.read_csv("Desktop/DummyBG.csv")


# read in csv with dates of already-recorded BG readings
def oldDates():
    dateCSV = pd.read_csv("Desktop/DatesSoFar.csv")
    dateRead = dateCSV.set_index("Patient ID")
    # fill dateDic dictionary to ensure physician messages aren't sent for old BG readings
    for patient, row in dateRead.iterrows():
        if patient not in dateDic:
            dateDic[patient] = []
        dateDic[patient].append(row["Date"])
    print(dateDic)
    print("Dates of prior BG readings successfully read in from Dates Thus Far csv")

# fill BGdic dictionary
def newReadings():
    bgRead = bgCSV.set_index("Patient ID")
    for patient, row in bgRead.iterrows():
        if patient not in BGdic:
            BGdic[patient] = []
        if row["Date"] not in dateDic[patient]:
            print("This is new: "+row["Date"])
            BGdic[patient].append((row["BG Reading"], row["Date"]))
    print(BGdic)
    print("Newest BG readings successfully read in")

# fill docDic dictionary
def mapPatientsToPhys():
    docCSV = pd.read_csv("Desktop/PatientInfo.csv")
    docRead = docCSV.set_index("Patient ID")
    for patient, row in docRead.iterrows():
        docDic[patient] = (row["Physician #"], row["Physician Phone Carrier"])
    print("Physician phone numbers successfully read in")

# SEND MESSAGE TO PHYSICIAN IF READING IS CONCERNING
def sendMessages():
    # indicator of whether or not there was a/were message/s to be sent
    sthgSent = 0
    # for each patient ID
    for patient in BGdic:
        # for each BG reading
        for readingAndDate in BGdic[patient]:
            # if the reading is dangerously low/high
            if readingAndDate[0] <= 45 or readingAndDate[0] >= 255:
                sthgSent = 1
                # establish usage of Gmail's outgoing server
                server = smtplib.SMTP("smtp.gmail.com",587)
                # create STARTTLS connection
                server.starttls()
                # complete connection session with valid login credentials, read in from csv
                loginCSV = pd.read_csv("Desktop/Login.csv")
                sender = loginCSV.iat[0,0]+"@gmail.com"
                server.login(sender,loginCSV.iat[0,1])
                # send message to appropriate doctor, specifying patient ID and the dangerous BG reading
                recipientMMS = str(docDic[patient][0])+"@"+carrierGatewayDict[docDic[patient][1]]
                bgReading = str(readingAndDate[0])
                dateOfReading = readingAndDate[1]
                server.sendmail(sender,recipientMMS,
                                "\nBG reading for patient #"+str(patient)+" is at a dangerous level - "
                                +bgReading+" mg/dL - as of "+dateOfReading)
                print("Message successfully sent")
    if sthgSent == 0:
        print("All BG readings safe. No messages were sent.")

# update .csv file containing Dates Thus Far
def updateDates():
    bgCSV.to_csv("Desktop/DatesSoFar.csv", columns=["Patient ID","Date"], index=False)
    print("New dates of BG readings successfully added to Dates Thus Far csv")

def main():
    oldDates()
    newReadings()
    mapPatientsToPhys()
    sendMessages()
    updateDates()

if __name__ == '__main__':
    schedule.every().day.at("14:30").do(main)
    schedule.every().day.at("21:00").do(main)

while True:
    schedule.run_pending()
    time.sleep(1)
