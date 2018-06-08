#
#
#
import os
import logging
import itertools



#
#
#
def sanePath(szabspath):
    """
    attempt to check whether path is a string representing a meaningful path,
    without automatic joining of current working directory,
    convert it to its no nonsense form
    and drive hardcore pythonians up against the wall
    """
    if not isinstance(szabspath, basestring): 
        logging.warn("Invalid type or None string: %s has type:%s", repr(szabspath), type(szabspath))
        return None
    if not os.path.isabs(szabspath):
        logging.warn("Non absolute path: %s", repr(szabspath))
        return None
    szabsrealpath = os.path.abspath(os.path.realpath(szabspath))
    logging.debug("Valid path: %s - using: %s", repr(szabspath), repr(szabsrealpath))
    return szabsrealpath

#
#
#
def saneExistingPath(szabspath):
    """
    attempt to check whether path is a string representing a meaningful existing path,
    and convert it to its no nonsense form
    """
    szsanepath = sanePath(szabspath)
    if not szsanepath: 
        logging.warn("Invalid absolute path: %s", repr(szabspath))
        return None
    if not os.path.exists(szsanepath):
        logging.warn("Path not found: %s", repr(szabspath))
        return None
    logging.debug("Valid existing path: %s - using: %s", repr(szabspath), repr(szsanepath))
    return szsanepath

#
#
#
def saneExistingDirectory(szabspath):
    """
    attempt to check whether path is a string representing a meaningful existing directory,
    and convert it to its no nonsense form
    """
    szsanepath = saneExistingPath(szabspath)
    if not szsanepath: 
        logging.warn("Invalid absolute path: %s", repr(szabspath))
        return None
    if not os.path.isdir(szsanepath):
        logging.warn("Non directory path %s", repr(szabspath))
        return None
    logging.debug("Valid existing directory path: %s - using: %s", repr(szabspath), repr(szsanepath))
    return szsanepath

#
#
#
def saneExistingFile(szabspath):
    """
    attempt to check whether path is a string representing a meaningful existing file,
    and convert it to its no nonsense form
    """
    szsanepath = saneExistingPath(szabspath)
    if not szsanepath: 
        logging.warn("Invalid absolute path: %s", repr(szabspath))
        return None
    if not os.path.isfile(szsanepath):
        logging.warn("Non file path %s", repr(szabspath))
        return None
    logging.debug("Valid existing file path: %s - using: %s", repr(szabspath), repr(szsanepath))
    return szsanepath

#
#
#
def saneFile(szabspath, bmayexist = False):
    """
    check whether path is a string representing a meaningful non-existing file,
    check whether the directory it should live in exists
    convert it to its no nonsense form
    """
    szsanepath = sanePath(szabspath)
    if not szsanepath: 
        logging.warn("Invalid absolute path: %s", repr(szabspath))
        return None
    if os.path.isdir(szsanepath):
        logging.warn("Existing directory path %s", repr(szabspath))
        return None
    if not bmayexist:
        if os.path.isfile(szsanepath):
            logging.warn("Existing file path %s", repr(szabspath))
            return None
    
    szabsdirpath = os.path.dirname(szsanepath)
    if not os.path.isdir(szabsdirpath):
        logging.warn("Non directory path %s", repr(szabspath))
        return None
    
    logging.debug("Valid file path: %s - using: %s", repr(szabspath), repr(szsanepath))
    return szsanepath

#
#
#
def directoryFromExistingFile(szabspath):
    """
    """
    szsanepath = saneExistingFile(szabspath)
    if not szsanepath:
        logging.warn("Non file path %s", repr(szabspath))
        return None
    szabsdirpath = os.path.dirname(szsanepath)
    return szabsdirpath

#
#
#
def directoryFromFile(szabspath):
    """
    """
    szsanepath = saneFile(szabspath, True)
    if not szsanepath:
        logging.warn("Non file path %s", repr(szabspath))
        return None
    szabsdirpath = os.path.dirname(szsanepath)
    return szabsdirpath

#
#
#
def parentFromExistingDirectory(szabspath):
    """
    """
    szsanepath = saneExistingDirectory(szabspath)
    if not szsanepath:
        logging.warn("Non directory path %s", repr(szabspath))
        return None
    szsanepath = saneExistingDirectory(os.path.dirname(szabspath))
    if not szsanepath:
        logging.warn("Directory path %s has no parent", repr(szabspath))
        return None
    return szsanepath

