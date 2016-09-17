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
    
url_login = "https://sso.garmin.com/sso/login?service=https%3A%2F%2Fconnect.garmin.com%2Fpost-auth%2Flogin&webhost=olaxpw-connect20.garmin.com&source=https%3A%2F%2Fconnect.garmin.com%2Fen-US%2Fsignin&redirectAfterAccountLoginUrl=https%3A%2F%2Fconnect.garmin.com%2Fpost-auth%2Flogin&redirectAfterAccountCreationUrl=https%3A%2F%2Fconnect.garmin.com%2Fpost-auth%2Flogin&gauthHost=https%3A%2F%2Fsso.garmin.com%2Fsso&locale=fr&id=gauth-widget&cssUrl=https%3A%2F%2Fstatic.garmincdn.com%2Fcom.garmin.connect%2Fui%2Fcss%2Fgauth-custom-v1.2-min.css&clientId=GarminConnect&rememberMeShown=true&rememberMeChecked=false&createAccountShown=true&openCreateAccount=false&usernameShown=false&displayNameShown=false&consumeServiceTicket=false&initialFocus=true&embedWidget=false&generateExtraServiceTicket=false"
url_post = 'https://connect.garmin.com/post-auth/login?'
url_activity    = 'https://connect.garmin.com/proxy/activity-search-service-1.0/json/activities?'

#OLD url_gc_gpx_activity = 'https://connect.garmin.com/modern/proxy/activity-service-1.1/gpx/activity/'
url_gc_gpx_activity = 'https://connect.garmin.com/modern/proxy/download-service/export/gpx/activity/'
#OLD url_gc_kml_activity = 'https://connect.garmin.com/modern/proxy/activity-service-1.1/kml/activity/'
url_gc_kml_activity = 'https://connect.garmin.com/modern/proxy/download-service/export/kml/activity/'
#OLD url_gc_tcx_activity = 'https://connect.garmin.com/modern/proxy/activity-service-1.1/tcx/activity/'
url_gc_tcx_activity = 'https://connect.garmin.com/modern/proxy/download-service/export/tcx/activity/'
url_gc_original_activity = 'https://connect.garmin.com/modern/proxy/download-service/files/activity/'
url_gc_csv_activity = 'https://connect.garmin.com/csvExporter/'

url_minAct ="https://connect.garmin.com/minactivities"

s = requests.Session()

#Forcing headers to avoid 500 error when downloading file
s.headers.update({"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
"Accept-Encoding":"gzip, deflate, sdch",'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/1337 Safari/537.36'})

#first call to init session
res = s.get(url_login)

#posting credentials
post_data = {'username': username, 'password': password, 'embed': 'true', 'lt': 'e1s1', '_eventId': 'submit', 'displayNameRequired': 'false'}  # Fields that are passed in a typical Garmin login.
res = s.post(url_login,post_data)

#testing login ticket (CASTGC)
login_ticket = None
for cookie in s.cookies:
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

#Post login to fix 403 error
tmp = s.get("http://connect.garmin.com/modern")
tmp = s.get("https://connect.garmin.com/legacy/session")

end = 0
currentPage = 0
nbDown = 0


while not end:
    print "========= Staring download from "+str(currentPage*maxDown)+ "================="
    search_params = {'start': currentPage*maxDown, 'limit': maxDown}
    result = s.get(url_activity + urlencode(search_params))
    
    json_results = json.loads(result.text.encode("UTF8"))
    try:
        activities = json_results['results']['activities']
    except:
        end=1
    

    for activity in activities:
        urls = [
            ["csv",url_gc_csv_activity+activity['activity']['activityId']+".csv"],
            ["Original",url_gc_original_activity+activity['activity']['activityId']],
            ["gpx",url_gc_gpx_activity+activity['activity']['activityId']+"?full=true"],
            ["kml",url_gc_kml_activity+activity['activity']['activityId']+"?full=true"],
            ["tcx",url_gc_tcx_activity+activity['activity']['activityId']+"?full=true"]
            ]

        currentActivityId = activity['activity']['activityId']
        currentActivityName =  activity['activity']['activityName']['value']
        currentActivityTime = activity['activity']['beginTimestamp']['display']
        print 'Garmin Connect activity: [' + currentActivityId + ']',
        print currentActivityName,
        print '\t' + currentActivityTime + ','
        formatDownloaded =0
        for tmpUrl in urls :
            req = "SELECT count(*) as nb FROM backup WHERE idActivity = %s AND Type = '%s'"%(activity['activity']['activityId'],tmpUrl[0])
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
                
                    cur.execute("INSERT INTO backup(idActivity,Name,Date,Type,File) VALUES (?,?,?,?,?)",(activity['activity']['activityId'],activity['activity']['activityName']['value'],activity['activity']['beginTimestamp']['display'],tmpUrl[0],dstFile))
                    con.commit()
                    formatDownloaded += 1

        if formatDownloaded > 1 :
            message += "\r\n"
    currentPage += 1
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