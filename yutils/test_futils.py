#
#
#
import unittest
import logging
import os
import shutil
import tempfile
import yutils.futils

#
#
#
verbose = True
level   = logging.DEBUG #logging.ERROR #logging.DEBUG #logging.ERROR #

#
#
#
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        #
        #    root ---+--- somedir ---+--- somefile.txt
        #            |               +--- otherfile_20170101_someversion.txt
        #            |               +--- otherfile_...     _someversion.txt
        #            |               +--- otherfile_20171231_someversion.txt
        #            |               +--- (nonefile.txt)
        #            |
        #            +--- othrdir
        #            |
        #            +--- (nonedir)
        #
        #
        cls.sz_test_rootdir   = tempfile.mkdtemp()
        cls.sz_some_dir_name  = 'somedir'
        cls.sz_othr_dir_name  = 'othrdir'
        cls.sz_none_dir_name  = 'nonedir'
        cls.sz_some_file_name = 'somefile.txt'
        cls.sz_none_file_name = 'nonefile.txt'

        cls.sz_some_dir       = os.path.join(cls.sz_test_rootdir, cls.sz_some_dir_name)
        cls.sz_othr_dir       = os.path.join(cls.sz_test_rootdir, cls.sz_othr_dir_name)
        cls.sz_none_dir       = os.path.join(cls.sz_test_rootdir, cls.sz_none_dir_name)
        cls.sz_some_file      = os.path.join(cls.sz_some_dir, cls.sz_some_file_name)
        cls.sz_none_file      = os.path.join(cls.sz_some_dir, cls.sz_none_file_name)

        os.mkdir(cls.sz_some_dir) # existing root/somedir
        os.mkdir(cls.sz_othr_dir) # existing root/othrdir

        def makefile(szfile):
            f = open(szfile, 'w')
            f.write(szfile)
            f.write('\nThe owls are not what they seem')
            f.close()

        makefile(cls.sz_some_file) # existing file root/somedir/somefile.txt

        for szyyyymmdd in ['20170101', '20170102', '20170103', '20171231']:
            makefile(os.path.join(cls.sz_some_dir, 'otherfile_' + szyyyymmdd + '_someversion.txt'))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.sz_test_rootdir)
        pass

    #@unittest.case.skip
    def test_sanePath(self):
        #
        #    sanePath
        #
        self.assertIsNotNone(yutils.futils.sanePath(Test.sz_some_dir,  verbose=verbose)) # sane existing dir
        self.assertIsNotNone(yutils.futils.sanePath(Test.sz_none_dir,  verbose=verbose)) # sane non-existing dir
        self.assertIsNotNone(yutils.futils.sanePath(Test.sz_some_file, verbose=verbose)) # sane existing file
        self.assertIsNotNone(yutils.futils.sanePath(Test.sz_none_file, verbose=verbose)) # sane non-existing file
        #
        #    saneExistingPath
        #
        self.assertIsNotNone(yutils.futils.saneExistingPath(Test.sz_some_dir,  verbose=verbose))
        self.assertIsNotNone(yutils.futils.saneExistingPath(Test.sz_some_file, verbose=verbose))

        self.assertIsNone(yutils.futils.saneExistingPath(Test.sz_none_dir,  verbose=verbose))
        self.assertIsNone(yutils.futils.saneExistingPath(Test.sz_none_file, verbose=verbose))
        #
        #    saneExistingDirectory
        #
        self.assertIsNotNone(yutils.futils.saneExistingDirectory(Test.sz_some_dir, verbose=verbose))

        self.assertIsNone(yutils.futils.saneExistingDirectory(Test.sz_none_dir,  verbose=verbose))
        self.assertIsNone(yutils.futils.saneExistingDirectory(Test.sz_some_file, verbose=verbose))
        self.assertIsNone(yutils.futils.saneExistingDirectory(Test.sz_none_file, verbose=verbose))
        #
        #    saneExistingFile
        #
        self.assertIsNotNone(yutils.futils.saneExistingFile(Test.sz_some_file, verbose=verbose))

        self.assertIsNone(yutils.futils.saneExistingFile(Test.sz_some_dir,  verbose=verbose))
        self.assertIsNone(yutils.futils.saneExistingFile(Test.sz_none_dir,  verbose=verbose))
        self.assertIsNone(yutils.futils.saneExistingFile(Test.sz_none_file, verbose=verbose))
        #
        #    saneFile
        #
        self.assertIsNotNone(yutils.futils.saneFile(Test.sz_some_file, bmayexist=True, verbose=verbose))
        self.assertIsNone(yutils.futils.saneFile(Test.sz_some_file, bmayexist=False,   verbose=verbose))

        self.assertIsNone(yutils.futils.saneFile(Test.sz_some_dir, bmayexist=True,  verbose=verbose))
        self.assertIsNone(yutils.futils.saneFile(Test.sz_some_dir, bmayexist=False, verbose=verbose))

        self.assertIsNotNone(yutils.futils.saneFile(Test.sz_none_file, bmayexist=True,  verbose=verbose))
        self.assertIsNotNone(yutils.futils.saneFile(Test.sz_none_file, bmayexist=False, verbose=verbose))

        self.assertIsNotNone(yutils.futils.saneFile(Test.sz_none_dir, bmayexist=True, verbose=verbose))
        self.assertIsNotNone(yutils.futils.saneFile(Test.sz_none_dir, bmayexist=False, verbose=verbose))
        #
        #    directoryFromExistingFile
        #
        self.assertIsNotNone(yutils.futils.directoryFromExistingFile(Test.sz_some_file, verbose=verbose))

        self.assertIsNone(yutils.futils.directoryFromExistingFile(Test.sz_some_dir,  verbose=verbose))
        self.assertIsNone(yutils.futils.directoryFromExistingFile(Test.sz_none_dir,  verbose=verbose))
        self.assertIsNone(yutils.futils.directoryFromExistingFile(Test.sz_none_file, verbose=verbose))
        #
        #    directoryFromFile
        #
        self.assertIsNotNone(yutils.futils.directoryFromFile(Test.sz_some_file, verbose=verbose))
        self.assertIsNotNone(yutils.futils.directoryFromFile(Test.sz_none_file, verbose=verbose))
        self.assertIsNotNone(yutils.futils.directoryFromFile(Test.sz_none_dir,  verbose=verbose)) # non existent directory cannot be distinguished from non existent file

        self.assertIsNone(yutils.futils.directoryFromFile(Test.sz_some_dir,  verbose=verbose))
        #
        #    parentFromExistingDirectory
        #
        self.assertIsNotNone(yutils.futils.parentFromExistingDirectory(Test.sz_some_dir,  verbose=verbose))

        self.assertIsNone(yutils.futils.parentFromExistingDirectory(Test.sz_some_file, verbose=verbose))
        self.assertIsNone(yutils.futils.parentFromExistingDirectory(Test.sz_none_dir,  verbose=verbose))
        self.assertIsNone(yutils.futils.parentFromExistingDirectory(Test.sz_none_file, verbose=verbose))

    #@unittest.case.skip
    def test_getDir(self):
        #
        #    getDir
        #
        self.assertIsNotNone(yutils.futils.getDir(Test.sz_some_dir,  bmayexist = True,  verbose=verbose)) # sane existing dir
        self.assertIsNone   (yutils.futils.getDir(Test.sz_some_file, bmayexist = True,  verbose=verbose)) # sane existing file
        self.assertIsNone   (yutils.futils.getDir(Test.sz_some_dir,  bmayexist = False, verbose=verbose)) # sane existing dir
        self.assertIsNotNone(yutils.futils.getDir(Test.sz_none_dir,  bmayexist = True,  verbose=verbose)) # sane non-existing dir => directory gets created
        self.assertIsNone   (yutils.futils.getDir(Test.sz_none_dir,  bmayexist = False, verbose=verbose)) # sane existing dir
        shutil.rmtree(Test.sz_none_dir)

        self.assertIsNotNone(yutils.futils.getDirPath(Test.sz_some_dir,  bmayexist = True,  verbose=verbose)) # sane existing dir
        self.assertIsNone   (yutils.futils.getDirPath(Test.sz_some_file, bmayexist = True,  verbose=verbose)) # sane existing file
        self.assertIsNone   (yutils.futils.getDirPath(Test.sz_some_dir,  bmayexist = False, verbose=verbose)) # sane existing dir
        self.assertIsNotNone(yutils.futils.getDirPath(Test.sz_none_dir,  bmayexist = True,  verbose=verbose)) # sane non-existing dir => directory gets created
        self.assertIsNone   (yutils.futils.getDirPath(Test.sz_none_dir,  bmayexist = False, verbose=verbose)) # sane existing dir
        shutil.rmtree(Test.sz_none_dir)

    #@unittest.case.skip
    def test_gFilesInDir(self):
        #
        #    gFilesInDir
        #
        self.assertCountEqual( [os.path.basename(p) for p in yutils.futils.gFilesInDir(Test.sz_some_dir,     verbose=verbose)], os.listdir(Test.sz_some_dir))
        self.assertCountEqual( [os.path.basename(p) for p in yutils.futils.gFilesInDir(Test.sz_none_dir,     verbose=verbose)], [])
        self.assertCountEqual( [os.path.basename(p) for p in yutils.futils.gFilesInDir(Test.sz_some_file,    verbose=verbose)], [])
        self.assertCountEqual( [os.path.basename(p) for p in yutils.futils.gFilesInDir(Test.sz_none_file,    verbose=verbose)], [])
        self.assertCountEqual( [os.path.basename(p) for p in yutils.futils.gFilesInDir(Test.sz_test_rootdir, verbose=verbose)], []) # root contains directories, no files
        #
        #    gfFilesInDir
        #
        self.assertCountEqual( list(yutils.futils.gfFilesInDir(None,           Test.sz_some_dir, verbose=verbose)), list(yutils.futils.gFilesInDir(Test.sz_some_dir, verbose=verbose)))
        self.assertCountEqual( list(yutils.futils.gfFilesInDir(lambda _:True,  Test.sz_some_dir, verbose=verbose)), list(yutils.futils.gFilesInDir(Test.sz_some_dir, verbose=verbose)))
        self.assertCountEqual( list(yutils.futils.gfFilesInDir(lambda _:False, Test.sz_some_dir, verbose=verbose)), [])
        #
        #    ggFilesInDirs - 'mylist = list(dict.fromkeys(mylist))' is used to remove duplicates
        #
        self.assertCountEqual( list(yutils.futils.ggFilesInDirs([Test.sz_some_dir],                                 verbose=verbose)),  list(yutils.futils.gFilesInDir(Test.sz_some_dir, verbose=verbose)))
        self.assertCountEqual( list(dict.fromkeys(yutils.futils.ggFilesInDirs([Test.sz_some_dir, Test.sz_some_dir], verbose=verbose))), list(yutils.futils.gFilesInDir(Test.sz_some_dir, verbose=verbose)))
        #
        #    ggfFilesInDirs - 'mylist = list(dict.fromkeys(mylist))' is used to remove duplicates
        #
        self.assertCountEqual( list(yutils.futils.ggfFilesInDirs(lambda _:True,                [Test.sz_some_dir],                   verbose=verbose)),  list(yutils.futils.gFilesInDir(Test.sz_some_dir, verbose=verbose)))
        self.assertCountEqual( list(dict.fromkeys(yutils.futils.ggfFilesInDirs(lambda _:True,  [Test.sz_some_dir, Test.sz_some_dir], verbose=verbose))), list(yutils.futils.gFilesInDir(Test.sz_some_dir, verbose=verbose)))
        self.assertCountEqual( list(dict.fromkeys(yutils.futils.ggfFilesInDirs(lambda _:False, [Test.sz_some_dir, Test.sz_some_dir], verbose=verbose))), [])

    #@unittest.case.skip
    def test_gDirsInDir(self):
        #
        #    gDirsInDir
        #
        self.assertCountEqual( [os.path.basename(p) for p in yutils.futils.gDirsInDir(Test.sz_test_rootdir,     verbose=verbose)], os.listdir(Test.sz_test_rootdir))
        self.assertCountEqual( [os.path.basename(p) for p in yutils.futils.gDirsInDir(Test.sz_some_dir,         verbose=verbose)], [])
        #
        #    gfDirsInDir
        #
        self.assertCountEqual( list(yutils.futils.gfDirsInDir(None,           Test.sz_test_rootdir, verbose=verbose)), list(yutils.futils.gDirsInDir(Test.sz_test_rootdir, verbose=verbose)))
        self.assertCountEqual( list(yutils.futils.gfDirsInDir(lambda _:True,  Test.sz_test_rootdir, verbose=verbose)), list(yutils.futils.gDirsInDir(Test.sz_test_rootdir, verbose=verbose)))
        self.assertCountEqual( list(yutils.futils.gfDirsInDir(lambda _:False, Test.sz_test_rootdir, verbose=verbose)), [])
        #
        #    ggDirsInDirs
        #
        self.assertCountEqual( [os.path.basename(p) for p in yutils.futils.ggDirsInDirs([Test.sz_test_rootdir],     verbose=verbose)], os.listdir(Test.sz_test_rootdir))
        self.assertCountEqual( [os.path.basename(p) for p in yutils.futils.ggDirsInDirs([Test.sz_some_dir],         verbose=verbose)], [])
        #
        #    ggfDirsInDirs
        #
        self.assertCountEqual( list(yutils.futils.ggfDirsInDirs(None,           [Test.sz_test_rootdir], verbose=verbose)), list(yutils.futils.gDirsInDir(Test.sz_test_rootdir, verbose=verbose)))
        self.assertCountEqual( list(yutils.futils.ggfDirsInDirs(lambda _:True,  [Test.sz_test_rootdir], verbose=verbose)), list(yutils.futils.gDirsInDir(Test.sz_test_rootdir, verbose=verbose)))
        self.assertCountEqual( list(yutils.futils.ggfDirsInDirs(lambda _:False, [Test.sz_test_rootdir], verbose=verbose)), [])

#
#
#
if __name__ == "__main__":
    #
    #
    #
    logging.basicConfig(level=level, format='%(asctime)s %(levelname).3s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
