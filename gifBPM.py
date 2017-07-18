import os
import sys
import sqlite3
import subprocess
import thread
import requests
import urlparse
from StringIO import StringIO
from time import time
from PIL import Image

def getChar():
   from sys import stdin
   import tty
   import termios
   fd = stdin.fileno()
   old_settings = termios.tcgetattr(fd)
   try:
      tty.setraw(stdin.fileno())
      ch = stdin.read(1)
   finally:
      termios.tcsetattr(fd,termios.TCSADRAIN, old_settings)
   return ch

def massAdd(path, connection, cursor):
   with open(path,'r') as fCollection:
      for filePaths in fCollection:
         filePaths = filePaths.rstrip()
         print(filePaths)
         processImage(filePaths,connection, cursor)


def processImage(path, connection, cursor):
   try:
      im = Image.open(path)
      fName = os.path.basename(path)
      fPath = os.path.dirname(path)
      if(fName == path):
         fPath = os.getcwd()
      isURL = False
   except IOError as err:
      try:
         response = requests.get(path)
         im = Image.open(StringIO(response.content))
         (myScheme, myNetloc, myPath, myParams, myQuery, myFrag) = urlparse.urlparse(path)
         fName = os.path.basename(myPath)
         fPath = myScheme+ "://" + myNetloc + os.path.dirname(myPath)
         isURL = True
      except IOError as err:
         print("error opening file")
         return

   count = 0
   gifLen = 0
   try:
      while True:
         try:
            frameLen = im.info['duration']
         except KeyError:
            frameLen = 0
         gifLen += frameLen
         count += 1
         im.seek(im.tell()+1)
   except EOFError:
      gifBPM = float(60000)/gifLen
      toInsert = (fPath, fName, gifLen, gifBPM,isURL)
      cursor.execute('INSERT INTO images (fPath, fName, gifLen, bpm, isURL) VALUES(?,?,?,?,?)', toInsert)
      connection.commit()
      print("gif successfully added")

def showDB(connection, cursor):
   isWin = (sys.platform == "win32")
   connection.commit()
   cursor.execute("SELECT image_ID, fPath, fName, gifLen, bpm, isURL FROM images")
   print("Database Contents")
   result = cursor.fetchall()
   for (image_ID, fPath, fName, gifLen, bpm, isURL) in result:
      if(isWin and not isURL):
         print("%d: %d %s\%s" % (image_ID, gifLen, fPath, fName))
      else:
         print("%d: %d %s/%s" % (image_ID, gifLen, fPath, fName))

def getFreq(Connection, cursor):
   isWin = (sys.platform == "win32")
   if(isWin):
      import msvcrt
   print("tap q to exit to main menu.")
   tapped = ' '

   curGap = 0.0
   gifGap = 0.0

   prevTime  = time()
   curTime   = time()

   while(True):
      prevTime = curTime
      if(isWin):
         tapped = msvcrt.getch()
      else:
         tapped = getChar()

      if tapped in ('q', 'Q'):
         break
      curTime = time()
      curGap = curTime - prevTime
#If the change in the gap between taps is more than a natural variance
#Then the bpm no longer matches up with the gif
      if(abs(curGap - gifGap) > 0.1):
         print("change in BPM")
         print('Gap change %.2f' % abs(curGap - gifGap))
         gifGap = curGap
         print('BPM is %.2f' % (float(60)/gifGap))
         print('Gap is %.2f' % gifGap)
         try:
#This SQL Query takes the lowest difference between the gif and the beat, but excludes gifs that are too short or long
            argSQL = (1000*gifGap,1000*gifGap,1000*gifGap,1000*gifGap,1000*gifGap,1000*gifGap)
            cursor.execute('SELECT fPath, fName, gifLen, isURL FROM images WHERE gifLen < 8*? AND gifLen*8 > ? ORDER BY (ABS(gifLen - ?)%((gifLen + ? - ABS(gifLen - ?))/2)), ABS(gifLen - ?);', argSQL)
            (r,a,b,isURL) = cursor.fetchone()
            if(isWin and not isURL):
               print("%s\%s %d" % (r,a,b))
               thread.start_new_thread(showMeTheGif, (r + '\\' + a,))
            else:
               print("%s/%s %d" % (r,a,b))
               thread.start_new_thread(showMeTheGif, (r + '/' + a,))
         except TypeError:
            print("No suitable gifs in database")

def showMeTheGif(imagePath):
   if(sys.platform == "win32"):
      subprocess.call(["explorer.exe ", "%s"%imagePath])
   else:
      subprocess.call(["sensible-browser", "%s"%imagePath])
   
def helpMe():
   print("Options:")
   print("G: Add a gif")
   print("A: Add multiple gifs (specify a file containing gif pathnames)")
   print("T: Tap a beat and get a gif")
   print("P: Print the database")
   print("D: Delete an entry from the database")
   print("H: Help")
   print("Q: Quit the program")   

def main():
   isWin = (sys.platform == "win32")
   
   connection = sqlite3.connect("images.db")
   cursor = connection.cursor()

   sqlCommand = """
   CREATE TABLE IF NOT EXISTS images (
   Image_ID INTEGER PRIMARY KEY,
   fPath VARCHAR(256),
   fName VARCHAR(256),
   gifLen INTEGER,
   bpm REAL,
   isURL BOOLEAN);"""

   cursor.execute(sqlCommand)
   connection.commit()

   while True:
      option = raw_input("press g to add gif.\npress t to tap tempo.\npress q to quit.\n")
      if option in ('a', 'A'):
         myPath = raw_input("enter path of file containing filepaths\n")
         print("Opening %s" % (myPath))
         massAdd(myPath, connection, cursor)
      elif option in ('d', 'D'):
         selector = raw_input("Enter id number of entry you wish to delete. Enter ALL to clear database\n")
         if (selector == "ALL"):
            optionCheck = raw_input("This will clear database. Are you sure?(Y/N)\n")
            if(optionCheck in ('y', 'Y', "Yes", "yes", "YES")):
               cursor.execute("""DELETE FROM images;""")
               connection.commit()
               print("Database cleared.")
         else:
            toDelete = (selector,)
            try:
               cursor.execute('SELECT Image_ID, fPath, fName, isURL FROM images WHERE Image_ID = ?;', toDelete)
               (image_ID, fPath, fName, isURL) = cursor.fetchone()
               print("Are you sure you want to delete the following entry?")
               if(isWin and not isURL):
                  print("%d: %s\%s" % (image_ID, fPath, fName))
               else:
                  print("%d: %s/%s %d" % (image_ID, fPath, fName))                       
               optionCheck = raw_input()
               if(optionCheck in ('y', 'Y', "Yes", "yes", "YES")):
                  cursor.execute('DELETE FROM images WHERE Image_ID = ?;', toDelete)
                  connection.commit()
                  print("entry deleted")
            except TypeError:
               print("could not find entry %s" % selector)
      elif option in ('g', 'G'):
         myPath = raw_input("enter path of file\n")
         print("Opening %s" % (myPath))
         processImage(myPath, connection, cursor)
      elif option in ('h', 'H'):
         helpMe()
      elif option in ('p', 'P'):
         showDB(connection, cursor)
      elif option in ('q', 'Q'):
         connection.commit()
         connection.close()
         print("goodbye")
         break
      elif option in ('t', 'T'):
         getFreq(connection,cursor)
      else:
         print("That is not a valid option")

if __name__ == "__main__":
   main()
