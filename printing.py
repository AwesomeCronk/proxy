from dbgTool.logging import basicLogFile

logFile = None
def initLogFile(logFilePath):
    global logFile
    logFile = basicLogFile(logFilePath)
    
def clearLogFile():
    logFile.reset()

def pPrint(strIn, end = '\n'):
    strOut = colored('proxy: {}'.format(strIn), 'yellow') + end
    print(strOut)
    logFile.addEntry(strOut)
        
def cPrint(strIn, end = '\n'):
    strOut = colored('clientSide: {}'.format(strIn), 'green') + end
    print(strOut)
    logFile.addEntry(strOut)

def sPrint(strIn, end = '\n'):
    strOut = colored('serverSide: {}'.format(strIn), 'cyan') + end
    print(strOut)
    logFile.addEntry(strOut)

def ePrint(strIn, end = '\n'):
    strOut = colored('cleanup: {}'.format(strIn), 'red') + end
    print(strOut)
    logFile.addEntry(strOut)
