import urllib.request
import serial
from threading import Thread
import requests
import smtplib
import imaplib
import datetime
import numpy as np
from matplotlib import pyplot as plt
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


#Serial communication params
PORT = 'COM9'
BAUD_RATE = 9600

#thingspeak channel and api keys for data exchange
CHANNEL_ID = 2704469
API_KEY_WRITE = '' # add key later
API_KEY_READ = '' # add key later

BASE_URL = 'https://api.thingspeak.com'
WRITE_URL = '{}/update?api_key={}'.format(BASE_URL, API_KEY_WRITE)
READ_CHANNEL_URL = '{}/channels/{}/feeds.json?api_key={}'.format(BASE_URL, CHANNEL_ID, API_KEY_READ)
READ_FIELD1_URL = '{}/channels/{}/fields/{}.json?api_key={}&results={}'.format(BASE_URL, CHANNEL_ID, 1, API_KEY_READ, 100)
READ_FIELD2_URL = '{}/channels/{}/fields/{}.json?api_key={}&results={}'.format(BASE_URL, CHANNEL_ID, 2, API_KEY_READ, 100)
READ_FIELD3_URL = '{}/channels/{}/fields/{}.json?api_key={}&results={}'.format(BASE_URL, CHANNEL_ID, 3, API_KEY_READ, 100)

temp = requests.get(READ_FIELD1_URL)
illum = requests.get(READ_FIELD2_URL)
mov = requests.get(READ_FIELD3_URL)

dataJsonT = temp.json()
dataJsonI = illum.json()
dataJsonM = mov.json()

#Extract temperature
feeds_temp = dataJsonT["feeds"]
temperature = []
for x in feeds_temp:
    x = float(x["field1"])
    temperature.append(x)

#Extract illumination
feeds_illum = dataJsonI["feeds"]
illumination = []
for x in feeds_illum:
    x = float(x["field2"])
    illumination.append(x)

#Extract number of movements 
feeds_mov = dataJsonM["feeds"]
movements = []
for x in feeds_mov:
    x = float(x["field3"])
    movements.append(x)

print(movements)

#initialize time variables
startTime = datetime.datetime.today()
lamTime = datetime.datetime.today()
hsmTime = datetime.datetime.today()

#Process data from Arduino
def processData(data):
    processedData = {}
    dataList = data.split()
    print(dataList)
    if dataList[0] == 'motion':
        sendMotionWarning()
    if len(dataList) >=3:
        processedData["temp_value"] = dataList[0]
        processedData["illum_value"] = dataList[1]
        processedData["mov_value"] = dataList[2]
        sendTS(processedData)

#Send motion warning
def sendMotionWarning():
    message  = MIMEMultipart()
    message['Subject'] = 'Motion Detected'

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    r = server.login('', 'xrxb yizn zcrx itrj') # add email later
    r = server.sendmail('', '', message.as_string()) # add email later
    server.quit()
    print('Motion Report Sent')


#Send data to TS
def sendTS(data):
    resp = urllib.request.urlopen("{}&field1={}&field2={}&field3={}".format(WRITE_URL, data["temp_value"], data["illum_value"], data["mov_value"]))

#Receive data from the serial port
def receive(serialCom):
    receviedMessage = ""
    while True:
        if serialCom.in_waiting > 0:
            receviedMessage = serialCom.read_until().decode('ascii')
            processData(receviedMessage)

