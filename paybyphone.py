import cookielib
import sys
import time
import traceback

import mechanize
from twilio.rest import TwilioRestClient

# Some Constants related with paybyphone account and meters
phoneNum = ["xxx", "xxx"]  # Phone number of each account
pin = ["xxx", "xxx"]  # pin for each account
cvv = ["xxx", "xxx"]  # CVV number for each card (account)
maxDuration = 60  # Maximum time in minutes to park each time
startTime = [9, 0]  # Meter Start Time: The time that meter start to require money (here is 9:00)
endTime = [18, 0]  # Meter End Time (here is 18:00)

# Related with twilio:
accountId = "xxx"
authToken = "xxx"
fromNum = "xxx"
toNum = "xxx"

"""
Usage:
    python paybyphone.py locationNum startCard{0,1} targetTimeHour targetTimeMin [nextTimeHour nextTimeMin]

Options:
    locationNum: The location number of the meter
    startCard: Which account to first to use (start from 0)
    targetTimeHour, targetTimeMin: Target time to park til, e.g. [17, 00]: park until 5 p.m.
    nextTimeHour, nextTimeMin: Next payment start time

Example:
    python paybyphone.py 12345678 0 17 00
        This will pay for meter number 12345678 until 17:00, and first using the first account. (Starting paying from
        now or meter start time, whenever is latter)

    python paybyphone.py 12345678 0 17 00 11 25
        This will start paying from 11:25 or now whenever is latter. (Suitable when you already paid or you know when to park)

"""


def sendSMS(msg):
    # the following line needs your Twilio Account SID and Auth Token
    client = TwilioRestClient(accountId, authToken)
    print ts() + "Send SMS MSG: " + msg
    # print "debuging"
    client.messages.create(to=toNum, from_=fromNum, body=msg)


def pay(locationNum, phoneNum, pin, cvv, duration):
    if duration <= 0 or duration > 120:
        print ts() + "Error input duration: " + str(duration)
        return False
    if duration < 5:
        print ts() + "Only " + str(duration) + " mins left, no need to pay"
        sendSMS("Only " + str(duration) + " mins left, no need to pay")
        return True
    print ts() + "Going to pay for duration of " + str(duration) + " mins using phone number " + str(
        phoneNum) + " for location " + str(locationNum) + ". You have 5 secs to cancel it."

    # print "debuging"
    # return True

    time.sleep(5)

    br = mechanize.Browser()
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)

    # Log in page
    br.open("https://m.paybyphone.com")
    br.select_form(nr=0)
    br["ctl00$ContentPlaceHolder1$CallingCodeDropDownList"][0] = -1
    br["ctl00$ContentPlaceHolder1$AccountTextBox"] = str(phoneNum)
    br["ctl00$ContentPlaceHolder1$PinOrLast4DigitCcTextBox"] = str(pin)
    response1 = br.submit()

    # Select location number
    checkin_URL = response1.geturl()
    br.open(checkin_URL)
    br.select_form(nr=0)
    if br.form.controls[4].name == 'ctl00$ContentPlaceHolder1$ActiveParkingGridView$ctl02$ExtendAllowedHiddenField' \
            and br['ctl00$ContentPlaceHolder1$ActiveParkingGridView$ctl02$ExtendAllowedHiddenField'] == 'Normal':
        print ts() + "Still remains some time when paying! Probably you are using same account for two successive payments."
        return False
    br["ctl00$ContentPlaceHolder1$LocationNumberTextBox"] = str(locationNum)
    response1 = br.submit()

    # Duration
    checkin_URL = response1.geturl()
    br.open(checkin_URL)
    br.select_form(nr=0)
    br["ctl00$ContentPlaceHolder1$DurationTextBox"] = str(duration)
    response1 = br.submit()

    # Check Out
    checkin_URL = response1.geturl()
    br.open(checkin_URL)
    br.select_form(nr=0)
    if br["ctl00$ContentPlaceHolder1$NoRatesFoundErrorHidden"] == 'True':
        print ts() + "NoRatesFoundError"
        return False
    if br['ctl00$ContentPlaceHolder1$SessionQuoteErrorHidden'] == 'True':
        print ts() + 'SessionQuoteErrorHidden'
        return False
    if br['ctl00$ContentPlaceHolder1$ParkingSessionValidationErrorHidden'] == 'True':
        print ts() + 'ParkingSessionValidationError'
        return False
    if br.form.controls[5].name == 'ctl00$ContentPlaceHolder1$ChangeButton':
        print ts() + 'Only change button exists!'
        return False
    if br.form.controls[6].name != 'ctl00$ContentPlaceHolder1$ConfirmParking':
        print ts() + 'No confirm parking button exists!'
        return False
    if br.form.controls[5].name != 'ctl00$ContentPlaceHolder1$CvvTextBox':
        print ts() + 'No CVV text box!'
        return False
    br["ctl00$ContentPlaceHolder1$CvvTextBox"] = cvv
    response1 = br.submit()

    # Make sure it successfully paid
    checkin_URL = response1.geturl()
    html = br.open(checkin_URL).read()
    br.select_form(nr=0)
    if br.form.controls[0].name == 'ctl00$ContentPlaceHolder1$AddTimeLongButton':
        print ts() + "Failed to find park again buttion"
        return False
    if html.find("Icon_checkmark.png") != -1:
        msg = "Successfully pay for duration of " + str(duration) + " mins using phone number " + str(
            phoneNum) + " for location " + str(locationNum)
        print ts() + msg
        sendSMS(msg)
        return True

    return False


def ts():
    return time.strftime("%Y-%m-%d %H:%M:%S") + " "


