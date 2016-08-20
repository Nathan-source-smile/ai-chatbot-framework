from __future__ import print_function
import requests
import json
import re
from datetime import datetime, timedelta

def getIfsc(entities):
    try:
        url = 'http://www.google.com/search'

        payload = {'q': 'site:ifsc.bankifsccode.com '+entities["bankName"], 'start': '0'}

        my_headers = {'User-agent': 'Mozilla/11.0'}

        r = requests.get(url, params=payload, headers=my_headers)
    except:
        return "IFSC search service is not Avilable. Please Try again later"

    pattern=re.compile(r'<h3 class="r"><a .*>(IFSC.*)...</a></h3>')

    result=pattern.findall(r.text.encode('utf-8'))

    if len(result)==0:
        result= "No match found"
    else:
        result = result[0] + "<br><br>" + result[1]
    return result

def activateUser(entities):
    url = "http://172.30.10.22/useraccount/activate/10/%s"%entities.get("userId")
    try:
        response = requests.put(url)
    except:
        return "Server Error,Please try again later."

    responseDict = json.loads(response.text)
    if responseDict.get("code")==203:
        return "Status : %s"%(responseDict.get("message"))
    elif responseDict.get("status")==500:
        return "No user account is registered with this user id"
    else:
        return "Status : %s"%(responseDict.get("customerRemarks"))

def getDetailsFromMobileNumber(entities):
    #http://172.30.10.119:7002/useraccount/mobile/10/12124?mobileno=5089005401
    url = "http://172.30.10.119:7002/useraccount/mobile/10/12124"
    parameters = {"mobileno": entities.get('mobileNumber').replace(" ", "").replace("-","")}
    try:
        response = requests.get(url, params=parameters)
    except:
        return "Server Error,Please try again later."
    try:
        responseDict = json.loads(response.text)
        return "Name : %s <br> User ID : %s <br>DOB : %s <Br>Status : %s<br>Tell <i>Activate {user id} </i> for user Activation"%(responseDict.get("firstName") +" "
                                                                           + responseDict.get("lastName"),
                                                                           responseDict.get("userAccountId")
                                                                           ,responseDict.get("dateOfBirthValue"),
                                                               responseDict.get("status"))
    except:
        return "No User Data found for the Mobile Number"

def hello(entities):
    return "hello"
def checkH2HTransactionStatus(entities):
    h2hSupportedBanks = {
        "ICICIHH",
        "DIBHH"
    }
    if not entities["routingKey"] and entities["routingKey"] not in h2hSupportedBanks:
        return "Routing key not supported."
    url = "http://172.30.10.119:8094/callyourpartner/YOM/%s"%entities["routingKey"]
    # {"txnType": "2O", "method": "enquiryTxn",  "txnRefNum": "0100016123165891",
    # "serviceProviderCode": "LULUXAE#####"
    #  }
    data = {"payload": json.dumps({
        "txnType":"2O",
        "method":"enquiryTxn",
        "txnRefNum":entities["txnNo"],
        "uploadDate": "2016-08-18 10:43:56.0",
        "serviceProviderCode": entities["serviceProviderCode"]}
    )}
    try:
        response = requests.post(url, data=data)
        responseDict = json.loads(response.text)
        if "statusDescription" not in responseDict:
            return "Status not available in Red currant."
        elif "Info" in responseDict["statusDescription"]:
            return responseDict["returnDescription"]
        else:
            return responseDict["statusDescription"]
    except:
        return "Redcurrant Server Not avilable"
    
