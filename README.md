# freenas
Scripts to automate tasks within my FreeNAS setup

RsyncAutomator.py   
  Automates two types of backups within a FreeNAS system, emails results at script completion                
    Internal: Rsyncs multiple shares to a Zpool allowing one or more directories to be excluded           
    External: Rsyncs the target Zpool used in the internal process to a UFS formatted external drive       
