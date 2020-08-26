from dbgTools.logging import basicLogFile
from termcolor import colored

logFile = None
def initLogFile(logFilePath):
    global logFile
    logFile = basicLogFile(logFilePath)
    
def clearLogFile():
    logFile.reset()

def pPrint(strIn, end = '\n'):
    strOut = colored('proxy: {}'.format(strIn), 'yellow')
    print(strOut, end = end)
    logFile.addEntry(strOut + end)
        
def cPrint(strIn, end = '\n'):
    strOut = colored('clientSide: {}'.format(strIn), 'green')
    print(strOut, end = end)
    logFile.addEntry(strOut + end)

def sPrint(strIn, end = '\n'):
    strOut = colored('serverSide: {}'.format(strIn), 'cyan')
    print(strOut, end = end)
    logFile.addEntry(strOut + end)

def ePrint(strIn, end = '\n'):
    strOut = colored('cleanup: {}'.format(strIn), 'red')
    print(strOut, end = end)
    logFile.addEntry(strOut + end)
