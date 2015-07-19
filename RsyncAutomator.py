#!/usr/bin/env python
##############################################################################################################
#                                                RsyncAutomator.py                                           # 
#                                                                                                            #
#												                              Ian Day                                                #
#                                                iandday@gmail.com                                           #
#                                                    20150719                                                #
#                                                                                                            #
# Automates two types of backups within a FreeNAS system, emails results at script completion                #
#	Internal: Rsyncs multiple shares to a Zpool allowing one or more directories to be excluded                #
#   External: Rsyncs the target Zpool used in the internal process to a UFS formatted external drive         #
#                                                                                                            #
# usage: RsyncAutomator.py [-h] [-v] function                                                                #
# FreeNAS Rsync Assistant                                                                                    #
#                                                                                                            #
# positional arguments:                                                                                      #
#  function       Backup destination: internal or external                                                   #
#                                                                                                            #
# optional arguments:                                                                                        #
#  -h, --help     show this help message and exit                                                            #
#  -v, --version  show program's version number and exit                                                     #
##############################################################################################################

import argparse
import datetime
from email.mime.text import MIMEText 
import smtplib
import subprocess

def func_rsync(sourceDir, destDir, excludeDirectories = []):
	'''Rsync sourceDir to destDir omitting list excludeDirectories.  Returns dictionary of stdOut and stdErr'''
	baseCommand = "rsync -rvh --update --delete --stats"
	exclude = ""
	if excludeDirectories != []:
		for directory in excludeDirectories:
			exclude += ("--exclude=" + directory + " ") 
		strCommand = baseCommand + " " + exclude + " " + sourceDir + " " + destDir
	if excludeDirectories == []:
		strCommand = baseCommand + " " + sourceDir + " " + destDir
	command = subprocess.Popen(strCommand.split(),stdout=subprocess.PIPE)
	return command.communicate()

def func_internal():
	'''Syncs multiple shares to backup volume, additional shares can be added by copying demo code under Rsync function calls.  Returns error status and email body in message'''
	#Variable Initialization
	resultsDictLog={}
	resultsDictError={}
	internalError = False
	startTime = datetime.datetime.now()
	message = []
	message.append("Rsync Job Status\n")
		
	#Rsync function calls
	#ExampleCode
	# tempResults = func_rsync("PATHTOBACKUP", "TARGETPATH", [DIRECTORIESTOEXCLUDE])
	# resultsDictLog['SHARENAME'] = tempResults[0]
	# if tempResults[1] is None:
		# resultsDictError['SHARENAME'] = None
	# else:
		# resultsDictError['SHARENAME'] = tempResults[1]
		
	tempResults = func_rsync("/mnt/Users/users/ian/", "/mnt/Backup/backup/VolumeMirror/home/", ['Downloads/', 'Desktop/', 'Documents/'])
	resultsDictLog['Home Directory'] = tempResults[0]
	if tempResults[1] is None:
		resultsDictError['Home Directory'] = None
	else:
		resultsDictError['Home Directory'] = tempResults[1]

	tempResults = func_rsync("/mnt/Repository/media/", "/mnt/Backup/backup/VolumeMirror/media/", ['IpadConverted/'])
	resultsDictLog['Media Directory'] = tempResults[0]
	if tempResults[1] is None:
		resultsDictError['Media Directory'] = None
	else:
		resultsDictError['Media Directory'] = tempResults[1]
	
	tempResults = func_rsync("/mnt/Recordings/recordings/DBBU/", "/mnt/Backup/backup/VolumeMirror/htpc/myth/DBBU/")
	resultsDictLog['Myth DB'] = tempResults[0]
	if tempResults[1] is None:
		resultsDictError['Myth DB'] = None
	else:
		resultsDictError['Myth DB'] = tempResults[1]	
	
	tempResults = func_rsync("/mnt/Repository/repository/", "/mnt/Backup/backup/VolumeMirror/repository/")
	resultsDictLog['Repository'] = tempResults[0]
	if tempResults[1] is None:
		resultsDictError['Repository'] = None
	else:
		resultsDictError['Repository'] = tempResults[1]
	
	#Parse results and return email body in message	
	for log in resultsDictLog:
		if resultsDictError[log] is None:
			message.append("  " + log + ": Completed successfully")
			results = func_parse_output(resultsDictLog[log], "internal")
			for line in results:
				message.append("   " + line + ":" + results[line])
			message.append('\n')
		else:
			message.append( log + ": Completed with errors")
			results = func_parse_output(resultsDictLog[log], "internal")
			for line in results:
				message.append("   " + line + ":" + results[line])
			message.append('\n')
			internalError = True
	endTime = datetime.datetime.now()
	elapsedTime = endTime - startTime
	message.append("Start Time: " + startTime.strftime("%H:%M:%S"))
	message.append("End  Time: " + endTime.strftime("%H:%M:%S"))
	message.append("Elapsed Time: " + str(elapsedTime).split('.', 2)[0])
	return (internalError, message)