def getTimeDiffInSec(nextTime):
    curTime = time.localtime(time.time())
    duration = (nextTime[0] - curTime[3]) * 3600 + (nextTime[1] - curTime[4]) * 60 - curTime[5]
    if duration <= 0:
        return 0
    return duration


def sleep(nextTime):
    duration = getTimeDiffInSec(nextTime)
    if duration < -120:
        print ts() + "Sleep time shouldn't be negative!"
    print ts() + "Going to sleep for " + str(float(duration) / 60) + " mins to reach next pay time: " + \
          "%02d" % nextTime[0] + ":" + "%02d" % nextTime[1]
    while duration > 0:
        if duration % (5 * 60) == 0:
            print ts() + "Remaining sleep time: " + str(float(duration) / 60) + " mins"
        if 10.5 * 60 >= duration >= 9.5 * 60:
            sendSMS("Remaining sleep time " + str(float(duration) / 60) + " mins")
        if duration >= 60:
            sleepTime = 60 + duration % 60
        else:
            break
        time.sleep(sleepTime)  # sleep for one minute
        duration -= sleepTime
    time.sleep(getTimeDiffInSec(nextTime))


def checkCurTime(nextTime):
    curTime = time.localtime(time.time())
    duration = (nextTime[0] - curTime[3]) * 60 + (nextTime[1] - curTime[4])
    if abs(duration) >= 3:
        print ts() + "Current time is not the next pay time!"
        return False
    return True


def auto_pay(locationNum, startCard, targetTime, nextTime):
    print ts() + "Target time is " + "%02d" % targetTime[0] + ":" + "%02d" % targetTime[1]
    print ts() + "Location number going to pay is " + locationNum + ". Please make sure it is correct! You have 10 secs to cancel."
    # print "debuging"
    time.sleep(10)

    # Some checks
    curTime = time.localtime(time.time())
    if curTime[6] == 6:
        print ts() + "Sunday is free!"
        sendSMS("Sunday is free!")
    elif curTime[3] > targetTime[0] or (curTime[3] == targetTime[0] and curTime[4] >= targetTime[1]):
        msg = ts() + "It already has reached target time! Current time: " + "%02d" % curTime[3] + ":" + "%02d" %  curTime[4] + \
              " target time: " + "%02d" % targetTime[0] + ":" + "%02d" % targetTime[1]
        print msg
        sendSMS(msg)
    else:
        if nextTime[0] == 0 and nextTime[1] == 0:  # Default value (Not paid today)
            if curTime[3] < startTime[0] or (
                            curTime[3] == startTime[0] and curTime[4] < startTime[1]):  # Earlier than start time
                nextTime[0] = startTime[0]
                nextTime[1] = startTime[1]
            else:
                nextTime[0] = curTime[3]
                nextTime[1] = curTime[4]
        elif curTime[3] > nextTime[0] or (
                        curTime[3] == nextTime[0] and curTime[4] > nextTime[1]):  # next pay time already passed
            nextTime[0] = curTime[3]
            nextTime[1] = curTime[4]

        # Start paying loop
        iter = startCard
        while nextTime[0] < targetTime[0] or (nextTime[0] == targetTime[0] and nextTime[1] < targetTime[1]):
            duration = min(maxDuration, (targetTime[0] - nextTime[0]) * 60 + (targetTime[1] - nextTime[1]))
            # Should sleep until reach next paid time
            sleep(nextTime)
            if not checkCurTime(nextTime):
                sendSMS("Failed to pay!")
                break
            if not pay(locationNum, phoneNum[iter], pin[iter], cvv[iter], duration):
                print ts() + "Failed to pay!"
                sendSMS("Failed to pay!")
                break
            nextTime[1] += int(float(duration) % 60)
            nextTime[0] = nextTime[0] + int(float(duration) / 60) + (nextTime[1] / 60)
            nextTime[1] %= 60
            if nextTime[0] > targetTime[0] or (nextTime[0] == targetTime[0] and nextTime[1] >= targetTime[1]):
                print ts() + "Finish the last pay!"
                sendSMS("Finish the last pay!")
                break
            print ts() + "Next pay time: " + "%02d" % nextTime[0] + ":" + "%02d" % nextTime[1]
            iter = (iter + 1) % 2  # switch two numbers
        if nextTime[0] < endTime[0] or (nextTime[0] == endTime[0] and nextTime[1] < endTime[1]):
            sleepTime = max(getTimeDiffInSec(nextTime) - 60 * 5, 0)
            time.sleep(sleepTime)
            print ts() + "Be careful that your time is going to run out!"
            sendSMS("Be careful that your time is going to run out in " + str(getTimeDiffInSec(nextTime) / 60)
                    + " minutes! Be better to pick up the car or refeed some time.")


# Parameters
# The location number of the meter
locationNum = sys.argv[1]
# Which account to first to use: start from 0
startCard = int(sys.argv[2])
# Target time to park til, e.g. [17, 00]: park until 5 p.m.
targetTime = [int(sys.argv[3]), int(sys.argv[4])]
# nextTime: Next payment start time. If set to [0,0], then start from now or meter start time, whenever is latter.
# If set to non-zero, then start paying from the time set or meter start time, whenever is latter.,
# e.g. [14, 00] means starting paying from 2 p.m.
if len(sys.argv) > 6:
    nextTime = [int(sys.argv[5]), int(sys.argv[6])]
else:
    nextTime = [0, 0]

try:
    auto_pay(locationNum, startCard, targetTime, nextTime)
except Exception as e:
    print traceback.format_exc()
    sendSMS("Some unexpected errors happened! Please check output.")
print ts() + "Exit program!"
