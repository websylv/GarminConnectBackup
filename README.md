# GarminConnectBackup

This script backup all your garmin connect activities without using the API
All the availaible files will be downloaded (fit , gpx, kml , ...)


This script run on python 2.7
You need to install first the module : requests 
pip install requests

Then edit the settings of the script :

```
####
# SETTINGS
####
localPath = "D:\GarminBackup" --> Base directory for you
username="<<enter Garmin connect email address>>" --> your garmin connect email address
password="<<enter Garmin connect password>>"

mailEnable = 1
mailFrom = "<<EMAIL FROM>>"
mailTo = "<<EMAIL TO>>"
useSmptSSL = 1
smtpSrv = "<<SMTP SERVER>>:<<SMTP PORT>>"
smtpUser = "<<SMTP USER>>"
smtpPwd = "<<SMTP PASSWORD>>"
#########
```

If you want to force a new download of all activities, juste delete the DB file backup.db
