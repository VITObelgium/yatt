#
#
#
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
#
#
#
import re
import numpy
import osgeo.gdal
import matplotlib.pyplot
import yatt.smooth
import yutils.dutils
import demo.testdata


#
#    WeightIntevals
#    construct with a default WeightValues object
#    add intervals (start_mmdd, end_mmdd) with specific WeightValues objects
#    then makeweightvaluesfunction will yield a function, 
#        this function can be called with a yyyymmdd parameter
#        and will return the WeightValues object applicable for that yyyymmdd 
#
class WeightIntevals(object):
    """
    """
    _fakeyear = 2000 # should be leap 

    #
    #
    #
    def __init__(self, defaultWeightValues):
        """
        """
        if not isinstance(defaultWeightValues, yatt.smooth.WeightValues): raise ValueError(" defaultWeightValues must be an actual WeightValues instance")
        self._defaultweightvalues     = defaultWeightValues.copy()
        self._intervalstartdates      = []
        self._intervalenddates        = []
        self._intervalweightvalues    = []

    #
    #
    #
    def addWeightValuesInterval(self, startmmdd, endmmdd, weightValues):
        """
        """
        if not isinstance(weightValues, yatt.smooth.WeightValues): raise ValueError(" weightValues must be an actual WeightValues instance")
        fake_start_date = yutils.dutils.fake_date_of_mmdd(startmmdd, WeightIntevals._fakeyear)
        fake_end_date   = yutils.dutils.fake_date_of_mmdd(endmmdd,   WeightIntevals._fakeyear)
        if fake_end_date <= fake_start_date: raise ValueError(" half open interval [startmmdd, endmmdd) must contain at least one day")
        #
        #
        #
        for iIdx in range(len(self._intervalweightvalues)):
            if self._intervalstartdates[iIdx] <= fake_start_date and fake_start_date < self._intervalenddates[iIdx] :
                raise ValueError(" startmmdd (%s) overlaps with existing interval [%s - %s)"  % (startmmdd, yutils.dutils.mmdd_from_datetimedate(self._intervalstartdates[iIdx]), yutils.dutils.mmdd_from_datetimedate(self._intervalenddates[iIdx])))
            if self._intervalstartdates[iIdx] < fake_end_date and fake_end_date < self._intervalenddates[iIdx] :
                raise ValueError(" endmmdd (%s) overlaps with existing interval [%s - %s)"  % (endmmdd, yutils.dutils.mmdd_from_datetimedate(self._intervalstartdates[iIdx]), yutils.dutils.mmdd_from_datetimedate(self._intervalenddates[iIdx])))
        #
        #
        #
        self._intervalstartdates.append(fake_start_date)
        self._intervalenddates.append(fake_end_date)
        self._intervalweightvalues.append(weightValues.copy())

    #
    #
    #
    def makeweightvaluesfunction(self):
        """
        """
        #
        # using copies just in case the WeightsSet is changed after the function has been handed out
        #
        defaultweightvalues  = self._defaultweightvalues.copy()
        intervalweightvalues = []
        for iIdx in range(len(self._intervalweightvalues)):
            intervalweightvalues.append(self._intervalweightvalues[iIdx].copy())
        #
        #
        #
        mmddweightvaluesdict = dict()    
        yyyy = str(yutils.dutils.iyyyy_from_yyyy(self._fakeyear))
        for yyyymmdd in yutils.dutils.g_yyyymmdd_interval(yyyy+"0101", yyyy+"1231"):
            mmdd = yyyymmdd[4:]
            fake_date = yutils.dutils.fake_date_of_mmdd(mmdd)
            for iIdx in range(len(intervalweightvalues)):
                if self._intervalstartdates[iIdx] <= fake_date and fake_date < self._intervalenddates[iIdx] :
                    mmddweightvaluesdict[mmdd] = intervalweightvalues[iIdx]
                    break
            if not mmdd in mmddweightvaluesdict:
                mmddweightvaluesdict[mmdd] = defaultweightvalues

        #
        #
        #
        def _weightvaluesfunction(yyyymmdd):
            """
            """
#             for key in sorted(mmddweightvaluesdict):
#                 print (key, mmddweightvaluesdict[key]._weightsdict, mmddweightvaluesdict[key])

            _, imonth, iday = yutils.dutils.iyear_imonth_iday_from_yyyymmdd(yyyymmdd)
            return mmddweightvaluesdict[yutils.dutils.mmdd_from_imonth_iday(imonth, iday)]

        #
        #
        #
        return _weightvaluesfunction

#
#
#
def makegraphs(inputdirectory, bmakepng):
    #
    #
    #
    verbose = True
    #
    #
    #
    yyyymmddfirst    = 20170101
    yyyymmddlast     = 20180101 
    #
    #    outlier parameters
    #
    maxdip        = 0.01 #* 200 # 1% full range daily dip
    maxdif        = 0.1  #* 200 # 10% full range daily drop 
    maxgap        = None
    extremapasses = 999
    #
    #    whittaker parameters
    #
    lmbda        = 5
    passes       = 3
    dokeepmaxima = True
    #
    #    swets parameters
    #
    regressionwindow  = 51 #51
    combinationwindow = 51 #51
    #
    #    weights parameters
    #
    aboutequalepsilon = 0.01 #2
    #
    #
    #
    minfieldokfraction = 0.95
    #
    #    dixit swets_roel
    #
