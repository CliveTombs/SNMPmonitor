#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Sat Jul 18 09:26:53 2020.
By clive

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.

Versions:
v00      Working version for one oid from one source.
v0.1   - added multi source ability and mulity OID.
v0.2 -   releady for use
v0.3 -   added progress numbers to output screen
v0.4 -   added skipping other OIDs for a unit where the first one fails.
v0.4.1 - fixed where if there was a comma in the returned value it messed up the csv by changing the chatracter to a `
v0.4.2 - enhancement to zip file selection.
v1.0.1 - Graphical release using QT5
v1.0.2 - Windows compatibility. 1. Not zipping files, 2.Not creating a blank csv file
         1.zip module changed for py7zr for greater flexability of zip methods and compatability with win and lin.
         2. routine was missing. could never have worked.

"""
from mainui import Ui_MainWindow  # uncomment when the .ui is converted to a .py
import sys
import subprocess
import time
from hnmp import SNMP
import getpass
import os
import py7zr
# from zipfile import ZipFile
# import zipfile
import re
import errno
# from PyQt5 import uic
from PyQt5.QtCore import QTimer, QEventLoop
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox

version = "v1.0.2"
Log_Location = "Monitor_files/"

# qtCreatorFile = "main.ui"  # Enter file here. Comment out when ui is converted to a .py
# Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):

        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.running = True
        self.tabWidget.setCurrentIndex(0)
        self.textEdit_results.setText("Log")
        self.helpfile()
        self.caption = ("Read Multiple OIDS from Multiple SNMP devices  User-" + getpass.getuser() + "   " + str(version))
        self.label_version.setText("version " + version)
        self.label_user.setText("User- " + getpass.getuser())
        self.Buttongetfile.clicked.connect(self.getzipfile)
        self.Buttonmakecsv.clicked.connect(self.makecsv)
        self.ButtonBoxSetup.accepted.connect(self.gotoaccepted)
        self.Button_zip.clicked.connect(self.makezipfile)
        self.Button_Run.clicked.connect(self.gotorun)
        self.Button_Stop.clicked.connect(self.stop)

    def helpfile(self):
        self.textEdit_help.setHtml("""<font color=#202020 size='6'>SNMP Monitor Guide</font>""")
        self.textEdit_help.append(
            """<font color=#404040 size='5'>Setup Tab<br></font
            <font size='4'>This is where the Zip file is selected. From this tab an empty CSV file can be
            created. It will contain one line as an example.<br>If, however, the folder from which the
            program is running already contains the CSV file, it will be overwriten if one desires <br>
            The time between readings can be set in seconds, minutes or hours as selected. Decimal points
            can be used.<br>
            The OK button is to move on to the Run dialogue once all the parameters have been set.<br>
            The Cancel button will close the program like clicking the top right X.<br></font""")
        self.textEdit_help.append("""
            <font font color=#404040 size='5'>Run Tab <br></font
            <font size='4'> The top portion of this screen is the STATUS line. It gives guidance as to the current action.<br>
            Below this the progress is shown. The name of the zip file and the creation of the log files is confirmed.<br>
            Once the Run button is clicked the continuing progress though the monitored points is displayed. If any OIDs are
            unresponsive the program will move on filling the log with --- for that reading. If it is the first OID which fails
            it is assumed that they all will due to a comms issue and the entire unit is skipped. Between scans of the OIDs
            an LCD countdown in seconds is displayed.<br>
            If the STOP button is pressed the program will finish its cycle then stop. The top STATUS line will indicate this.
            The program can be restatred by clicking the Run button and the log file will be continued albeit with time gaps in
            the data, of course.<br></font""")
        self.textEdit_help.append("""
            <font color=#404040 size='5'>Create Zip Tab <br></font
            <font size='4'>The unitdetails.csv file in the folder from which the program is run can be zipped and password
            protected from the tab. Just enter the name of the file to be created along with the password to be used and click
            "Zip Now". The file extension needs to be entered, i.e. "filename.zip" not just "filename"</font>""")

    def makezipfile(self):
        my_filter = [{"id": py7zr.FILTER_CRYPTO_AES256_SHA256}]
        try:
            outfile = self.line_enter_filename.displayText()
            infile = "unitdetails.csv"
            zipPass = self.line_ZipPassword.displayText()
            if os.name == "posix":  # Detect Linux OS
                subprocess.call(["zip", "-P", zipPass, outfile, infile])
            else:
                # subprocess.call([, zipPass, outfile, infile])
                #  subprocess.call(["7z.exe", "a", "-tzip", "-p" + zipPass, outfile, infile])
                with py7zr.SevenZipFile(outfile, 'w', filters=my_filter, password=zipPass) as archive:
                    archive.writeall(infile)
        except Exception as e:
            #  Go back to front page to display error box
            self.tabWidget.setCurrentIndex(0)
            self.label_selection.setText("Error: " + str(e))
            return

    def gotorun(self):

        self.running = True
        self.lineEdit_status.setText("Run in Progress")
        self.delay(0.5)
        while self.running is True:
            self.start = time.time()
            for self.n in range(1, self.L):  # the number of entries in unitdetails.csv
                self.readstructure()  # puts the value for one line of unitdetails.csv into the list variables
                self.read()
                self.writelog()
            while self.start > time.time() - float(self.delaysecs):  # calculates when the time is up
                self.d = int(self.start - (time.time()-float(self.delaysecs)))
                self.lcdNumbercountdown.display(self.d)
                if self.running is False:
                    self.lineEdit_status.setText("Run Stopped")
                    return
                self.delay(0.5)

    def stop(self):
        """
        Is read by the gotorun def and makes it stop if the stop button has been subsequently pressed.

        Returns
        -------
        None.

        """
        self.running = False

    def gotoaccepted(self):
        '''
        The OK button has been pressed.

        Returns
        -------
        None.

        '''
        try:
            self.BUtime = time.strftime(
                "%Y.%m.%d-%H.%M.%S")  # time in a string format as described, the log files will use this in the filename
            self.createdir()
            self.tabWidget.setCurrentIndex(1)  # get the run tab displayed.
            self.readUnitList()  # Also find the number of different units i.e.(self.L)
            self.timedelay()  # read the length of time between readings. (self.delaysecs)
            for self.n in range(1, self.L):
                self.readstructure()
                if self.success is True:
                    self.createlog()
                else:
                    self.textEdit_results.append("The following error occured:\n" + str(self.report))
                    return
            self.lineEdit_status.setText("Click RUN when you want to start")
        except Exception as e:
            self.tabWidget.setCurrentIndex(0)
            self.label_selection.setText("Error: " + str(e))

    def makecsv(self):
        '''
        Creates a text file (csv format) for the storage of the OIDS text and OID. The file is empty of all but one line of
        test data for use as an example.

        Returns
        -------
        None.

        '''
        if os.path.isfile("unitdetails.csv"):
            msg = QMessageBox()
            msg.setWindowTitle("File Exists Warning")
            msg.setText("There is a file \"unitdetails.csv\" already here.\rDo you want to overwrite it?")
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)  # seperate buttons with "|"
            msg.setDefaultButton(QMessageBox.No)
            x = msg.exec_()  # this will show our messagebox
            if x == msg.Yes:
                with open(os.path.normpath("unitdetails.csv"), mode='w', encoding='utf8', newline='\r\n') as f:  # create the file
                    f.write(
                        "ID1,ID2,IP,READCOMMUNITY,SNMPVer,No. of OIDS,OIDTEXT1 ,OID1,OIDTEXT2,OID2\nOffice,printer,192.168.1.4,public,1,1,Uptime,.1.3.6.1.2.1.1.3.0")
                QMessageBox.about(self, "File Written", "A new \"unitdetails.csv\" file was written")
            else:
                QMessageBox.about(self, "CSV file ", "No new file was written")
        else:
            with open(os.path.normpath("unitdetails.csv"), mode='w', encoding='utf8', newline='\r\n') as f:  # create the file
                f.write(
                    "ID1,ID2,IP,READCOMMUNITY,SNMPVer,No. of OIDS,OIDTEXT1 ,OID1,OIDTEXT2,OID2\nOffice,printer,192.168.1.4,public,1,1,Uptime,.1.3.6.1.2.1.1.3.0")
            QMessageBox.about(self, "File Written", "A new \"unitdetails.csv\" file was written")

    def readUnitList(self):
        '''
        Takes the selected file and opens the content of unitdetails.csv from within and puts
        them in a list. The first entry of the list are the column headings.
        Throws error if password is wrong or any other problem.


        Returns
        -------
        None.

        '''

        try:
            with py7zr.SevenZipFile(self.zip_file, mode='r', password=self.line_pw.text()) as archive:
                for fname,  bio in archive.read("unitdetails.csv").items():
                    content = (bio.read().decode())
                self.contentlist = content.split('\n')
                self.L = len(self.contentlist)  # number of lines in the csv file
                self.textEdit_results.setText("Logging - read " + str(self.L - 1) + " lines from " + self.zip_file)
#            archive.close()
#        try:
#            with ZipFile(self.zip_file) as z:
#                self.content = z.read("unitdetails.csv", pwd=self.line_pw.text().encode()).decode()
#                z.close()
#            self.contentlist = self.content.split('\n')
#            self.L = len(self.contentlist) - 1  # number of lines in the csv file
#            self.textEdit_results.setText("Logging - read " + str(self.L - 1) + " lines from " + self.zip_file)

        except Exception as e:
            #  Go back to front page to display error box
            self.tabWidget.setCurrentIndex(0)
            self.label_selection.setText("Error: " + str(e))
            return

    def getzipfile(self):
        '''
        The zipfile contains directories named by the unit
        designation i.e. PA1.
        The module selects the zip file and returns its path. Then starts
        the Unit selection process.

        Returns
        -------
        None.

        '''
        self.dir_path = QFileDialog.getOpenFileName(self, "Choose the zip file", "~/")
        self.zip_file = (self.dir_path[0])  # path to the zip file
        self.label_selection.setText("File selected- " + self.zip_file)

    def readstructure(self):  # was fileline
        #  break the list (line) apart and strip white-space
        #            self.contentlist is a list of the units to interogate
        self.success = False
        try:

            self.line = self.contentlist[self.n]
            self.NUMOID = int(re.split(',', (self.line))[5].strip())  # find how many OIDS in the line accross the list
            self.READCOMMUNITY = re.split(',', str(self.line))[3].strip()  # third entry on a line
            self.SNMPV = re.split(',', str(self.line))[4].strip()
            self.ID1 = re.split(',', str(self.line))[0].strip()  # where in the country is it
            self.ID2 = re.split(',', str(self.line))[1].strip()  # and which ID2lifier there is it
            self.IP = re.split(',', str(self.line))[2].strip()  # ip address
# Set up the lists to receive the OIDS and text from the input sheet. because there are a variable number of them on each line they have to be done in a separate loop
            self.OIDTEXT = []
            self.OID = []
            for o in range(self.NUMOID):  # see above - the number of oids on the line
                self.OIDTEXT.append(re.split(',', str(self.line))[(6+(2*o))].strip())
                self.OID.append(re.split(',', str(self.line))[7+(2*o)].strip())

            self.success = True
        except Exception as e:
            self.success = False
            self.report = e

    def delay(self, amount):
        loop = QEventLoop()
        QTimer.singleShot(int(amount*1000), loop.quit)
        loop.exec_()

    def createdir(self):
        '''
        Makes the directory to store the logs in. If The directory exists just carry on.

        Parameters
        ----------
        None.

        Returns
        -------
        None.

        '''
        try:
            os.makedirs(os.path.normpath(Log_Location))
        except OSError as exception:
            if exception.errno != errno.EEXIST:  # if the folder already exists do not make it.
                self.textEdit_results.append("Folder is present")
                raise
            else:  # if it does not exist make it
                self.textEdit_results.append("Making Directory")
        finally:
            self.delay(0.1)

    def createlog(self):
        '''
        Creates a log csv for each line in the csv file.
        Names the file by ID1 ID2 and time to make it unique.
        In the first line of the file write the unit position and title each colomn

        Parameters
        ----------
        BUtime : TYPE string
            DESCRIPTION. The toime in a defined string format
        ID1 : TYPE string
            DESCRIPTION. Location of the unit
        ID2 : TYPE string
            DESCRIPTION. The name of the unit on ID1
        num : TYPE int
            DESCRIPTION. The time in seconds between scans
        NUMOID : TYPE int
            DESCRIPTION. How many OID/OIDText pairs in the list
        OIDTEXT : TYPE list
            DESCRIPTION. contains all the descriptions of the parameters

        Returns
        -------
        None.

        '''
        if os.path.isfile(os.path.normpath(Log_Location+"Monitor_Log-" + self.ID1 + "-" + self.ID2 + "-" + self.BUtime + ".csv")) is False:  # if the file does not already exist
            with open(os.path.normpath(Log_Location+"Monitor_Log-" + self.ID1 + "-" + self.ID2 + "-" + self.BUtime + ".csv"), mode='w', encoding='utf8', newline='\r\n') as f:  # create the file
                f.write("Monitor log by " + getpass.getuser() + " at " + self.ID1 + " - " + self.ID2)
    #  now, for each OID write the colomn title
                for r in range(self.NUMOID):
                    f.write("," + self.OIDTEXT[r])
                f.write("\n")
                f.close()
            self.textEdit_results.append("Log CSV files for" + self.ID1 + " - " + self.ID2 + " initiated.")
        else:
            self.textEdit_results.append("Log CSV files were already there!")

    def writelog(self):
        '''
        Routine for adding all the OIDValues to the logfile. Opens the file for appending, adds the time then each OID value as returned from 'read'

        Parameters
        ----------
        ID1 : TYPE String
            DESCRIPTION. Location Name. Required to open the correct file
        ID2 : TYPE
            DESCRIPTION.
        OIDTEXT : TYPE String
            DESCRIPTION. The name of the parameter. Used for the coloumn heading
        OIDValue : TYPE List
            DESCRIPTION. The returned values from the IOD get query
        NUMOID : TYPE int
            DESCRIPTION. The number of OID vales to be logged.
        BUtime : TYPE string
            DESCRIPTION.Time. Needed to open the correct log.

        Returns
        -------
        None.

        '''
        with open(os.path.normpath(Log_Location+"Monitor_Log-" + self.ID1 + "-" + self.ID2 + "-" + self.BUtime + ".csv"), mode='a', encoding='utf8', newline='\r\n') as f:
            f.write(time.strftime("%Y.%m.%d-%H.%M.%S"))
            for r in range(self.NUMOID):
                f.write("," + self.OIDValue[r])
            f.write("\n")
            f.close()

    def read(self):
        """
         Has to add a line of data containing a reading from all the OIDS in the OID list and

        Parameters
        ----------
        ID1 : TYPE
            DESCRIPTION.From the first coloumn of the csv file ( like NHT)
        ID2 : TYPE
            DESCRIPTION.From the second coloumn of the csv file. (like NVR2A)
        READCOMMUNITY : TYPE
            DESCRIPTION.
        SNMPV : TYPE
            DESCRIPTION. SNMP version number (like 1)
        IP : TYPE
            DESCRIPTION.
        NUMOID : TYPE Int
            DESCRIPTION.The number of OIDS in the csv file in the line.

        OIDTEXT : TYPE List
            DESCRIPTION. The name to be used for the column in the output file
        OID : TYPE List
            DESCRIPTION.The OID to get the value of. Taken as a pair with the OIDTEXT
            above form the output data coloumn values

        Returns
        -------
        OIDValue : TYPE List
            DESCRIPTION. The values returned in a list with positioal match with OID

        """
        self.SNMPV = int(self.SNMPV)
        self.OIDValue = []  # initiate the list
        self.textEdit_results.cut()
        self.textEdit_results.append("Fetching " + self.ID1 + " - " + self.ID2)
        for r in range(self.NUMOID):
            if r != 0:
                self.textEdit_results.undo()
            else:
                pass

            self.textEdit_results.append("OID" + str(r+1) + "of" + str(self.NUMOID))
            try:
                session = SNMP(self.IP, community=self.READCOMMUNITY, version=self.SNMPV, timeout=2, retries=3)
                v = self.OID[r]
                self.OIDV = (str(session.get(v)))
                self.changecommas()  # any commas are converted here
                self.OIDValue.append(self.checkedtext)
            except Exception as e:
                if r == 0:  # this section stops it trying to get any oids after the first one if it fails to get an answer. Saves a lot of time.
                    for r in range(self.NUMOID):
                        self.OIDValue.append("----")

                    self.textEdit_results.append("Failed.  " + str(e))
                    return
                else:
                    self.OIDValue.append("----")

    def changecommas(self):
        '''
        Remove commas which would otherwise interfere with the csv file formating.

        Any commas are converted to ` characters.

        Parameters
        ----------
        OIDV : TYPE probably a string
            DESCRIPTION.

        Returns
        -------
        checkedtext : TYPE string
            DESCRIPTION. The value which came in but with commas converted to `

        '''
        self.OIDV = str(self.OIDV)
        self.OIDV = list(self.OIDV)
        for r in range(len(self.OIDV)):
            if self.OIDV[r] == ',':
                self.OIDV[r] = '`'
        self.checkedtext = ''.join(self.OIDV)
        return self.checkedtext

    def timedelay(self):
        '''
        Specify the Number of seconds between readings.
        Allows the value to be presented in secs mins or hours
        Returns
        -------
        None.

        '''
        try:
            if self.radio_Hour.isChecked() is True:
                self.delaysecs = int((float(self.lineEdit_Rtime.text())) * 3600)
            elif self.radio_Min.isChecked() is True:
                self.delaysecs = int((float(self.lineEdit_Rtime.text())) * 60)
            else:
                self.delaysecs = int(self.lineEdit_Rtime.text())
        except Exception as e:
            self.delaysecs = 1
            self.label_selection.setText("Error: " + str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
