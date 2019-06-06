#
#
#
import os
import logging



"""
some misc filesystem utilities and snippets - no rocket science, just tired of googling them each time. 
"""

#
#
#
def sanePath(szabspath, verbose = False):
    """
    attempt to check whether path is representing a meaningful path,
    without automatic joining of current working directory,
    convert it to its no nonsense form
    and drive hardcore pythonians up against the wall
    knowing that this module will cause far more problems than it possibly could solve. Ha!
    """
    if not os.path.isabs(szabspath):
        if verbose: logging.warning("Non absolute path: %s", repr(szabspath))
        return None
    szabsrealpath = os.path.abspath(os.path.realpath(szabspath))
    if verbose: logging.debug("Valid path: %s - using: %s", repr(szabspath), repr(szabsrealpath))
    return szabsrealpath

#
#
#
def saneExistingPath(szabspath, verbose = False):
    """
    attempt to check whether path is a string representing a meaningful existing path,
    and convert it to its no nonsense form
    """
    szsanepath = sanePath(szabspath, verbose=verbose)
    if not szsanepath: 
        if verbose: logging.warning("Invalid absolute path: %s", repr(szabspath))
        return None
    if not os.path.exists(szsanepath):
        if verbose: logging.warning("Path not found: %s", repr(szabspath))
        return None
    if verbose: logging.debug("Valid existing path: %s - using: %s", repr(szabspath), repr(szsanepath))
    return szsanepath

#
#
#
def saneExistingDirectory(szabspath, verbose = False):
    """
    attempt to check whether path is a string representing a meaningful existing directory,
    and convert it to its no nonsense form
    """
    szsanepath = saneExistingPath(szabspath, verbose=verbose)
    if not szsanepath: 
        if verbose: logging.warning("Invalid absolute path: %s", repr(szabspath))
        return None
    if not os.path.isdir(szsanepath):
        if verbose: logging.warning("Non directory path %s", repr(szabspath))
        return None
    if verbose: logging.debug("Valid existing directory path: %s - using: %s", repr(szabspath), repr(szsanepath))
    return szsanepath

#
#
#
def saneExistingFile(szabspath, verbose = False):
    """
    attempt to check whether path is a string representing a meaningful existing file,
    and convert it to its no nonsense form
    """
    szsanepath = saneExistingPath(szabspath, verbose=verbose)
    if not szsanepath: 
        if verbose: logging.warning("Invalid absolute path: %s", repr(szabspath))
        return None
    if not os.path.isfile(szsanepath):
        if verbose: logging.warning("Non file path %s", repr(szabspath))
        return None
    if verbose: logging.debug("Valid existing file path: %s - using: %s", repr(szabspath), repr(szsanepath))
    return szsanepath

#
#
#
def saneFile(szabspath, bmayexist = False, verbose = False):
    """
    check whether path is a string representing a meaningful non-existing file,
    check whether the directory it should live in exists
    convert it to its no nonsense form
    """
    szsanepath = sanePath(szabspath, verbose=verbose)
    if not szsanepath: 
        if verbose: logging.warning("Invalid absolute path: %s", repr(szabspath))
        return None
    if os.path.isdir(szsanepath):
        if verbose: logging.warning("Existing directory path %s", repr(szabspath))
        return None
    if not bmayexist:
        if os.path.isfile(szsanepath):
            if verbose: logging.warning("Existing file path %s", repr(szabspath))
            return None

    szabsdirpath = os.path.dirname(szsanepath)
    if not os.path.isdir(szabsdirpath):
        if verbose: logging.warning("Non directory path %s", repr(szabspath))
        return None

    if verbose: logging.debug("Valid file path: %s - using: %s", repr(szabspath), repr(szsanepath))
    return szsanepath