def checkMail(email, serialCommunication):
    email.select('inbox')
    while True:

        _, responseSE = email.search(None, '(SUBJECT "SEND REPORT" UNSEEN)')
        #------------------------------------------------------------------------
        # SEND REPORT
        if len(responseSE[0]) > 0:
            emailIds = responseSE[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')
            sendReport()
        #------------------------------------------------------------------------

        _, responseHeatingOn = email.search(None, '(SUBJECT "HEATING ON" UNSEEN)')
        _, responseHeatingOff = email.search(None, '(SUBJECT "HEATING OFF" UNSEEN)')
        #------------------------------------------------------------------------
        # HEATING ON
        if len(responseHeatingOn[0]) > 0:
            text = "heating on"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseHeatingOn[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')

        # HEATING OFF
        if len(responseHeatingOff[0]) > 0:
            text = "heating off"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseHeatingOff[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')
        #------------------------------------------------------------------------

        _, responseCoolingOn = email.search(None, '(SUBJECT "COOLING ON" UNSEEN)')
        _, responseCoolingOff = email.search(None, '(SUBJECT "COOLING OFF" UNSEEN)')
        #------------------------------------------------------------------------
        # COOLING ON
        if len(responseCoolingOn[0]) > 0:
            text = "cooling on"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseCoolingOn[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')

        # COOLING OFF
        if len(responseCoolingOff[0]) > 0:
            text = "cooling off"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseCoolingOff[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')
        #------------------------------------------------------------------------

        _, responseATCON = email.search(None, '(SUBJECT "AUTO TEMPERATURE CONTROL ON" UNSEEN)')
        _, responseATCOFF = email.search(None, '(SUBJECT "AUTO TEMPERATURE CONTROL OFF" UNSEEN)')
        #------------------------------------------------------------------------
        # AUTO TEMPERATURE CONTROL ON
        if len(responseATCON[0]) > 0:
            text = "auto temperature control on"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseATCON[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')

        # AUTO TEMPERATURE CONTROL OFF
        if len(responseATCOFF[0]) > 0:
            text = "auto temperature control off"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseATCOFF[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')
        #------------------------------------------------------------------------


        _, responseLAMON = email.search(None, '(SUBJECT "LIGHT AUTO MODE ON" UNSEEN)')
        _, responseLAMOFF = email.search(None, '(SUBJECT "LIGHT AUTO MODE OFF" UNSEEN)')
        #------------------------------------------------------------------------
        # LIGHT AUTO MODE ON
        if len(responseLAMON[0]) > 0:
            global lamTime
            lamTime = datetime.datetime.today()

            text = "light auto mode on"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseLAMON[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')

        # LIGHT AUTO MODE OFF
        if len(responseLAMOFF[0]) > 0:
            text = "light auto mode off"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseLAMOFF[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')
        #------------------------------------------------------------------------


        _, responseHSMON = email.search(None, '(SUBJECT "HOME SECURE MODE ON" UNSEEN)')
        _, responseHSMOFF = email.search(None, '(SUBJECT "HOME SECURE MODE OFF" UNSEEN)')
        #------------------------------------------------------------------------
        # HOME SECURE MODE ON
        if len(responseHSMON[0]) > 0:
            global hsmTime
            hsmTime = datetime.datetime.today()
            text = "home secure mode on"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseHSMON[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')

        # HOME SECURE MODE OFF
        if len(responseHSMOFF[0]) > 0:
            text = "home secure mode off"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseHSMOFF[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')
        #------------------------------------------------------------------------


        _, responseLightOn = email.search(None, '(SUBJECT "LIGHT ON" UNSEEN)')
        _, responseLightOff = email.search(None, '(SUBJECT "LIGHT OFF" UNSEEN)')
        #------------------------------------------------------------------------
        # LIGHT ON
        if len(responseLightOn[0]) > 0:
            text = "light on"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseLightOn[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')

        # LIGHT OFF
        if len(responseLightOff[0]) > 0:
            text = "light off"
            serialCommunication.write(text.encode('ascii'))
            emailIds = responseLightOff[0].split()
            for id in emailIds:
                email.store(id, '+FLAGS', '\\Seen')
        #------------------------------------------------------------------------


# Email Report function
def sendReport():
    message  = MIMEMultipart()
    message['Subject'] = 'Report from my Arduino'

    #------------------------------------------------------------------------
    # TEMPERATURE GRAPH
    plt.ioff()
    x = np.linspace(0, 23, (len(temperature)*1))
    plt.title("Daily temperature")
    plt.xlabel("Hours")
    plt.ylabel("Temperature (C)")
    plt.plot(x, temperature, label="Temperature")
    plt.axhline(y=np.min(temperature), linestyle=':', c='r', label='Min Temp')
    plt.axhline(y=np.max(temperature), linestyle=':', c='m', label='Max Temp')
    plt.axhline(y=np.average(temperature), linestyle='--', c='g', label='Average Temp')
    plt.legend()
    fileName = 'report-temperature-{}.png'.format(datetime.date.today())
    plt.savefig('C:\\Users\\foxyc\\Documents\\_University\\Internet of Things\\report_images\\' + fileName)
    plt.cla()
    tempGraph = open('C:\\Users\\foxyc\\Documents\\_University\\Internet of Things\\report_images\\' + fileName, 'rb')
    msgTempGraph = MIMEImage(tempGraph.read())
    tempGraph.close()
    message.attach(msgTempGraph)
    #------------------------------------------------------------------------

    #------------------------------------------------------------------------
    # ILLUMINATION GRAPH
    plt.ioff()
    x = np.linspace(0, 23, (1*len(illumination)))
    plt.title("Daily illumination")
    plt.xlabel("Hours")
    plt.ylabel("Illumination (%)")
    plt.plot(x, illumination, label="Illumination")
    plt.axhline(y=np.min(illumination), linestyle=':', c='r', label='Min Illum')
    plt.axhline(y=np.max(illumination), linestyle=':', c='m', label='Max Illum')
    plt.axhline(y=np.average(illumination), linestyle='--', c='g', label='Average Illum')
    plt.legend()
    fileName = 'report-illumination-{}.png'.format(datetime.date.today())
    plt.savefig('C:\\Users\\foxyc\\Documents\\_University\\Internet of Things\\report_images\\' + fileName)
    plt.cla()
    illumGraph = open('C:\\Users\\foxyc\\Documents\\_University\\Internet of Things\\report_images\\' + fileName, 'rb')
    msgIllumGraph = MIMEImage(illumGraph.read())
    illumGraph.close()
    message.attach(msgIllumGraph)
    #------------------------------------------------------------------------

    #------------------------------------------------------------------------
    # MOVEMENT GRAPH
    plt.ioff()
    x = np.linspace(0, 23, (1*len(movements)))
    plt.title("Daily movement")
    plt.xlabel("Hours")
    plt.ylabel("Number of movements detected")
    plt.plot(x, movements, label="Movements")
    fileName = 'report-movement-{}.png'.format(datetime.date.today())
    plt.savefig('C:\\Users\\foxyc\\Documents\\_University\\Internet of Things\\report_images\\' + fileName)
    plt.cla()
    movGraph = open('C:\\Users\\foxyc\\Documents\\_University\\Internet of Things\\report_images\\' + fileName, 'rb')
    msgMovGraph = MIMEImage(movGraph.read())
    movGraph.close()
    message.attach(msgMovGraph)
    #------------------------------------------------------------------------

    #------------------------------------------------------------------------
    lamTimeDelta = "0:00:00.0"
    if lamTime.ctime() != startTime.ctime():
        lamTimeDelta = str(datetime.datetime.today() - lamTime)

    hsmTimeDelta = "0:00:00.0"
    if hsmTime.ctime() != startTime.ctime():
        hsmTimeDelta = str(datetime.datetime.today() - hsmTime)


    htmlText = """\
        <html>
            <head></head>
            <body>
                <h1>Daily report on {}</h1>
                <p>
                    The minimum daily temperature was: <strong>{:.2f}</strong> C and the maximum was
                    <strong>{:.2f}</strong> C and the average was <strong>{:.2f}</strong> C. 
                </p>
                <p>
                    The minimum daily illumination was: <strong>{:.2f}</strong> % and the maximum was
                    <strong>{:.2f}</strong> % and the average was <strong>{:.2f}</strong> %. 
                </p>
                <p>
                    Number of movements today {}.
                </p>
                <p>
                    "Home secure mode" was ON for ({}).
                </p>
                <p>
                    "Light auto mode" was ON for ({}).
                </p>
            </body>
        </html>
    """.format(datetime.date.today(), np.min(temperature), np.max(temperature), np.average(temperature), np.min(illumination), np.max(illumination), np.average(illumination), np.sum(movements), hsmTimeDelta, lamTimeDelta)

    mimeText = MIMEText(htmlText, 'html')
    message.attach(mimeText)
    #------------------------------------------------------------------------

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    r = server.login('', 'xrxb yizn zcrx itrj') # add email later
    r = server.sendmail('', '', message.as_string()) # add email later
    server.quit()
    print('Report sent')

#init serial comm
serialCommunication = serial.Serial(PORT, BAUD_RATE)

#email login
email = imaplib.IMAP4_SSL('imap.gmail.com')
email.login('', 'xrxb yizn zcrx itrj') # add email later 

# check email thread
checkEmailThread = Thread(target=checkMail, args=(email, serialCommunication))
checkEmailThread.start()

#start a thread to receive the data from the Arduino
receivingThread = Thread(target=receive, args=(serialCommunication,))
receivingThread.start()