#     potatoweightintevals = WeightIntevals(yatt.smooth.WeightValues(maximum = 0, minimum = 0, posslope=0, negslope=0, aboutequal=0, default=0.1))
#     potatoweightintevals.addWeightValuesInterval("0101", "0501", yatt.smooth.WeightValues(maximum = 3.5, minimum = 0.005, posslope=0.1, negslope=0.1, aboutequal=0.1, default=0.1))
#     potatoweightintevals.addWeightValuesInterval("0501", "0715", yatt.smooth.WeightValues(maximum = 1.5, minimum = 3.5,   posslope=0.1, negslope=0.1, aboutequal=0.1, default=0.1))
#     potatoweightintevals.addWeightValuesInterval("0715", "1021", yatt.smooth.WeightValues(maximum = 3.5, minimum = 0.005, posslope=0.1, negslope=0.1, aboutequal=0.1, default=0.1))
#     potatoweightintevals.addWeightValuesInterval("1021", "1231", yatt.smooth.WeightValues(maximum = 1.5, minimum = 3.5,   posslope=0.1, negslope=0.1, aboutequal=0.1, default=0.1))
    #
    #    simplified temporal weights; just enhance growing season
    #
    potatoweightintevals = WeightIntevals(yatt.smooth.WeightValues(maximum = 1, minimum = 1, posslope=1, negslope=1, aboutequal=1, default=1))
    potatoweightintevals.addWeightValuesInterval("0601", "1001", yatt.smooth.WeightValues(maximum = 3.5, minimum = 0.005, posslope=0.1, negslope=0.1, aboutequal=0.1, default=0.1))
    potatoweightvaluesfunction = potatoweightintevals.makeweightvaluesfunction()

    #
    #
    #
    field_gdaldataset = osgeo.gdal.Open(os.path.join(inputdirectory,"fieldmask.tif"))
    field_numpyparray = field_gdaldataset.ReadAsArray()

    #
    #
    #
    iIdx                  = -1
    numberofobservations  = 0

    #
    #
    #    
    profile_zedates                                       = []
    profile_all_fapar_pixels_all_field_observations       = [] # all valid pixels in the field (not "no data"), for all observations
    profile_all_fapar_pixels_good_field_observations      = [] # all valid pixels in the field (not "no data"), only observations with x% of the pixels are valid
    profile_perfect_fapar_pixels_good_field_observations  = [] # all perfect pixels in the field (not "no data"), only observations with x% of the pixels are valid

    #
    #
    #    
    for date_yyyymmdd in yutils.dutils.g_yyyymmdd_interval(yyyymmddfirst, yyyymmddlast):

        profile_zedates.append(date_yyyymmdd)
        profile_all_fapar_pixels_all_field_observations.append(None)
        profile_all_fapar_pixels_good_field_observations.append(None)
        profile_perfect_fapar_pixels_good_field_observations.append(None)
        iIdx += 1

        ptFAPARpattern = demo.testdata.makefilenamepattern(date_yyyymmdd, "FAPAR_10M")
        ptSCENEpattern = demo.testdata.makefilenamepattern(date_yyyymmdd, "SCENECLASSIFICATION_10M")

        szFAPARfilenames =  [f for f in os.listdir(inputdirectory) if re.match(ptFAPARpattern, f)]
        szSCENEfilenames =  [f for f in os.listdir(inputdirectory) if re.match(ptSCENEpattern, f)]

        if not (szFAPARfilenames and szSCENEfilenames) : continue
        numberofobservations += 1
 
        #
        #    all files for this date are available 
        #
        fapar_gdaldataset   = osgeo.gdal.Open(os.path.join(inputdirectory,szFAPARfilenames[0]))
        scene_gdaldataset   = osgeo.gdal.Open(os.path.join(inputdirectory,szSCENEfilenames[0]))

        #
        #    mask the raster with the field - result is an array - no a raster anymore
        #
        fapar_numpyparray = fapar_gdaldataset.ReadAsArray()[field_numpyparray == 0]
        scene_numpyparray = scene_gdaldataset.ReadAsArray()[field_numpyparray == 0]

        #
        #
        #
        total_all_pixels           = fapar_numpyparray.size
        total_all_fapar_pixels     = fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue)].size
        total_perfect_fapar_pixels = fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue) & (scene_numpyparray < 8) & (scene_numpyparray > 3)].size # "low probability clouds" allowed

        #
        #
        #
        if verbose:
            print
            print (date_yyyymmdd)
            print ("total pixels in field             %s" % (total_all_pixels))
            print ("total fapar as data               %s" % (total_all_fapar_pixels))
            print ("total fapar in perfect scene      %s" % (total_perfect_fapar_pixels))

        #
        #    averages & scale
        #
        if 0 < total_all_fapar_pixels:
            average_all_fapar_pixels_all_field_observations = numpy.average(fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue)])
            profile_all_fapar_pixels_all_field_observations[iIdx] = average_all_fapar_pixels_all_field_observations / 200.
            if verbose: print ("average fapars data               %s" % (average_all_fapar_pixels_all_field_observations))

        if 0 < total_all_fapar_pixels and minfieldokfraction <= (float(total_all_fapar_pixels) / float(total_all_pixels)) :
            average_all_fapar_pixels_good_field_observation = numpy.average(fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue)])
            profile_all_fapar_pixels_good_field_observations[iIdx] = average_all_fapar_pixels_good_field_observation / 200.
            if verbose: print ("average fapars data good fields   %s" % (average_all_fapar_pixels_good_field_observation))

        if 0 < total_perfect_fapar_pixels and minfieldokfraction <= (float(total_perfect_fapar_pixels) / float(total_all_pixels)) :
            average_perfect_fapar_pixels_good_field_observations = numpy.average(fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue)& (scene_numpyparray < 8) & (scene_numpyparray > 3)])
            profile_perfect_fapar_pixels_good_field_observations[iIdx] = average_perfect_fapar_pixels_good_field_observations / 200.
            if verbose: print ("average perfect fapar good fields %s" % (average_perfect_fapar_pixels_good_field_observations))



    #
    #    callback for yatt.smooth.makeweightscube
    #    since we're dealing with scalars, not rasters, this might seem like overkill, but hey...
    #
    def potatoweightsrasterfunction(iRasterIdx, weighttypesraster):
        """
        """
        yyyymmdd = profile_zedates[iRasterIdx]
        weightsraster = numpy.full_like(weighttypesraster, numpy.nan, dtype=float)
        weightsraster[weighttypesraster == yatt.smooth.WeightTypeId.MAXIMUM]    = potatoweightvaluesfunction(yyyymmdd).getweight(yatt.smooth.WeightTypeId.MAXIMUM)
        weightsraster[weighttypesraster == yatt.smooth.WeightTypeId.MINIMUM]    = potatoweightvaluesfunction(yyyymmdd).getweight(yatt.smooth.WeightTypeId.MINIMUM)
        weightsraster[weighttypesraster == yatt.smooth.WeightTypeId.POSSLOPE]   = potatoweightvaluesfunction(yyyymmdd).getweight(yatt.smooth.WeightTypeId.POSSLOPE)
        weightsraster[weighttypesraster == yatt.smooth.WeightTypeId.NEGSLOPE]   = potatoweightvaluesfunction(yyyymmdd).getweight(yatt.smooth.WeightTypeId.NEGSLOPE)
        weightsraster[weighttypesraster == yatt.smooth.WeightTypeId.ABOUTEQUAL] = potatoweightvaluesfunction(yyyymmdd).getweight(yatt.smooth.WeightTypeId.ABOUTEQUAL)
        weightsraster[weighttypesraster == yatt.smooth.WeightTypeId.DEFAULT]    = potatoweightvaluesfunction(yyyymmdd).getweight(yatt.smooth.WeightTypeId.DEFAULT)

        #print ("raster[%s] date(%s) weight:%s"%(iRasterIdx, yyyymmdd, weightsraster)) 
        return weightsraster

    #
    #
    #
    mindatavalue = demo.testdata.minimumdatavalue / 200.
    maxdatavalue = demo.testdata.maximumdatavalue / 200.

    all_fapar_all_field_raw_data_datacube      = yatt.smooth.makedatacube(profile_all_fapar_pixels_all_field_observations,      minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    all_fapar_good_field_raw_data_datacube     = yatt.smooth.makedatacube(profile_all_fapar_pixels_good_field_observations,     minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    perfect_fapar_good_field_raw_data_datacube = yatt.smooth.makedatacube(profile_perfect_fapar_pixels_good_field_observations, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)

    all_fapar_all_field_raw_data_standard_whittaker_datacube      = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_all_field_raw_data_datacube,      None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    all_fapar_good_field_raw_data_standard_whittaker_datacube     = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_good_field_raw_data_datacube,     None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    perfect_fapar_good_field_raw_data_standard_whittaker_datacube = yatt.smooth.whittaker_second_differences(lmbda, perfect_fapar_good_field_raw_data_datacube, None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)

    all_fapar_all_field_raw_data_unweighted_swets_datacube      = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_all_field_raw_data_datacube,      numpyweightscube= None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    all_fapar_good_field_raw_data_unweighted_swets_datacube     = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_good_field_raw_data_datacube,     numpyweightscube= None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    perfect_fapar_good_field_raw_data_unweighted_swets_datacube = yatt.smooth.swets(regressionwindow, combinationwindow, perfect_fapar_good_field_raw_data_datacube, numpyweightscube= None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)


    all_fapar_all_field_raw_data_weightstypecube      = yatt.smooth.makeweighttypescube(all_fapar_all_field_raw_data_datacube,      aboutequalepsilon)
    all_fapar_good_field_raw_data_weightstypecube     = yatt.smooth.makeweighttypescube(all_fapar_good_field_raw_data_datacube,     aboutequalepsilon)
    perfect_fapar_good_field_raw_data_weightstypecube = yatt.smooth.makeweighttypescube(perfect_fapar_good_field_raw_data_datacube, aboutequalepsilon)

    all_fapar_all_field_raw_data_stdswetsweightscube      = yatt.smooth.makesimpleweightscube(all_fapar_all_field_raw_data_weightstypecube,      weightvalues=yatt.smooth.defaultswetsweightvalues)
    all_fapar_good_field_raw_data_stdswetsweightscube     = yatt.smooth.makesimpleweightscube(all_fapar_good_field_raw_data_weightstypecube,     weightvalues=yatt.smooth.defaultswetsweightvalues)
    perfect_fapar_good_field_raw_data_stdswetsweightscube = yatt.smooth.makesimpleweightscube(perfect_fapar_good_field_raw_data_weightstypecube, weightvalues=yatt.smooth.defaultswetsweightvalues)

    all_fapar_all_field_raw_data_stdswetsweights_whittaker_datacube      = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_all_field_raw_data_datacube,      all_fapar_all_field_raw_data_stdswetsweightscube,     minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    all_fapar_good_field_raw_data_stdswetsweights_whittaker_datacube     = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_good_field_raw_data_datacube,     all_fapar_good_field_raw_data_stdswetsweightscube,    minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    perfect_fapar_good_field_raw_data_stdswetsweights_whittaker_datacube = yatt.smooth.whittaker_second_differences(lmbda, perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_stdswetsweightscube, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)

    all_fapar_all_field_raw_data_stdswetsweights_swets_datacube      = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_all_field_raw_data_datacube,      numpyweightscube= all_fapar_all_field_raw_data_stdswetsweightscube,      minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    all_fapar_good_field_raw_data_stdswetsweights_swets_datacube     = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_good_field_raw_data_datacube,     numpyweightscube= all_fapar_good_field_raw_data_stdswetsweightscube,     minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    perfect_fapar_good_field_raw_data_stdswetsweights_swets_datacube = yatt.smooth.swets(regressionwindow, combinationwindow, perfect_fapar_good_field_raw_data_datacube, numpyweightscube= perfect_fapar_good_field_raw_data_stdswetsweightscube, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)


    all_fapar_all_field_raw_data_potatoweightscube      = yatt.smooth.makeweightscube(all_fapar_all_field_raw_data_weightstypecube,      potatoweightsrasterfunction)
    all_fapar_good_field_raw_data_potatoweightscube     = yatt.smooth.makeweightscube(all_fapar_good_field_raw_data_weightstypecube,     potatoweightsrasterfunction)
    perfect_fapar_good_field_raw_data_potatoweightscube = yatt.smooth.makeweightscube(perfect_fapar_good_field_raw_data_weightstypecube, potatoweightsrasterfunction)
    
    all_fapar_all_field_raw_data_potatoweights_whittaker_datacube      = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_all_field_raw_data_datacube,      all_fapar_all_field_raw_data_potatoweightscube,      minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    all_fapar_good_field_raw_data_potatoweights_whittaker_datacube     = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_good_field_raw_data_datacube,     all_fapar_good_field_raw_data_potatoweightscube,     minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    perfect_fapar_good_field_raw_data_potatoweights_whittaker_datacube = yatt.smooth.whittaker_second_differences(lmbda, perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_potatoweightscube, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)

    all_fapar_all_field_raw_data_potatoweights_swets_datacube      = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_all_field_raw_data_datacube,      numpyweightscube= all_fapar_all_field_raw_data_potatoweightscube,      minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    all_fapar_good_field_raw_data_potatoweights_swets_datacube     = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_good_field_raw_data_datacube,     numpyweightscube= all_fapar_good_field_raw_data_potatoweightscube,     minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    perfect_fapar_good_field_raw_data_potatoweights_swets_datacube = yatt.smooth.swets(regressionwindow, combinationwindow, perfect_fapar_good_field_raw_data_datacube, numpyweightscube= perfect_fapar_good_field_raw_data_potatoweightscube, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)




    all_fapar_all_field_nooutliers_data_datacube      = yatt.smooth.flaglocalminima(numpy.copy(all_fapar_all_field_raw_data_datacube),      maxdip, maxdif, maxgap=maxgap, maxpasses=extremapasses)
    all_fapar_good_field_nooutliers_data_datacube     = yatt.smooth.flaglocalminima(numpy.copy(all_fapar_good_field_raw_data_datacube),     maxdip, maxdif, maxgap=maxgap, maxpasses=extremapasses)
    perfect_fapar_good_field_nooutliers_data_datacube = yatt.smooth.flaglocalminima(numpy.copy(perfect_fapar_good_field_raw_data_datacube), maxdip, maxdif, maxgap=maxgap, maxpasses=extremapasses)

    all_fapar_all_field_nooutliers_data_standard_whittaker_datacube      = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_all_field_nooutliers_data_datacube,      None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    all_fapar_good_field_nooutliers_data_standard_whittaker_datacube     = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_good_field_nooutliers_data_datacube,     None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    perfect_fapar_good_field_nooutliers_data_standard_whittaker_datacube = yatt.smooth.whittaker_second_differences(lmbda, perfect_fapar_good_field_nooutliers_data_datacube, None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)

    all_fapar_all_field_nooutliers_data_unweighted_swets_datacube      = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_all_field_nooutliers_data_datacube,      numpyweightscube= None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    all_fapar_good_field_nooutliers_data_unweighted_swets_datacube     = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_good_field_nooutliers_data_datacube,     numpyweightscube= None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    perfect_fapar_good_field_nooutliers_data_unweighted_swets_datacube = yatt.smooth.swets(regressionwindow, combinationwindow, perfect_fapar_good_field_nooutliers_data_datacube, numpyweightscube= None, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)


    all_fapar_all_field_nooutliers_data_weightstypecube      = yatt.smooth.makeweighttypescube(all_fapar_all_field_nooutliers_data_datacube,      aboutequalepsilon)
    all_fapar_good_field_nooutliers_data_weightstypecube     = yatt.smooth.makeweighttypescube(all_fapar_good_field_nooutliers_data_datacube,     aboutequalepsilon)
    perfect_fapar_good_field_nooutliers_data_weightstypecube = yatt.smooth.makeweighttypescube(perfect_fapar_good_field_nooutliers_data_datacube, aboutequalepsilon)

    all_fapar_all_field_nooutliers_data_stdswetsweightscube      = yatt.smooth.makesimpleweightscube(all_fapar_all_field_nooutliers_data_weightstypecube,      weightvalues=yatt.smooth.defaultswetsweightvalues)
    all_fapar_good_field_nooutliers_data_stdswetsweightscube     = yatt.smooth.makesimpleweightscube(all_fapar_good_field_nooutliers_data_weightstypecube,     weightvalues=yatt.smooth.defaultswetsweightvalues)
    perfect_fapar_good_field_nooutliers_data_stdswetsweightscube = yatt.smooth.makesimpleweightscube(perfect_fapar_good_field_nooutliers_data_weightstypecube, weightvalues=yatt.smooth.defaultswetsweightvalues)

    all_fapar_all_field_nooutliers_data_stdswetsweights_whittaker_datacube      = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_all_field_nooutliers_data_datacube,      all_fapar_all_field_nooutliers_data_stdswetsweightscube,     minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    all_fapar_good_field_nooutliers_data_stdswetsweights_whittaker_datacube     = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_good_field_nooutliers_data_datacube,     all_fapar_good_field_nooutliers_data_stdswetsweightscube,    minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    perfect_fapar_good_field_nooutliers_data_stdswetsweights_whittaker_datacube = yatt.smooth.whittaker_second_differences(lmbda, perfect_fapar_good_field_nooutliers_data_datacube, perfect_fapar_good_field_nooutliers_data_stdswetsweightscube, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)

    all_fapar_all_field_nooutliers_data_stdswetsweights_swets_datacube      = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_all_field_nooutliers_data_datacube,      numpyweightscube= all_fapar_all_field_nooutliers_data_stdswetsweightscube,      minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    all_fapar_good_field_nooutliers_data_stdswetsweights_swets_datacube     = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_good_field_nooutliers_data_datacube,     numpyweightscube= all_fapar_good_field_nooutliers_data_stdswetsweightscube,     minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    perfect_fapar_good_field_nooutliers_data_stdswetsweights_swets_datacube = yatt.smooth.swets(regressionwindow, combinationwindow, perfect_fapar_good_field_nooutliers_data_datacube, numpyweightscube= perfect_fapar_good_field_nooutliers_data_stdswetsweightscube, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)


    all_fapar_all_field_nooutliers_data_potatoweightscube      = yatt.smooth.makeweightscube(all_fapar_all_field_nooutliers_data_weightstypecube,      potatoweightsrasterfunction)
    all_fapar_good_field_nooutliers_data_potatoweightscube     = yatt.smooth.makeweightscube(all_fapar_good_field_nooutliers_data_weightstypecube,     potatoweightsrasterfunction)
    perfect_fapar_good_field_nooutliers_data_potatoweightscube = yatt.smooth.makeweightscube(perfect_fapar_good_field_nooutliers_data_weightstypecube, potatoweightsrasterfunction)
    
    all_fapar_all_field_nooutliers_data_potatoweights_whittaker_datacube      = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_all_field_nooutliers_data_datacube,      all_fapar_all_field_nooutliers_data_potatoweightscube,     minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    all_fapar_good_field_nooutliers_data_potatoweights_whittaker_datacube     = yatt.smooth.whittaker_second_differences(lmbda, all_fapar_good_field_nooutliers_data_datacube,     all_fapar_good_field_nooutliers_data_potatoweightscube,    minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    perfect_fapar_good_field_nooutliers_data_potatoweights_whittaker_datacube = yatt.smooth.whittaker_second_differences(lmbda, perfect_fapar_good_field_nooutliers_data_datacube, perfect_fapar_good_field_nooutliers_data_potatoweightscube, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)

    all_fapar_all_field_nooutliers_data_potatoweights_swets_datacube      = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_all_field_nooutliers_data_datacube,      numpyweightscube= all_fapar_all_field_nooutliers_data_potatoweightscube,      minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    all_fapar_good_field_nooutliers_data_potatoweights_swets_datacube     = yatt.smooth.swets(regressionwindow, combinationwindow, all_fapar_good_field_nooutliers_data_datacube,     numpyweightscube= all_fapar_good_field_nooutliers_data_potatoweightscube,     minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)
    perfect_fapar_good_field_nooutliers_data_potatoweights_swets_datacube = yatt.smooth.swets(regressionwindow, combinationwindow, perfect_fapar_good_field_nooutliers_data_datacube, numpyweightscube= perfect_fapar_good_field_nooutliers_data_potatoweightscube, minimumdatavalue=mindatavalue, maximumdatavalue=maxdatavalue)

    #
    #    aesthetics: show lines only between first and last actual point available
    #
    def removeextrapolation(rawdataarray, smoothedarray):
        for iIdx in range(len(rawdataarray)):
            if numpy.isnan(rawdataarray[iIdx]): smoothedarray[iIdx] = numpy.nan
            else: break
        for iIdx in range(len(rawdataarray))[::-1]: # reversed
            if numpy.isnan(rawdataarray[iIdx]): smoothedarray[iIdx] = numpy.nan
            else: break

    if True:
        removeextrapolation(all_fapar_all_field_raw_data_datacube, all_fapar_all_field_raw_data_standard_whittaker_datacube)    
        removeextrapolation(all_fapar_all_field_raw_data_datacube, all_fapar_all_field_raw_data_stdswetsweights_whittaker_datacube)    
        removeextrapolation(all_fapar_all_field_raw_data_datacube, all_fapar_all_field_raw_data_potatoweights_whittaker_datacube)    
        removeextrapolation(all_fapar_all_field_raw_data_datacube, all_fapar_all_field_raw_data_unweighted_swets_datacube)    
        removeextrapolation(all_fapar_all_field_raw_data_datacube, all_fapar_all_field_raw_data_stdswetsweights_swets_datacube)    
        removeextrapolation(all_fapar_all_field_raw_data_datacube, all_fapar_all_field_raw_data_potatoweights_swets_datacube)    

        removeextrapolation(all_fapar_good_field_raw_data_datacube, all_fapar_good_field_raw_data_standard_whittaker_datacube)    
        removeextrapolation(all_fapar_good_field_raw_data_datacube, all_fapar_good_field_raw_data_stdswetsweights_whittaker_datacube)    
        removeextrapolation(all_fapar_good_field_raw_data_datacube, all_fapar_good_field_raw_data_potatoweights_whittaker_datacube)    
        removeextrapolation(all_fapar_good_field_raw_data_datacube, all_fapar_good_field_raw_data_unweighted_swets_datacube)    
        removeextrapolation(all_fapar_good_field_raw_data_datacube, all_fapar_good_field_raw_data_stdswetsweights_swets_datacube)    
        removeextrapolation(all_fapar_good_field_raw_data_datacube, all_fapar_good_field_raw_data_potatoweights_swets_datacube)    

        removeextrapolation(perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_standard_whittaker_datacube)    
        removeextrapolation(perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_stdswetsweights_whittaker_datacube)    
        removeextrapolation(perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_potatoweights_whittaker_datacube)    
        removeextrapolation(perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_unweighted_swets_datacube)    
        removeextrapolation(perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_stdswetsweights_swets_datacube)    
        removeextrapolation(perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_potatoweights_swets_datacube)    


        removeextrapolation(all_fapar_all_field_nooutliers_data_datacube, all_fapar_all_field_nooutliers_data_standard_whittaker_datacube)    
        removeextrapolation(all_fapar_all_field_nooutliers_data_datacube, all_fapar_all_field_nooutliers_data_stdswetsweights_whittaker_datacube)    
        removeextrapolation(all_fapar_all_field_nooutliers_data_datacube, all_fapar_all_field_nooutliers_data_potatoweights_whittaker_datacube)    
        removeextrapolation(all_fapar_all_field_nooutliers_data_datacube, all_fapar_all_field_nooutliers_data_unweighted_swets_datacube)    
        removeextrapolation(all_fapar_all_field_nooutliers_data_datacube, all_fapar_all_field_nooutliers_data_stdswetsweights_swets_datacube)    
        removeextrapolation(all_fapar_all_field_nooutliers_data_datacube, all_fapar_all_field_nooutliers_data_potatoweights_swets_datacube)    
        
        removeextrapolation(all_fapar_good_field_nooutliers_data_datacube, all_fapar_good_field_nooutliers_data_standard_whittaker_datacube)    
        removeextrapolation(all_fapar_good_field_nooutliers_data_datacube, all_fapar_good_field_nooutliers_data_stdswetsweights_whittaker_datacube)    
        removeextrapolation(all_fapar_good_field_nooutliers_data_datacube, all_fapar_good_field_nooutliers_data_potatoweights_whittaker_datacube)    
        removeextrapolation(all_fapar_good_field_nooutliers_data_datacube, all_fapar_good_field_nooutliers_data_unweighted_swets_datacube)    
        removeextrapolation(all_fapar_good_field_nooutliers_data_datacube, all_fapar_good_field_nooutliers_data_stdswetsweights_swets_datacube)    
        removeextrapolation(all_fapar_good_field_nooutliers_data_datacube, all_fapar_good_field_nooutliers_data_potatoweights_swets_datacube)    

        removeextrapolation(perfect_fapar_good_field_nooutliers_data_datacube, perfect_fapar_good_field_nooutliers_data_standard_whittaker_datacube)    
        removeextrapolation(perfect_fapar_good_field_nooutliers_data_datacube, perfect_fapar_good_field_nooutliers_data_stdswetsweights_whittaker_datacube)    
        removeextrapolation(perfect_fapar_good_field_nooutliers_data_datacube, perfect_fapar_good_field_nooutliers_data_potatoweights_whittaker_datacube)    
        removeextrapolation(perfect_fapar_good_field_nooutliers_data_datacube, perfect_fapar_good_field_nooutliers_data_unweighted_swets_datacube)    
        removeextrapolation(perfect_fapar_good_field_nooutliers_data_datacube, perfect_fapar_good_field_nooutliers_data_stdswetsweights_swets_datacube)
        removeextrapolation(perfect_fapar_good_field_nooutliers_data_datacube, perfect_fapar_good_field_nooutliers_data_potatoweights_swets_datacube)

    #
    #    overview Whittaker
    #
    if True:
        #
        #
        #
        rows = 2
        cols = 3
        subplots = numpy.empty( (rows,cols), dtype=object )

        figure = matplotlib.pyplot.figure(figsize=(16,9))
        for irow in range(rows):
            for icol in range(cols):
                subplots[irow, icol] = figure.add_subplot(rows, cols, 1 + icol + irow * cols)

        row = 0; col = 0
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_standard_whittaker_datacube,     'Red'    ); #line.set_label("all data")  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_standard_whittaker_datacube,    'Green'  ); #line.set_label("%s pct field ok"%(int(100*minfieldokfraction)))     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_standard_whittaker_datacube,'Blue'   ); #line.set_label("%s pct field perfect"%(int(100*minfieldokfraction))) 

        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_datacube,                  'ro' ); line.set_label("all data")    
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_datacube,                 'go' ); line.set_label("%s pct field ok"%(int(100*minfieldokfraction)))   
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_datacube,             'bo' ); line.set_label("%s pct field perfect"%(int(100*minfieldokfraction)))   
        subplots[row, col].set_title("whittaker default")
        subplots[row, col].legend()

        row = 0; col = 1
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_stdswetsweights_whittaker_datacube,     'Red'    ); #line.set_label('whit.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_stdswetsweights_whittaker_datacube,    'Green'  ); #line.set_label('swets no outliers')     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_stdswetsweights_whittaker_datacube,'Blue'   ); #line.set_label('interp-swets no outliers')   

        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_datacube,                  'ro' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_datacube,                 'go' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_datacube,             'bo' )  
        subplots[row, col].set_title("whittaker swets weights")
        #subplots[row, col].legend()

        row = 0; col = 2
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_potatoweights_whittaker_datacube,    'Red'     ); #line.set_label('whit.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_potatoweights_whittaker_datacube,   'Green'   ); #line.set_label('swets no outliers')     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_potatoweights_whittaker_datacube,'Blue'   ); #line.set_label('interp-swets no outliers')   

        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_datacube,                       'ro' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_datacube,                      'go' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_datacube,                  'bo' )  
        subplots[row, col].set_title("whittaker temporal weights")
        #subplots[row, col].legend()

        row = 1; col = 0
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_standard_whittaker_datacube,    'Red'     ); #line.set_label('whit.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_standard_whittaker_datacube,   'Green'   ); #line.set_label('swets no outliers')     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_standard_whittaker_datacube,'Blue'   ); #line.set_label('interp-swets no outliers')   

        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_datacube,                  'ro' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_datacube,                 'go' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_datacube,             'bo' )  
        subplots[row, col].set_title("whittaker default - no outliers")
        #subplots[row, col].legend()    

        row = 1; col = 1
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_stdswetsweights_whittaker_datacube,     'Red'    ); #line.set_label('whit.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_stdswetsweights_whittaker_datacube,    'Green'  ); #line.set_label('swets no outliers')     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_stdswetsweights_whittaker_datacube,'Blue'   ); #line.set_label('interp-swets no outliers')   

        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_datacube,                  'ro' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_datacube,                 'go' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_datacube,             'bo' )  
        subplots[row, col].set_title("whittaker swets weights - no outliers")
        #subplots[row, col].legend()    

        row = 1; col = 2
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_potatoweights_whittaker_datacube,    'Red'     ); #line.set_label('whit.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_potatoweights_whittaker_datacube,   'Green'   ); #line.set_label('swets no outliers')     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_potatoweights_whittaker_datacube,'Blue'   ); #line.set_label('interp-swets no outliers')   

        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_datacube,                  'ro' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_datacube,                 'go' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_datacube,             'bo' )  
        subplots[row, col].set_title("whittaker temporal weights - no outliers")
        #subplots[row, col].legend()    

        for irow in range(rows):
            for icol in range(cols):
                subplots[irow, icol].xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d/%m'))
                subplots[irow, icol].set_ylim(-0.05, 1.05)
                for tick in subplots[irow, icol].get_xticklabels(): tick.set_rotation(45)

        matplotlib.pyplot.subplots_adjust(left = 0.05, right = 0.95, wspace=0.1, hspace=0.4)
        matplotlib.pyplot.suptitle(os.path.basename(inputdirectory) + " - Whittaker - dip(%s) dif(%s) lmbda(%s) pass(%s)"%(maxdip, maxdif, lmbda, passes))

        if bmakepng:
            matplotlib.pyplot.savefig(os.path.join(demo.testdata.sztestdatarootdirectory, os.path.basename(inputdirectory) + "_Whitt_Overview.png"), dpi=300)
        else:
            matplotlib.pyplot.show()
        matplotlib.pyplot.close('all')

    #
    #    overview Swets
    #
    if True:
        #
        #
        #
        rows = 2
        cols = 3
        subplots = numpy.empty( (rows,cols), dtype=object )

        figure = matplotlib.pyplot.figure(figsize=(16,9))
        for irow in range(rows):
            for icol in range(cols):
                subplots[irow, icol] = figure.add_subplot(rows, cols, 1 + icol + irow * cols)

        row = 0; col = 0
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_unweighted_swets_datacube,     'Red'    ); #line.set_label("all data")  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_unweighted_swets_datacube,    'Green'  ); #line.set_label("%s pct field ok"%(int(100*minfieldokfraction)))     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_unweighted_swets_datacube,'Blue'   ); #line.set_label("%s pct field perfect"%(int(100*minfieldokfraction))) 

        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_datacube,                  'ro' ); line.set_label("all data")    
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_datacube,                 'go' ); line.set_label("%s pct field ok"%(int(100*minfieldokfraction)))   
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_datacube,             'bo' ); line.set_label("%s pct field perfect"%(int(100*minfieldokfraction)))   
        subplots[row, col].set_title("unweighted swets")
        subplots[row, col].legend()

        row = 0; col = 1
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_stdswetsweights_swets_datacube,     'Red'    ); #line.set_label('whit.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_stdswetsweights_swets_datacube,    'Green'  ); #line.set_label('swets no outliers')     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_stdswetsweights_swets_datacube,'Blue'   ); #line.set_label('interp-swets no outliers')   

        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_datacube,                  'ro' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_datacube,                 'go' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_datacube,             'bo' )  
        subplots[row, col].set_title("swets default weights")
        #subplots[row, col].legend()

        row = 0; col = 2
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_potatoweights_swets_datacube,    'Red'     ); #line.set_label('whit.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_potatoweights_swets_datacube,   'Green'   ); #line.set_label('swets no outliers')     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_potatoweights_swets_datacube,'Blue'   ); #line.set_label('interp-swets no outliers')   

        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_raw_data_datacube,                       'ro' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_raw_data_datacube,                      'go' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_raw_data_datacube,                  'bo' )  
        subplots[row, col].set_title("swets temporal weights")
        #subplots[row, col].legend()

        row = 1; col = 0
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_unweighted_swets_datacube,    'Red'     ); #line.set_label('whit.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_unweighted_swets_datacube,   'Green'   ); #line.set_label('swets no outliers')     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_unweighted_swets_datacube,'Blue'   ); #line.set_label('interp-swets no outliers')   

        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_datacube,                  'ro' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_datacube,                 'go' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_datacube,             'bo' )  
        subplots[row, col].set_title("unweighted swets - no outliers")
        #subplots[row, col].legend()    

        row = 1; col = 1
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_stdswetsweights_swets_datacube,     'Red'    ); #line.set_label('whit.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_stdswetsweights_swets_datacube,    'Green'  ); #line.set_label('swets no outliers')     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_stdswetsweights_swets_datacube,'Blue'   ); #line.set_label('interp-swets no outliers')   

        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_datacube,                  'ro' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_datacube,                 'go' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_datacube,             'bo' )  
        subplots[row, col].set_title("swets default weights - no outliers")
        #subplots[row, col].legend()    

        row = 1; col = 2
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_potatoweights_swets_datacube,    'Red'     ); #line.set_label('whit.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_potatoweights_swets_datacube,   'Green'   ); #line.set_label('swets no outliers')     
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_potatoweights_swets_datacube,'Blue'   ); #line.set_label('interp-swets no outliers')   

        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_all_field_nooutliers_data_datacube,                  'ro' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_fapar_good_field_nooutliers_data_datacube,                 'go' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_fapar_good_field_nooutliers_data_datacube,             'bo' )  
        subplots[row, col].set_title("swets temporal weights - no outliers")
        #subplots[row, col].legend()    

        for irow in range(rows):
            for icol in range(cols):
                subplots[irow, icol].xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d/%m'))
                subplots[irow, icol].set_ylim(-0.05, 1.05)
                for tick in subplots[irow, icol].get_xticklabels(): tick.set_rotation(45)

        matplotlib.pyplot.subplots_adjust(left = 0.05, right = 0.95, wspace=0.1, hspace=0.4)
        matplotlib.pyplot.suptitle(os.path.basename(inputdirectory) + " - Swets - dip(%s) dif(%s) reg(%s) com(%s)"%(maxdip, maxdif, regressionwindow, combinationwindow))
        matplotlib.pyplot.savefig(os.path.join(demo.testdata.sztestdatarootdirectory, os.path.basename(inputdirectory) + "_Swets_Overview.png"), dpi=300)

        if bmakepng:
            matplotlib.pyplot.savefig(os.path.join(demo.testdata.sztestdatarootdirectory, os.path.basename(inputdirectory) + "_Whitt_Overview.png"), dpi=300)
        else:
            matplotlib.pyplot.show()
        matplotlib.pyplot.close('all')

    #
    #    step by step for screenshots
    #
    if True:
        #
        #
        #
        def lazy(szbasename, items, itemfmts):
            matplotlib.pyplot.figure(figsize=(9,4.5))
            for iIdx in range(len(items)):
                matplotlib.pyplot.plot_date(matplotlib.dates.datestr2num (profile_zedates), items[iIdx], itemfmts[iIdx]);
            matplotlib.pyplot.xticks(rotation=45)
            matplotlib.pyplot.gca().xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d/%m'))
            matplotlib.pyplot.ylim(-0.05, 1.05)
            if bmakepng and (szbasename is not None) :
                matplotlib.pyplot.savefig(os.path.join(demo.testdata.sztestdatarootdirectory, os.path.basename(inputdirectory) + "_" + szbasename + ".png"), dpi=300)
            else :
                matplotlib.pyplot.show()
            matplotlib.pyplot.close('all')

        #
        #    raw_data            - std whittaker
        #                        - unweighted swets
        #
        lazy("Whitt_Grafiek_1_", [all_fapar_all_field_raw_data_standard_whittaker_datacube,              all_fapar_all_field_raw_data_datacube],                                                                                     ['r', 'ro'] )
        lazy("Swets_Grafiek_1_", [all_fapar_all_field_raw_data_unweighted_swets_datacube,                all_fapar_all_field_raw_data_datacube],                                                                                     ['r', 'ro'] )
        #
        #    good fields data    - std whittaker
        #                        - unweighted swets
        #
        lazy("Whitt_Grafiek_2_", [all_fapar_good_field_raw_data_standard_whittaker_datacube,             all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube],                                             ['g', 'ro', 'go'] )
        lazy("Swets_Grafiek_2_", [all_fapar_good_field_raw_data_unweighted_swets_datacube,               all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube],                                             ['g', 'ro', 'go'] )
        #
        #    perfect fields data - std whittaker
        #                        - unweighted swets
        #
        lazy("Whitt_Grafiek_3_", [perfect_fapar_good_field_raw_data_standard_whittaker_datacube,         all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube], ['m', 'ro', 'go', 'mo'] )
        lazy("Swets_Grafiek_3_", [perfect_fapar_good_field_raw_data_unweighted_swets_datacube,           all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube], ['m', 'ro', 'go', 'mo'] )
        #
        #    perfect fields data without outliers  - std whittaker
        #                                          - unweighted swets
        #
        lazy("Whitt_Grafiek_b4_", [perfect_fapar_good_field_nooutliers_data_standard_whittaker_datacube, all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_nooutliers_data_datacube], ['b', 'ro', 'go', 'mo', 'bo'] )
        lazy("Swets_Grafiek_b4_", [perfect_fapar_good_field_nooutliers_data_unweighted_swets_datacube,   all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_nooutliers_data_datacube], ['b', 'ro', 'go', 'mo', 'bo'] )
        #
        #    perfect fields data without outliers  - std whittaker     => weighted whittaker => potatoweights whittaker
        #                                          - unweighted swets  => weighted swets     => potatoweights swets
        #
        lazy("Whitt_Grafiek_b5_", [perfect_fapar_good_field_nooutliers_data_standard_whittaker_datacube, perfect_fapar_good_field_nooutliers_data_stdswetsweights_whittaker_datacube,                                                                            all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_nooutliers_data_datacube], ['b--', 'b', 'ro', 'go', 'mo', 'bo'] )
        lazy("Whitt_Grafiek_b6_", [perfect_fapar_good_field_nooutliers_data_standard_whittaker_datacube, perfect_fapar_good_field_nooutliers_data_stdswetsweights_whittaker_datacube, perfect_fapar_good_field_nooutliers_data_potatoweights_whittaker_datacube, all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_nooutliers_data_datacube], ['b:', 'b--', 'b', 'ro', 'go', 'mo', 'bo'] )
        lazy("Swets_Grafiek_b5_", [perfect_fapar_good_field_nooutliers_data_unweighted_swets_datacube,   perfect_fapar_good_field_nooutliers_data_stdswetsweights_swets_datacube,                                                                                all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_nooutliers_data_datacube], ['b--', 'b', 'ro', 'go', 'mo', 'bo'] )
        lazy("Swets_Grafiek_b6_", [perfect_fapar_good_field_nooutliers_data_unweighted_swets_datacube,   perfect_fapar_good_field_nooutliers_data_stdswetsweights_swets_datacube,     perfect_fapar_good_field_nooutliers_data_potatoweights_swets_datacube,     all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_nooutliers_data_datacube], ['b:', 'b--', 'b', 'ro', 'go', 'mo', 'bo'] )
        #
        #    perfect fields data - std whittaker => weighted whittaker => potatoweights whittaker
        #                        - unweighted swets  => weighted swets => potatoweights swets
        #
        lazy("Whitt_Grafiek_t4_", [perfect_fapar_good_field_raw_data_standard_whittaker_datacube, perfect_fapar_good_field_raw_data_stdswetsweights_whittaker_datacube,                                                                     all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube], ['m--', 'm',       'ro', 'go', 'mo'] )
        lazy("Whitt_Grafiek_t5_", [perfect_fapar_good_field_raw_data_standard_whittaker_datacube, perfect_fapar_good_field_raw_data_stdswetsweights_whittaker_datacube, perfect_fapar_good_field_raw_data_potatoweights_whittaker_datacube, all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube], ['m:', 'm--', 'm', 'ro', 'go' ,'mo'] )
        lazy("Swets_Grafiek_t4_", [perfect_fapar_good_field_raw_data_unweighted_swets_datacube,   perfect_fapar_good_field_raw_data_stdswetsweights_swets_datacube,                                                                         all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube], ['m--', 'm',       'ro', 'go', 'mo'] )
        lazy("Swets_Grafiek_t5_", [perfect_fapar_good_field_raw_data_unweighted_swets_datacube,   perfect_fapar_good_field_raw_data_stdswetsweights_swets_datacube,     perfect_fapar_good_field_raw_data_potatoweights_swets_datacube,     all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube], ['m:', 'm--', 'm', 'ro', 'go' ,'mo'] )
        #
        #    perfect fields data without outliers - potatoweights whittaker
        #                                         - potatoweights swets
        #
        lazy("Whitt_Grafiek_t6_", [perfect_fapar_good_field_raw_data_potatoweights_whittaker_datacube,   perfect_fapar_good_field_nooutliers_data_potatoweights_whittaker_datacube, all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_nooutliers_data_datacube], ['m', 'b', 'ro', 'go', 'mo', 'bo'] )
        lazy("Swets_Grafiek_t6_", [perfect_fapar_good_field_raw_data_potatoweights_swets_datacube,       perfect_fapar_good_field_nooutliers_data_potatoweights_swets_datacube,     all_fapar_all_field_raw_data_datacube, all_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_raw_data_datacube, perfect_fapar_good_field_nooutliers_data_datacube], ['m', 'b', 'ro', 'go', 'mo', 'bo'] )

#
#
#
if __name__ == '__main__':
    
    #
    #
    #
    bmakepng = False
    makegraphs(os.path.join(demo.testdata.sztestdatarootdirectory, "2-AVy-ofdls9bS8_4_3GLH"  ), bmakepng)
    makegraphs(os.path.join(demo.testdata.sztestdatarootdirectory, "29-AV0TcoCXZjsFpiOBA3gL" ), bmakepng)
    makegraphs(os.path.join(demo.testdata.sztestdatarootdirectory, "190-AVzO_BSZZjsFpiOBRYcR"), bmakepng)
