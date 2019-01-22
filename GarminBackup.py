# coding: utf-8
import requests
import json
import re
from urllib import urlencode
import os
import sqlite3
import sys
import smtplib


localPath = "C:\GarminBackup"
username="<<Garmin connect EMAIL>>"
password="<<Garmin Connect password>>"
maxDown = 50
dbFile = "backup.db"

mailEnable = 1
mailFrom = "<<EMAIL FROM>>"
mailTo = "<<EMAIL TO>>"
useSmptSSL = 1
smtpSrv = "<<SMTP SERVER>>:<<SMTP PORT>>"
smtpUser = "<<SMTP USER>>"
smtpPwd = "<<SMTP PASSWORD>>"

message = """From: Garmin Backup <%s>
To: %s
Subject: Garmin Backup Report

"""%(mailFrom,mailTo)


if not os.path.isdir(localPath):
    os.mkdir(localPath)
    
dbPath = localPath+"\\"+dbFile

con = sqlite3.connect(dbPath)

try:
    req = "SELECT * FROM backup LIMIT 1"
    cur = con.cursor()
    cur.execute(req)
    
    data = cur.fetchone()
except Exception:
    print "DB not ready"
    req = "CREATE TABLE \"backup\" (\"idActivity\" INTEGER NOT NULL , \"Name\" TEXT NOT NULL , \"Date\" TEXT NOT NULL, \"Type\" TEXT NOT NULL,\"File\" TEXT NOT NULL)"
    cur = con.cursor()
    cur.execute(req)
    req = "CREATE  INDEX \"main\".\"Ibackup\" ON \"backup\" (\"idActivity\" DESC, \"Type\" DESC)"
    cur.execute(req)
    
url_login = "https://sso.garmin.com/sso/signin?service=https%3A%2F%2Fconnect.garmin.com%2Fmodern%2F&webhost=https%3A%2F%2Fconnect.garmin.com&source=https%3A%2F%2Fconnect.garmin.com%2Fen-US%2Fsignin&redirectAfterAccountLoginUrl=https%3A%2F%2Fconnect.garmin.com%2Fmodern%2F&redirectAfterAccountCreationUrl=https%3A%2F%2Fconnect.garmin.com%2Fmodern%2F&gauthHost=https%3A%2F%2Fsso.garmin.com%2Fsso&locale=en_US&id=gauth-widget&cssUrl=https%3A%2F%2Fstatic.garmincdn.com%2Fcom.garmin.connect%2Fui%2Fcss%2Fgauth-custom-v1.2-min.css&privacyStatementUrl=%2F%2Fconnect.garmin.com%2Fen-US%2Fprivacy%2F&clientId=GarminConnect&rememberMeShown=true&rememberMeChecked=false&createAccountShown=true&openCreateAccount=false&displayNameShown=false&consumeServiceTicket=false&initialFocus=true&embedWidget=false&generateExtraServiceTicket=true&generateTwoExtraServiceTickets=false&generateNoServiceTicket=false&globalOptInShown=true&globalOptInChecked=false&mobile=false&connectLegalTerms=true&locationPromptShown=true"
url_post = 'https://connect.garmin.com/post-auth/login?'
url_activity    = 'https://connect.garmin.com/modern/proxy/activitylist-service/activities/search/activities?'

#OLD url_gc_gpx_activity = 'https://connect.garmin.com/modern/proxy/activity-service-1.1/gpx/activity/'
url_gc_gpx_activity = 'https://connect.garmin.com/modern/proxy/download-service/export/gpx/activity/'
#OLD url_gc_kml_activity = 'https://connect.garmin.com/modern/proxy/activity-service-1.1/kml/activity/'
url_gc_kml_activity = 'https://connect.garmin.com/modern/proxy/download-service/export/kml/activity/'
#OLD url_gc_tcx_activity = 'https://connect.garmin.com/modern/proxy/activity-service-1.1/tcx/activity/'
url_gc_tcx_activity = 'https://connect.garmin.com/modern/proxy/download-service/export/tcx/activity/'
url_gc_original_activity = 'https://connect.garmin.com/modern/proxy/download-service/files/activity//'
url_gc_csv_activity = 'https://connect.garmin.com/csvExporter/'

url_minAct ="https://connect.garmin.com/minactivities"

s = requests.Session()

#Forcing headers to avoid 500 error when downloading file
s.headers.update({"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
"Accept-Encoding":"gzip, deflate, sdch",'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36','origin' : 'https://sso.garmin.com','referer':'https://sso.garmin.com/sso/signin?service=https%3A%2F%2Fconnect.garmin.com%2Fmodern%2F&webhost=https%3A%2F%2Fconnect.garmin.com&source=https%3A%2F%2Fconnect.garmin.com%2Fen-US%2Fsignin&redirectAfterAccountLoginUrl=https%3A%2F%2Fconnect.garmin.com%2Fmodern%2F&redirectAfterAccountCreationUrl=https%3A%2F%2Fconnect.garmin.com%2Fmodern%2F&gauthHost=https%3A%2F%2Fsso.garmin.com%2Fsso&locale=en_US&id=gauth-widget&cssUrl=https%3A%2F%2Fstatic.garmincdn.com%2Fcom.garmin.connect%2Fui%2Fcss%2Fgauth-custom-v1.2-min.css&privacyStatementUrl=%2F%2Fconnect.garmin.com%2Fen-US%2Fprivacy%2F&clientId=GarminConnect&rememberMeShown=true&rememberMeChecked=false&createAccountShown=true&openCreateAccount=false&displayNameShown=false&consumeServiceTicket=false&initialFocus=true&embedWidget=false&generateExtraServiceTicket=true&generateTwoExtraServiceTickets=false&generateNoServiceTicket=false&globalOptInShown=true&globalOptInChecked=false&mobile=false&connectLegalTerms=true&locationPromptShown=true'})