#
#
#
def getDir(szabspath, bmayexist = True, verbose = False):
    """
    attempt to check whether path is representing a meaningful directory path,
    create it if needed and allowed (just the last subdirectory, not the full path)
    """
    szsanepath = sanePath(szabspath, verbose=verbose)
    if not szsanepath: 
        if verbose: logging.error("Invalid absolute path: %s", repr(szabspath))
        return None
    if not saneExistingPath(szsanepath, verbose=verbose):
        os.mkdir(szsanepath)
        szsanepath = saneExistingDirectory(szsanepath, verbose=verbose)
        if not szsanepath: 
            if verbose: logging.error("Could not create absolute path: %s", repr(szabspath))
            return None
        if verbose: logging.debug("Created directory absolute path: %s - using: %s", repr(szabspath), repr(szsanepath))
        return szsanepath
    if not bmayexist:
        if verbose: logging.error("Existing path %s", repr(szabspath))
        return None
    if not saneExistingDirectory(szsanepath, verbose=verbose):
        if verbose: logging.error("Non directory path %s", repr(szabspath))
        return None
    if verbose: logging.debug("Existing directory absolute path: %s - using: %s", repr(szabspath), repr(szsanepath))
    return szsanepath

#
#
#
def getDirPath(szabspath, bmayexist = True, verbose = False):
    """
    attempt to check whether path is representing a meaningful directory path,
    create it if needed and allowed, including missing parents
    """
    szsanepath = sanePath(szabspath, verbose=verbose)
    if not szsanepath: 
        if verbose: logging.error("Invalid absolute path: %s", repr(szabspath))
        return None
    if not saneExistingPath(szsanepath, verbose=verbose):
        os.makedirs(szsanepath)
        szsanepath = saneExistingDirectory(szsanepath, verbose=verbose)
        if not szsanepath: 
            if verbose: logging.error("Could not create absolute path: %s", repr(szabspath))
            return None
        if verbose: logging.debug("Created directory absolute path: %s - using: %s", repr(szabspath), repr(szsanepath))
        return szsanepath
    if not bmayexist:
        if verbose: logging.error("Existing path %s", repr(szabspath))
        return None
    if not saneExistingDirectory(szsanepath, verbose=verbose):
        if verbose: logging.error("Non directory path %s", repr(szabspath))
        return None
    if verbose: logging.debug("Existing directory absolute path: %s - using: %s", repr(szabspath), repr(szsanepath))
    return szsanepath

#
#
#
def directoryFromExistingFile(szabspath, verbose = False):
    """
    """
    szsanepath = saneExistingFile(szabspath, verbose=verbose)
    if not szsanepath:
        if verbose: logging.warning("Non file path %s", repr(szabspath))
        return None
    szabsdirpath = os.path.dirname(szsanepath)
    if verbose: logging.debug("Valid directory path from existing file: %s - using: %s", repr(szabspath), repr(szabsdirpath))
    return szabsdirpath

#
#
#
def directoryFromFile(szabspath, verbose = False):
    """
    """
    szsanepath = saneFile(szabspath, bmayexist=True, verbose=verbose)
    if not szsanepath:
        if verbose: logging.warning("Non file path %s", repr(szabspath))
        return None
    szabsdirpath = os.path.dirname(szsanepath)
    if verbose: logging.debug("Valid directory path from file: %s - using: %s", repr(szabspath), repr(szabsdirpath))
    return szabsdirpath

#
#
#
def parentFromExistingDirectory(szabspath, verbose = False):
    """
    """
    szsanepath = saneExistingDirectory(szabspath, verbose=verbose)
    if not szsanepath:
        if verbose: logging.warning("Non directory path %s", repr(szabspath))
        return None
    szsanepath = saneExistingDirectory(os.path.dirname(szabspath), verbose=verbose)
    if not szsanepath:
        if verbose: logging.warning("Directory path %s has no parent", repr(szabspath))
        return None
    if verbose: logging.debug("Directory parent path from existing directory: %s - using: %s", repr(szabspath), repr(szsanepath))
    return szsanepath