# 
#
#
def gFilesInDir(szabsdir):
    """
    generator yielding the files in a directory
    """
    szsanedirpath = saneExistingDirectory(szabsdir)
    if not szsanedirpath:
        logging.warn("Invalid absolute directory: %s", repr(szabsdir))
        return
    listofitemsindir = os.listdir(szsanedirpath)
    for stringitem in listofitemsindir:
        saneexistingpath = saneExistingPath(os.path.join(szsanedirpath, stringitem))
        if saneexistingpath:
            if os.path.isfile(saneexistingpath):
                logging.debug("Using file: %s", repr(saneexistingpath))
                yield saneexistingpath
            else:
                logging.debug("Ignoring non-file path: %s", repr(saneexistingpath))

# 
#
#
def gfFilesInDir(predicate, szabsdir):
    """
    generator yielding the files, for which the predicate is True, from a directory
    """
    for szfilepath in itertools.ifilter(predicate, gFilesInDir(szabsdir)):
        logging.debug("Using file: %s", repr(szfilepath))
        yield szfilepath

#
#
#
def ggFilesInDirs(iszabsdirs):
    """
    generator yielding the files from a directories iterable
    """
    if not iszabsdirs:
        logging.warn("Invalid directories iterable: %s", repr(iszabsdirs))
        return
    for iszabsdir in iszabsdirs:
        for szfilepath in gFilesInDir(iszabsdir):
            logging.debug("Using file: %s", repr(szfilepath))
            yield szfilepath

# 
#
#
def ggfFilesInDirs(predicate, iszabsdirs):
    """
    generator yielding the files, for which the predicate is True, from a directories iterable
    """
    for szfilepath in itertools.ifilter(predicate, ggFilesInDirs(iszabsdirs)):
        logging.debug("Using file: %s", repr(szfilepath))
        yield szfilepath

# 
#
#
def gDirsInDir(szabsdir):
    """
    generator yielding the subdirectories in a directory
    """
    szsanedirpath = saneExistingDirectory(szabsdir)
    if not szsanedirpath:
        logging.warn("Invalid absolute directory: %s", repr(szabsdir))
        return
    listofitemsindir = os.listdir(szsanedirpath)
    for stringitem in listofitemsindir:
        saneexistingpath = saneExistingPath(os.path.join(szsanedirpath, stringitem))
        if saneexistingpath:
            if os.path.isdir(saneexistingpath):
                logging.debug("Using directory: %s", repr(saneexistingpath))
                yield saneexistingpath
            else:
                logging.debug("Ignoring non-directory path: %s", repr(saneexistingpath))
                

# 
#
#
def gfDirsInDir(predicate, szabsdir):
    """
    generator yielding the subdirectories, for which the predicate is True, from a directory
    """
    for szdirpath in itertools.ifilter(predicate, gDirsInDir(szabsdir)):
        logging.debug("Using directory: %s", repr(szdirpath))
        yield szdirpath

#
#
#
def ggDirsInDirs(iszabsdirs):
    """
    generator yielding the subdirectories from a directories iterable
    """
    if not iszabsdirs:
        logging.warn("Invalid directories iterable: %s", repr(iszabsdirs))
        return
    for iszabsdirs in iszabsdirs:
        for szdirpath in gDirsInDir(iszabsdirs):
            logging.debug("Using directory: %s", repr(szdirpath))
            yield szdirpath

# 
#
#
def ggfDirsInDirs(predicate, iszabsdirs):
    """
    generator yielding the subdirectories, for which the predicate is True, from a directories iterable
    """
    for szdirpath in itertools.ifilter(predicate, ggDirsInDirs(iszabsdirs)):
        logging.debug("Using directory: %s", repr(szdirpath))
        yield szdirpath

# 
#
#
def gFilesInDirTree(szabsdir):
    """
    generator yielding the files in a directory tree 
    """
    szsanedirpath = saneExistingDirectory(szabsdir)
    if not szsanedirpath:
        logging.warn("Invalid abs directory: %s", repr(szabsdir))
        return
    listofitemsindir = os.listdir(szsanedirpath)
    for stringitem in listofitemsindir:
        saneexistingpath = saneExistingPath(os.path.join(szsanedirpath, stringitem))
        if os.path.isfile(saneexistingpath):
            yield saneexistingpath
        elif os.path.isdir(saneexistingpath):
            for item in gFilesInDirTree(saneexistingpath):
                yield item
        else:
            logging.warn("Directory: %s contains alien entry: %s", repr(szabsdir), repr(saneexistingpath))
            return