#first call to init session
res = s.get(url_login)

#posting credentials
post_data = {'username': username, 'password': password, 'embed': 'false'}  # Fields that are passed in a typical Garmin login.
res = s.post(url_login,post_data)

#testing login ticket (CASTGC)
login_ticket = None
for cookie in s.cookies:
    print cookie.name
    if cookie.name == 'CASTGC':
        login_ticket = cookie.value
        break
if not login_ticket:
	raise Exception('Did not get a ticket cookie. Cannot log in. Did you enter the correct username and password?')

#Doing post login to validate ticket
login_ticket = 'ST-0' + login_ticket[4:]
s.get(url_post + 'ticket=' + login_ticket)

rawstr = r"""filename="*([\w|\.]*)"*"""
compile_obj = re.compile(rawstr,  re.IGNORECASE)

tmo = s.get("https://connect.garmin.com/modern")
tmo = s.get("https://connect.garmin.com/legacy/session")

end = 0
currentPage = 0
nbDown = 0


while not end:
    print "========= Staring download from "+str(currentPage*maxDown)+ "================="
    search_params = {'start': currentPage*maxDown, 'limit': maxDown}
    result = s.get(url_activity + urlencode(search_params))
    
    json_results = json.loads(result.text.encode("UTF8"))
    #print json_results
    try:
        activities = json_results
    except:
        end=1

    nbDownPage = 0

    for activity in activities:
        nbDownPage += 1
        currentActivityId = str(activity['activityId'])
        currentActivityName =  activity['activityName']
        currentActivityTime = str(activity['beginTimestamp'])

        if(currentActivityName is None):
            currentActivityName = "Unknown"
        
        urls = [
            ["csv",url_gc_csv_activity+currentActivityId+".csv"],
            ["Original",url_gc_original_activity+currentActivityId],
            ["gpx",url_gc_gpx_activity+currentActivityId+"?full=true"],
            ["kml",url_gc_kml_activity+currentActivityId+"?full=true"],
            ["tcx",url_gc_tcx_activity+currentActivityId+"?full=true"]
            ]

        print 'Garmin Connect activity: [' + currentActivityId + ']',
        print currentActivityName,
        print '\t' + currentActivityTime + ','
        formatDownloaded =0
        for tmpUrl in urls :
            req = "SELECT count(*) as nb FROM backup WHERE idActivity = %s AND Type = '%s'"%(currentActivityId,tmpUrl[0])
            cur.execute(req)
            res=cur.fetchone()
            if res[0] == 0:
                
                r = s.get(tmpUrl[1], stream=True)
                headerContent = r.headers.get('content-disposition')
                
                if headerContent is not None or tmpUrl[0] == "csv":
                    print "Downloading "+tmpUrl[0]+" file from : "+tmpUrl[1]+""
                    nbDown += 1

                    #Generating email
                    if formatDownloaded == 0:
                        message += "Downloaded : %s - %s (%s) Format : "%(currentActivityName,currentActivityTime,currentActivityId)
                    message += " %s "%(tmpUrl[0])
                
                    if tmpUrl[0] == "csv":
                        fileName = tmpUrl[1].split('/')[-1:][0]
                    else:
                        headerContent = r.headers.get('content-disposition')
                        match_obj = compile_obj.search(headerContent)
                        fileName = match_obj.group(1)
                    dstDir = localPath + "\\"+tmpUrl[0]+"\\"
                    if not os.path.isdir(dstDir):
                        print "Creating directory "+dstDir
                        os.mkdir(dstDir)
                    dstFile = dstDir + fileName
                    with open(dstFile, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024): 
                            if chunk: 
                                f.write(chunk)
                
                    cur.execute("INSERT INTO backup(idActivity,Name,Date,Type,File) VALUES (?,?,?,?,?)",(currentActivityId,currentActivityName,activity['beginTimestamp'],tmpUrl[0],dstFile))
                    con.commit()
                    formatDownloaded += 1

        if formatDownloaded > 1 :
            message += "\r\n"
    currentPage += 1
    if nbDownPage == 0:
        end = 1
con.close()


if mailEnable and nbDown > 0 :
    message = message.encode("UTF8")
    if useSmptSSL :
        smtpObj = smtplib.SMTP_SSL(smtpSrv)
    else :
        smtpObj = smtplib.smtp(smtpSrv)
    smtpObj.login(smtpUser,smtpPwd)
    smtpObj.sendmail(mailFrom, mailTo, message)         
    print "Successfully sent email"
    smtpObj.quit()