def func_external():
	'''Backup of ZFS volume to an external USB drive formated with UFS file system, utilizes drive label to mount instead of device number'''
	startTime = datetime.datetime.now()
	deleted = 0
	copied = 0
	message = []
	mountBase = "mount /dev/label/"
	driveLabel = "extUSB"
	mountDst = "/mnt/extDrive"
	mountCmd = mountBase + driveLabel + " " + mountDst
	subprocess.Popen(mountCmd.split())
	newmountDst = mountDst + '/'
	backupCommand = subprocess.Popen(['rsync','-rhv', '--stats', '--update', '--delete',  '/mnt/Backup/backup/VolumeMirror/', newmountDst + '/'],stdout=subprocess.PIPE)
	backupOut = backupCommand.communicate()
	subprocess.Popen(["umount", mountDst])
	endTime = datetime.datetime.now()
	results = func_parse_output(backupOut, "external")		
	
	if backupOut[1] is None:
		externalError = False
		message.append("External Backup: Completed successfully")
	else:
		externalError = False
		message.append( "External Backup: Completed with errors")	
	for line in results:
		message.append("   " + line + ":" + results[line])
	elapsedTime = endTime - startTime
	message.append("   Start Time         : " + startTime.strftime("%H:%M:%S"))
	message.append("   End Time          : " + endTime.strftime("%H:%M:%S"))
	message.append("   Elapsed Time    : " + str(elapsedTime).split('.', 2)[0])
	return (externalError, message)
	
def func_parse_output(syncOut, method):
	'''parse rsync stats output in syncOut based on method, returns dictionary of values to be included in email'''
	if method == "internal":
		lines = syncOut.split('\n')
	elif method == "external":
		lines = syncOut[0].split('\n')
	parsed={}
	parsed["Total Files          "] = lines[-17].split(':',1)[1]
	parsed["New Files           "] = lines[-16].split(':',1)[1]
	parsed["Deleted Files      "] = lines[-15].split(':',1)[1]
	parsed["Total Size          "] = lines[-13].split(':',1)[1]
	parsed["Transferred Size "] = lines[-12].split(':',1)[1]
	return parsed
	
	
def func_send_email(subject, message):
	'''sends message and subject in an email utilizing Gmail account to specified addresses'''
	SMTP_SERVER = "smtp.gmail.com"
	SMTP_PORT = 587
	SMTP_USERNAME = "EMAIL@gmail.com"
	SMTP_PASSWORD = "PASSWORD"
	#Multiple to addresses possible, separate addresses by a comma
	EMAIL_TO = ["EMAIL@gmail.com"]
	EMAIL_FROM = "EMAIL@gmail.com"
	EMAIL_SUBJECT = subject

	DATE_FORMAT = "%Y%m%d"
	EMAIL_SPACE = ", "
	msg = MIMEText(message)
	msg['Subject'] = EMAIL_SUBJECT + " %s" % (datetime.date.today().strftime(DATE_FORMAT))
	msg['To'] = EMAIL_SPACE.join(EMAIL_TO)
	msg['From'] = EMAIL_FROM
	mail = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
	mail.starttls()
	mail.login(SMTP_USERNAME, SMTP_PASSWORD)
	mail.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
	mail.quit()


if __name__=='__main__':
	parser = argparse.ArgumentParser(description='FreeNAS Rsync Assistant')
	parser.add_argument("function", help = 'Backup destination: internal or external')
	parser.add_argument('-v', '--version', action='version', version='%(prog)s (version 1.0)')
	args = parser.parse_args()
 
	if args.function.upper() == "INTERNAL":
		internalError, internalMessage = func_internal()
		if internalError == False:
			func_send_email("FreeNAS Backup Volume Sync", '\n'.join(internalMessage))
		else:
			func_send_email("ERROR - FreeNAS Backup Volume Sync", '\n'.join(internalMessage))

	if args.function.upper() == "EXTERNAL":
		externalError, externalMessage = func_external()
		if externalError == False:
			func_send_email("FreeNAS External Backup", '\n'.join(externalMessage))
		else:
			func_send_email("ERROR - FreeNAS External Backup", '\n'.join(externalMessage))
	
