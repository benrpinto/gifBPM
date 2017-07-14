import os
import tty
import termios
import sqlite3
import subprocess
import thread
import requests
import urlparse
from StringIO import StringIO
from time import time
from PIL import Image
from sys import stdin

def getchar():
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
   except IOError as err:
      try:
         response = requests.get(path)
         im = Image.open(StringIO(response.content))
         (myScheme, myNetloc, myPath, myParams, myQuery, myFrag) = urlparse.urlparse(path)
         fName = os.path.basename(myPath)
         fPath = myScheme+ "://" + myNetloc + os.path.dirname(myPath)
      except IOError as err:
         print("error opening file")
         return

   count = 0
   gifLen = 0
   try:
      while True:
         #im.show()
         try:
            frameLen = im.info['duration']
         except KeyError:
            frameLen = 0
         gifLen += frameLen
         #print "frame %d is length %d. total length is %d" % (count, frameLen, gifLen)
         count += 1
         im.seek(im.tell()+1)
   except EOFError:

#      print("total gif length is %d." % (gifLen))
      gifBPM = float(60000)/gifLen
#      print("would suit a bpm of %.2f." % (gifBPM))
      print("----")
      print(fPath)
      print(fName)
      print(gifLen)
      print(gifBPM)
      print("----")
      toInsert = (fPath, fName, gifLen, gifBPM)
      cursor.execute('INSERT INTO images (fPath, fName, gifLen, bpm) VALUES(?,?,?,?)', toInsert)
      connection.commit()

def showDB(connection, cursor):
   connection.commit()
   cursor.execute("SELECT * FROM images")
   print("Database Contents")
   result = cursor.fetchall()
   for r in result:
      print(r)

def getFreq(Connection, cursor):
   print("tap q to exit to main menu.")
   tapped = ' '

   curGap = 0.0
   gifGap = 0.0

   prevTime  = time()
   curTime   = time()

   while(True):
      prevTime = curTime
      tapped = getchar()
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
#This SQL Query takes the lowest difference between the gif and the beat, but only returns values where the difference is less than 0.1 seconds
#            cursor.execute('SELECT fPath, fName FROM images WHERE ABS(gifLen - ?) < 100 ORDER BY ABS(gifLen - ?);', (1000*gifGap,1000*gifGap))
#This SQL Query takes the lowest difference between the gif and the beat, with the modulo (acknowledging gifs and beats repeating)
#            cursor.execute('SELECT fPath, fName, gifLen FROM images ORDER BY (ABS(gifLen - ?)%((gifLen + ? - ABS(gifLen - ?))/2)), ABS(gifLen - ?);', (1000*gifGap,1000*gifGap,1000*gifGap,1000*gifGap))
#This SQL Query takes the lowest difference between the gif and the beat, but penalises gifs by how proportionally smaller or larger they are than the beat
#            argSQL = (1000*gifGap,1000*gifGap,1000*gifGap,1000*gifGap,1000*gifGap)
#            cursor.execute('SELECT fPath, fName, gifLen FROM images ORDER BY (ABS(gifLen - ?)%((gifLen + ? - ABS(gifLen - ?))/2)) + (ABS(gifLen - ?)/gifLen), ABS(gifLen - ?);', argSQL)
#This SQL Query takes the lowest difference between the gif and the beat, but excludes gifs that are too short
            argSQL = (1000*gifGap,1000*gifGap,1000*gifGap,1000*gifGap,1000*gifGap,1000*gifGap)
            cursor.execute('SELECT fPath, fName, gifLen FROM images WHERE gifLen < 8*? AND gifLen*8 > ? ORDER BY (ABS(gifLen - ?)%((gifLen + ? - ABS(gifLen - ?))/2)), ABS(gifLen - ?);', argSQL)
            (r,a,b) = cursor.fetchone()
            print("%s/%s %d" % (r,a,b))
            thread.start_new_thread(showMeTheGif, (r + '/' + a,))
         except TypeError:
            print("No suitable gifs in database")
         
# works in Linux, but probably not in windows
def showMeTheGif(imagePath):
   subprocess.call(["sensible-browser", "%s"%imagePath])
   

def main():
   connection = sqlite3.connect("images.db")
   cursor = connection.cursor()
   sqlCommand = """
   CREATE TABLE IF NOT EXISTS images (
   Image_ID INTEGER PRIMARY KEY,
   fPath VARCHAR(256),
   fName VARCHAR(256),
   gifLen INTEGER,
   bpm REAL);"""

   cursor.execute(sqlCommand)
   connection.commit()

   while True:
      option = raw_input("press g to add gif.\npress t to tap tempo.\npress q to quit.\n")
      if option in ('g', 'G'):
         myPath = raw_input("enter path of file\n")
         print("Opening %s" % (myPath))
         processImage(myPath, connection, cursor)
      elif option in ('a', 'A'):
         myPath = raw_input("enter path of file containing filepaths\n")
         print("Opening %s" % (myPath))
         massAdd(myPath, connection, cursor)
      elif option in ('t', 'T'):
         getFreq(connection,cursor)
      elif option in ('p', 'P'):
         showDB(connection, cursor)
      elif option in ('q', 'Q'):
         connection.commit()
         connection.close()
         print("goodbye")
         break
      elif option in ('d', 'D'):
         optionCheck = raw_input("This will clear database. Are you sure?(Y/N)\n")
         if(optionCheck in ('y', 'Y', "Yes", "yes", "YES")):
            cursor.execute("""DROP TABLE images;""")
            sqlCommand = """
            CREATE TABLE IF NOT EXISTS images (
            Image_ID INTEGER PRIMARY KEY,
            fPath VARCHAR(256),
            fName VARCHAR(256),
            gifLen INTEGER,
            bpm REAL);"""
            cursor.execute(sqlCommand)
            print("Database cleared.")
      else:
         print("That is not a valid option")

if __name__ == "__main__":
   main()
