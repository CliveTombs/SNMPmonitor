# SNMPmonitor
Python script to interrogate multiple OIDS on multiple devices
The input csv file must be zipped with a password for security.
The number of colomns may vary but must contain pairs consisting of OID Text and then the OID. The number of Text/OID pairs is described in a separate colomn.
The origin of each OID has two descriptors. These could be, for example "Office" and "Printer" The sequence is described below:-
ID1,ID2,IP,READCOMMUNITY,SNMPVer,No. of OIDS,OIDTEXT1,OID1,OIDTEXT2,OID2,etc...
Cntl + c to stop
----------------------------------------------------------------------------
This branch will contain a GUI version and aim to compile the zip file too.