def checkTransactionStatus(entities):
    #http://172.30.10.141:7027/rateboard/enquiry/0002/12312313?txnno=0107416113445215
    url = "http://172.30.10.141:7027/rateboard/enquiry/0002/12312313"
    parameters = {"txnno": entities['txnNo']}
    if not entities['txnNo']:
        return "Empty or Invalid Transaction number"

    response = requests.get(url, params=parameters)
    responseDict = json.loads(response.text)
    statusDesc = responseDict.get('statusDesc')
    if not (statusDesc):
        return "Invalid transaction number/Status not available in YOM"
    elif "HOST_2_HOST" in responseDict.get("paymentDetail").get("txnType2") and "Transmitted" in statusDesc:
        result = "Transmitted from YOM. Redcurrant API is offline"
        # entities["routingKey"] = responseDict.get('beneficiary').get("beneficiaryBank").get("draweeBankGroup")
        # entities["serviceProviderCode"] = responseDict.get('serviceProviderCode')
        #result = checkH2HTransactionStatus(entities)
    else:
        result = statusDesc
    return ("Txn no : %s <br> Customer Name : %s <br> status :<b>%s</b> <br>")%(entities['txnNo'],responseDict.get('customerDetail').get('firstName')+" "+responseDict.get('customerDetail').get('lastName'),result)

def calculateOutTime(entities):
    userId = "356000199"
    password = "lulu@123"
    if not userId or not password:
        return "username or password cant be empty"

    URL = 'http://172.30.15.124:2020/HRMS/j_acegi_security_check'
    session = requests.session()

    login_data = {
        'j_username': userId,
        'j_password': password,
        'Submit.x': '50',
        'Submit.y': '12',
    }
    headers = {
        "Referer": "http://172.30.15.124:2020/HRMS/login.do",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    try:
        r = session.post(URL, data=login_data, headers=headers)
        if "incorrect" in r.text:
            return "username or password incorrect"
    except:
        return "Server can't be reached"

    now = datetime.now()
    post_data = {
        'attendancedate': now.strftime("%d %b %Y"),
        'dummyattendancedate': now.strftime("%d %b %Y")
    }
    attendence_url = 'http://172.30.15.124:2020/HRMS/attendance/swipeinfo.do?action=show'
    r = session.post(attendence_url, post_data)
    result = re.findall(r'<td nowrap="true">.*&nbsp;(.*?)</td>', r.text)
    inTime = datetime.strptime(result[0], '%I:%M').time()
    defaultTime = datetime.strptime("9:30", '%I:%M').time()

    if (inTime <= defaultTime):
        # outTime = (defaultTime + timedelta(hours=8, minutes=30)).strftime('%I:%M')
        outTime = (datetime.combine(datetime.today(), defaultTime) + timedelta(hours=8, minutes=30))
    else:
        outTime = (datetime.combine(datetime.today(), inTime) + timedelta(hours=8, minutes=30))

    now += timedelta(hours=5, minutes=30)
    print(now)

    if now.time() >= outTime.time():
        result = "You can leave now. Have a nice time ahead :)"
    elif now.time() < outTime.time():
        diff = "%s hours and %s Minutes" % (str(outTime - now).split(":")[0], str(outTime - now).split(":")[1])
        result = "No. You punched in at %s, You can leave at %s ( %s more)" % (inTime, outTime.time(), diff)

    return result
def addEventToGoogleCalender(entities):
    from apiclient.discovery import build
    from httplib2 import Http
    from oauth2client import file, client, tools
    from datetime import datetime, timedelta

    try:
        import argparse

        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

    except ImportError:
        flags = Nones

    SCOPES = 'https://www.googleapis.com/auth/calendar'
    store = file.Storage('ikyActions/Zstorage.json')
    creds = store.get()

    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('ikyActions/client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store, flags) \
            if flags else tools.run(flow, store)

    CAL = build('calendar', 'v3', http=creds.authorize(Http()))

    GMT_OFF = '+05:30'  # GMT for india
    date_time_object = datetime.strptime(entities["date"], '%Y-%m-%d %H:%M:%S')
    START_DATE = date_time_object.strftime("%Y-%m-%dT%H:%M:%S" + GMT_OFF)
    END_DATE = (date_time_object + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S" + GMT_OFF)
    EVENT = {
        'summary': entities["event"],
        'start': {'dateTime': START_DATE},
        'end': {'dateTime': END_DATE},
    }

    e = CAL.events().insert(calendarId='primary',
                            sendNotifications=True, body=EVENT).execute()

    return ('''added Event : %r,
            at: %s''' % (e['summary'].encode('utf-8'),
                         e['start']['dateTime']))


print(getDetailsFromMobileNumber({"mobileNumber":"5089005401"}))