# 
#
#
def gFilesInDir(szabsdir, verbose = False):
    """
    generator yielding the files in a directory
    """
    szsanedirpath = saneExistingDirectory(szabsdir, verbose=verbose)
    if not szsanedirpath:
        if verbose: logging.warning("Invalid absolute directory: %s", repr(szabsdir))
        return
    listofitemsindir = os.listdir(szsanedirpath)
    for stringitem in listofitemsindir:
        saneexistingpath = saneExistingPath(os.path.join(szsanedirpath, stringitem), verbose=verbose)
        if saneexistingpath:
            if os.path.isfile(saneexistingpath):
                if verbose: logging.debug("Using file: %s", repr(saneexistingpath))
                yield saneexistingpath
            else:
                if verbose: logging.debug("Ignoring non-file path: %s", repr(saneexistingpath))

# 
#
#
def gfFilesInDir(predicate, szabsdir, verbose = False):
    """
    generator yielding the files, for which the predicate is True, from a directory
    """
    for szfilepath in filter(predicate, gFilesInDir(szabsdir, verbose=verbose)):
        if verbose: logging.debug("Using file: %s", repr(szfilepath))
        yield szfilepath

#
#
#
def ggFilesInDirs(itrszabsdirs, verbose = False):
    """
    generator yielding the files from a directories iterable. beware: nothing prevents lstszabsdirs to contain duplicates.
    """
    if not itrszabsdirs:
        if verbose: logging.warning("Invalid directories iterable: %s", repr(itrszabsdirs))
        return
    for szabsdir in itrszabsdirs:
        for szfilepath in gFilesInDir(szabsdir, verbose=verbose):
            if verbose: logging.debug("Using file: %s", repr(szfilepath))
            yield szfilepath

# 
#
#
def ggfFilesInDirs(predicate, itrszabsdirs, verbose = False):
    """
    generator yielding the files, for which the predicate is True, from a directories iterable
    """
    for szfilepath in filter(predicate, ggFilesInDirs(itrszabsdirs, verbose=verbose)):
        if verbose: logging.debug("Using file: %s", repr(szfilepath))
        yield szfilepath

# 
#
#
def gDirsInDir(szabsdir, verbose = False):
    """
    generator yielding the subdirectories in a directory
    """
    szsanedirpath = saneExistingDirectory(szabsdir, verbose=verbose)
    if not szsanedirpath:
        if verbose: logging.warning("Invalid absolute directory: %s", repr(szabsdir))
        return
    listofitemsindir = os.listdir(szsanedirpath)
    for stringitem in listofitemsindir:
        saneexistingpath = saneExistingPath(os.path.join(szsanedirpath, stringitem), verbose=verbose)
        if saneexistingpath:
            if os.path.isdir(saneexistingpath):
                if verbose: logging.debug("Using directory: %s", repr(saneexistingpath))
                yield saneexistingpath
            else:
                if verbose: logging.debug("Ignoring non-directory path: %s", repr(saneexistingpath))

#
#
#
def gfDirsInDir(predicate, szabsdir, verbose = False):
    """
    generator yielding the subdirectories, for which the predicate is True, from a directory
    """
    for szdirpath in filter(predicate, gDirsInDir(szabsdir, verbose=verbose)):
        if verbose: logging.debug("Using directory: %s", repr(szdirpath))
        yield szdirpath

#
#
#
def ggDirsInDirs(itrszabsdirs, verbose = False):
    """
    generator yielding the subdirectories from a directories iterable
    """
    if not itrszabsdirs:
        if verbose: logging.warning("Invalid directories iterable: %s", repr(itrszabsdirs))
        return
    for szabsdir in itrszabsdirs:
        for szdirpath in gDirsInDir(szabsdir, verbose=verbose):
            if verbose: logging.debug("Using directory: %s", repr(szdirpath))
            yield szdirpath

# 
#
#
def ggfDirsInDirs(predicate, itrszabsdirs, verbose = False):
    """
    generator yielding the subdirectories, for which the predicate is True, from a directories iterable
    """
    for szdirpath in filter(predicate, ggDirsInDirs(itrszabsdirs, verbose)):
        if verbose: logging.debug("Using directory: %s", repr(szdirpath))
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
        logging.warning("Invalid abs directory: %s", repr(szabsdir))
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
            logging.warning("Directory: %s contains alien entry: %s", repr(szabsdir), repr(saneexistingpath))
            return

