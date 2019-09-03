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
#
#
def doprofiles(inputdirectory, bmakepng):
    #
    #
    #

    ###########################################################################
    #
    #    collect some data
    #
    ###########################################################################

    #
    #
    #
    yyyymmddfirst    = 20170101
    yyyymmddlast     = 20180101

    field_gdaldataset = osgeo.gdal.Open(os.path.join(inputdirectory,"fieldmask.tif"))
    field_numpyparray = field_gdaldataset.ReadAsArray()

    #
    #
    #
    profile_zedates                           = []
    profile_avarage_pixels_fapar_data         = []; size_profile_avarage_pixels_fapar_data         = 0
    profile_avarage_pixels_fapar_perfect_data = []; size_profile_avarage_pixels_fapar_perfect_data = 0

    #
    #
    #    
    iIdx                  = -1
    numberofobservations  = 0

    #
    #
    #    
    for date_yyyymmdd in yutils.dutils.g_yyyymmdd_interval(yyyymmddfirst, yyyymmddlast):

        profile_zedates.append(date_yyyymmdd)
        profile_avarage_pixels_fapar_data.append(None)
        profile_avarage_pixels_fapar_perfect_data.append(None)
        iIdx += 1

        ptFAPARpattern = demo.testdata.makefilenamepattern(date_yyyymmdd, "FAPAR_10M")
        ptCLOUDpattern = demo.testdata.makefilenamepattern(date_yyyymmdd, "CLOUDMASK_10M")
        ptSHADWpattern = demo.testdata.makefilenamepattern(date_yyyymmdd, "SHADOWMASK_10M")
        ptSCENEpattern = demo.testdata.makefilenamepattern(date_yyyymmdd, "SCENECLASSIFICATION_10M")

        szFAPARfilenames =  [f for f in os.listdir(inputdirectory) if re.match(ptFAPARpattern, f)]
        szCLOUDfilenames =  [f for f in os.listdir(inputdirectory) if re.match(ptCLOUDpattern, f)]
        szSHADWfilenames =  [f for f in os.listdir(inputdirectory) if re.match(ptSHADWpattern, f)]
        szSCENEfilenames =  [f for f in os.listdir(inputdirectory) if re.match(ptSCENEpattern, f)]

        if not (szFAPARfilenames and szCLOUDfilenames and szSHADWfilenames and szSCENEfilenames) :
            continue

        #
        #    all files for this date are available 
        #
        fapar_gdaldataset   = osgeo.gdal.Open(os.path.join(inputdirectory,szFAPARfilenames[0]))
        cloud_gdaldataset   = osgeo.gdal.Open(os.path.join(inputdirectory,szCLOUDfilenames[0]))
        shadw_gdaldataset   = osgeo.gdal.Open(os.path.join(inputdirectory,szSHADWfilenames[0]))
        scene_gdaldataset   = osgeo.gdal.Open(os.path.join(inputdirectory,szSCENEfilenames[0]))

        #
        #    mask the raster with the field - result is an array - no a raster anymore
        #         
        fapar_numpyparray = fapar_gdaldataset.ReadAsArray()[field_numpyparray == 0]
        cloud_numpyparray = cloud_gdaldataset.ReadAsArray()[field_numpyparray == 0]
        shadw_numpyparray = shadw_gdaldataset.ReadAsArray()[field_numpyparray == 0]
        scene_numpyparray = scene_gdaldataset.ReadAsArray()[field_numpyparray == 0]

        #
        #    some statistics
        #    - it is hard to find out what exactly is flagged as no data in fapar. (probably cloudmask and shadowmask. but what about snow...)
        #    - using the scene classification requires converting to 10meter resolution
        #    - scene classification "low probability clouds" seems to have problems; some fields sometimes match exactly the low probability clouds? (hence, reluctantly we allow scenes 4,5,6 AND 7)
        #
        total_pixels_in_field            = fapar_numpyparray.size
        total_pixels_as_nodata           = fapar_numpyparray[fapar_numpyparray > demo.testdata.maximumdatavalue].size
        total_pixels_as_cloud            = cloud_numpyparray[cloud_numpyparray != 0].size
        total_pixels_as_shadw            = shadw_numpyparray[shadw_numpyparray != 0].size
        total_pixels_scene_nok           = scene_numpyparray[(scene_numpyparray >= 8) | (scene_numpyparray <= 3)].size
        total_pixels_scene_nodata        = scene_numpyparray[(scene_numpyparray ==  0)].size
        total_pixels_scene_defective     = scene_numpyparray[(scene_numpyparray ==  1)].size
        total_pixels_scene_darkarea      = scene_numpyparray[(scene_numpyparray ==  2)].size
        total_pixels_scene_shadows       = scene_numpyparray[(scene_numpyparray ==  3)].size
        total_pixels_scene_loprob_clouds = scene_numpyparray[(scene_numpyparray ==  7)].size
        total_pixels_scene_meprob_clouds = scene_numpyparray[(scene_numpyparray ==  8)].size
        total_pixels_scene_hiprob_clouds = scene_numpyparray[(scene_numpyparray ==  9)].size
        total_pixels_scene_cirrus        = scene_numpyparray[(scene_numpyparray == 10)].size
        total_pixels_scene_snow          = scene_numpyparray[(scene_numpyparray == 11)].size

        total_pixels_fapar_data          = fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue)].size
        total_pixels_fapar_unmasked_data = fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue) & (cloud_numpyparray == 0) & (shadw_numpyparray == 0)].size
        #
        #    actually, at the moment CLOUDMASK_10M and SHADOWMASK_10M are burned 
        #    in FAPAR_10M as no-data but who knows what happens in next version
        #
        #total_pixels_fapar_perfect_data  = fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue) & (scene_numpyparray < 8) & (scene_numpyparray > 3)].size    
        total_pixels_fapar_perfect_data  = fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue) & (cloud_numpyparray == 0) & (shadw_numpyparray == 0) & (scene_numpyparray < 8) & (scene_numpyparray > 3)].size    

        if True:
            print (date_yyyymmdd)
            print ("total pixels in field        %s" % (total_pixels_in_field))
            print ("total fapar as data          %s" % (total_pixels_fapar_data))
            print ("total fapar as no data       %s" % (total_pixels_as_nodata))
            print ("total pixels as cloud        %s" % (total_pixels_as_cloud))
            print ("total pixels as shadow       %s" % (total_pixels_as_shadw))
            print ("sum cloud and shadow         %s" % (total_pixels_as_cloud + total_pixels_as_shadw))
            print
            print ("total pixels scene NOK       %s"    % (total_pixels_scene_nok))
            print ("total scene no data          %s %s" % (total_pixels_scene_nodata,    ("" if 0 == total_pixels_scene_nodata    else "NO DATA !")))
            print ("total scene defective        %s %s" % (total_pixels_scene_defective, ("" if 0 == total_pixels_scene_defective else "DEFECTIVE !")))
            print ("total scene dark             %s %s" % ( total_pixels_scene_darkarea, ("" if 0 == total_pixels_scene_darkarea  else "DARK !")))
            print ("total scene hi prob clouds   %s"    % (total_pixels_scene_hiprob_clouds))
            print ("total scene med prob clouds  %s"    % (total_pixels_scene_meprob_clouds))
            print ("total scene low prob clouds  %s"    % (total_pixels_scene_loprob_clouds))
            print ("total scene shadow           %s"    % (total_pixels_scene_shadows))
            print ("total scene cirrus           %s %s" % (total_pixels_scene_cirrus,    ("" if 0 == total_pixels_scene_cirrus    else "CIRRUS !")))
            print ("total scene snow             %s %s" % (total_pixels_scene_snow,      ("" if 0 == total_pixels_scene_snow      else "SNOW !")))
            print ("sum hi, med and shadow       %s"    % (total_pixels_scene_hiprob_clouds + total_pixels_scene_meprob_clouds + total_pixels_scene_shadows))


            print ("total fapar unmasked pixels  %s" % (total_pixels_fapar_unmasked_data))
            print ("total fapar perfect pixels   %s" % (total_pixels_fapar_perfect_data))
            print


        if 0 < total_pixels_fapar_data:
            numberofobservations += 1

            #
            #    all available pixel values in the fields
            #
            if 0 < total_pixels_fapar_data: #  and 0.80 <= (float(total_pixels_fapar_data) / float(total_pixels_in_field)) :
                avarage_pixels_fapar_data = numpy.average(fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue)])
                profile_avarage_pixels_fapar_data[iIdx] = avarage_pixels_fapar_data
                size_profile_avarage_pixels_fapar_data +=1

            #
            #    only perfect pixel values in case field has 80% perfect pixels 
            #
            if 0 < total_pixels_fapar_perfect_data and 0.80 <= (float(total_pixels_fapar_perfect_data) / float(total_pixels_in_field)) :
                avarage_pixels_fapar_perfect_data = numpy.average(fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue) & (cloud_numpyparray == 0) & (shadw_numpyparray == 0) & (scene_numpyparray < 8) & (scene_numpyparray > 3)])
                #avarage_pixels_fapar_perfect_data = numpy.average(fapar_numpyparray[(fapar_numpyparray <= demo.maximumdatavalue) & (scene_numpyparray < 8) & (scene_numpyparray > 3)])
                profile_avarage_pixels_fapar_perfect_data[iIdx] = avarage_pixels_fapar_perfect_data
                size_profile_avarage_pixels_fapar_perfect_data +=1

    print ("number of dates: %s - number of observations: %s" % (iIdx + 1, numberofobservations))

    #
    #
    #

    ###########################################################################
    #
    #    actual smoothing
    #
    ###########################################################################

    #
    #    outlier parameters (we're using fapar values as is: 0-200; no scaling)
    #
    maxdip        = 0.01 * 200 #0.005 * 200
    maxdif        = 0.1  * 200 #0.05  * 200
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
    regressionwindow  = 51
    combinationwindow = 51
    #
    #    weights parameters
    #
    aboutequalepsilon = 2

    #
    #    raw data
    #
    all_raw_data_datacube         = yatt.smooth.makedatacube(profile_avarage_pixels_fapar_data, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    all_raw_data_weighttypescube  = yatt.smooth.makeweighttypescube(all_raw_data_datacube, aboutequalepsilon)
    all_raw_data_swetsweightscube = yatt.smooth.makesimpleweightscube(all_raw_data_weighttypescube, weightvalues=yatt.smooth.defaultswetsweightvalues)
    #
    #    whittaker on raw data
    #
    all_raw_data_whitcube = yatt.smooth.whittaker_second_differences(lmbda, all_raw_data_datacube, None, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    #
    #    swets on raw data
    #
    all_raw_data_swetscube = yatt.smooth.swets(regressionwindow, combinationwindow, all_raw_data_datacube, all_raw_data_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    #
    #    weighted whittaker on raw data
    #
    all_raw_data_weightedwhitcube = yatt.smooth.whittaker_second_differences(lmbda, all_raw_data_datacube, all_raw_data_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    #
    #    linear interpolation + swets on raw data
    #
    all_raw_data_interpolated_datacube         = yatt.smooth.linearinterpolation(numpy.copy(all_raw_data_datacube))
    all_raw_data_interpolated_weighttypescube  = yatt.smooth.makeweighttypescube(all_raw_data_interpolated_datacube, aboutequalepsilon)
    all_raw_data_interpolated_swetsweightscube = yatt.smooth.makesimpleweightscube(all_raw_data_interpolated_weighttypescube, weightvalues=yatt.smooth.defaultswetsweightvalues)
    all_raw_data_interpolated_swetscube        = yatt.smooth.swets(regressionwindow, combinationwindow, all_raw_data_interpolated_datacube, all_raw_data_interpolated_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    #
    #    movingaverage on raw data
    #
    all_raw_data_movingaverage       = yatt.smooth.movingaverage(all_raw_data_datacube, 51)
    all_raw_data_linearinterpolation = yatt.smooth.linearinterpolation(numpy.copy(all_raw_data_datacube))
    all_raw_data_movingaverage_of_linearinterpolation = yatt.smooth.movingaverage(all_raw_data_linearinterpolation, 51)

    #
    #    remove outliers
    #
    all_outliers_removed_datacube         = yatt.smooth.flaglocalminima(numpy.copy(all_raw_data_datacube), maxdip, maxdif, maxgap=maxgap, maxpasses=extremapasses)
    all_outliers_removed_weighttypescube  = yatt.smooth.makeweighttypescube(all_outliers_removed_datacube, aboutequalepsilon)
    all_outliers_removed_swetsweightscube = yatt.smooth.makesimpleweightscube(all_outliers_removed_weighttypescube, weightvalues=yatt.smooth.defaultswetsweightvalues)
    #
    #    whittaker on data without outliers
    #
    all_outliers_removed_whitcube = yatt.smooth.whittaker_second_differences(lmbda, all_outliers_removed_datacube, None, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    #
    #    swets  on data without outliers
    #
    all_outliers_removed_swetscube = yatt.smooth.swets(regressionwindow, combinationwindow, all_outliers_removed_datacube, all_outliers_removed_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    #
    #    weighted whittaker on data without outliers
    #
    all_outliers_removed_weightedwhitcube = yatt.smooth.whittaker_second_differences(lmbda, all_outliers_removed_datacube, all_outliers_removed_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    #
    #    linear interpolation + swets on data without outliers
    #
    all_outliers_removed_interpolated_datacube         = yatt.smooth.linearinterpolation(numpy.copy(all_outliers_removed_datacube))
    all_outliers_removed_interpolated_weighttypescube  = yatt.smooth.makeweighttypescube(all_outliers_removed_interpolated_datacube, aboutequalepsilon)
    all_outliers_removed_interpolated_swetsweightscube = yatt.smooth.makesimpleweightscube(all_outliers_removed_interpolated_weighttypescube, weightvalues=yatt.smooth.defaultswetsweightvalues)
    all_outliers_removed_interpolated_swetscube        = yatt.smooth.swets(regressionwindow, combinationwindow, all_outliers_removed_interpolated_datacube, all_outliers_removed_interpolated_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    #
    #    movingaverage on data without outliers
    #
    all_outliers_removed_movingaverage       = yatt.smooth.movingaverage(all_outliers_removed_datacube, 51)
    all_outliers_removed_linearinterpolation = yatt.smooth.linearinterpolation(numpy.copy(all_outliers_removed_datacube))
    all_outliers_removed_movingaverage_of_linearinterpolation = yatt.smooth.movingaverage(all_outliers_removed_linearinterpolation, 51)



    #
    #    perfect data
    #
    perfect_raw_data_datacube         = yatt.smooth.makedatacube(profile_avarage_pixels_fapar_perfect_data, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    perfect_raw_data_weighttypescube  = yatt.smooth.makeweighttypescube(perfect_raw_data_datacube, aboutequalepsilon)
    perfect_raw_data_swetsweightscube = yatt.smooth.makesimpleweightscube(perfect_raw_data_weighttypescube, weightvalues=yatt.smooth.defaultswetsweightvalues)
    #
    #    whittaker on perfect data
    #
    perfect_raw_data_whitcube = yatt.smooth.whittaker_second_differences(lmbda, perfect_raw_data_datacube, None, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    #
    #    swets on perfect data
    #
    perfect_raw_data_swetscube = yatt.smooth.swets(regressionwindow, combinationwindow, perfect_raw_data_datacube, perfect_raw_data_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    #
    #    weighted whittaker on perfect data
    #
    perfect_raw_data_weightedwhitcube = yatt.smooth.whittaker_second_differences(lmbda, perfect_raw_data_datacube, perfect_raw_data_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    #
    #    linear interpolation + swets on raw perfect data
    #
    perfect_raw_data_interpolated_datacube         = yatt.smooth.linearinterpolation(numpy.copy(perfect_raw_data_datacube))
    perfect_raw_data_interpolated_weighttypescube  = yatt.smooth.makeweighttypescube(perfect_raw_data_interpolated_datacube, aboutequalepsilon)
    perfect_raw_data_interpolated_swetsweightscube = yatt.smooth.makesimpleweightscube(perfect_raw_data_interpolated_weighttypescube, weightvalues=yatt.smooth.defaultswetsweightvalues)
    perfect_raw_data_interpolated_swetscube        = yatt.smooth.swets(regressionwindow, combinationwindow, perfect_raw_data_interpolated_datacube, perfect_raw_data_interpolated_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    #
    #    movingaverage on raw perfect data
    #
    perfect_raw_data_movingaverage       = yatt.smooth.movingaverage(perfect_raw_data_datacube, 51)
    perfect_raw_data_linearinterpolation = yatt.smooth.linearinterpolation(numpy.copy(perfect_raw_data_datacube))
    perfect_raw_data_movingaverage_of_linearinterpolation = yatt.smooth.movingaverage(perfect_raw_data_linearinterpolation, 51)

    #
    #    remove outliers
    #
    perfect_outliers_removed_datacube = yatt.smooth.flaglocalminima(numpy.copy(perfect_raw_data_datacube), maxdip, maxdif, maxgap=maxgap, maxpasses=extremapasses)
    perfect_outliers_removed_weighttypescube  = yatt.smooth.makeweighttypescube(perfect_outliers_removed_datacube, aboutequalepsilon)
    perfect_outliers_removed_swetsweightscube = yatt.smooth.makesimpleweightscube(perfect_outliers_removed_weighttypescube, weightvalues=yatt.smooth.defaultswetsweightvalues)
    #
    #    whittaker on perfect data without outliers
    #
    perfect_outliers_removed_whitcube = yatt.smooth.whittaker_second_differences(lmbda, perfect_outliers_removed_datacube, None, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    #
    #    swets  on perfect data without outliers
    #
    perfect_outliers_removed_swetscube = yatt.smooth.swets(regressionwindow, combinationwindow, perfect_outliers_removed_datacube, perfect_outliers_removed_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    #
    #    weighted whittaker on perfect data without outliers
    #
    perfect_outliers_removed_weightedwhitcube = yatt.smooth.whittaker_second_differences(lmbda, perfect_outliers_removed_datacube, perfect_outliers_removed_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    #
    #    linear interpolation + swets on perfect data without outliers
    #
    perfect_outliers_removed_interpolated_datacube         = yatt.smooth.linearinterpolation(numpy.copy(perfect_outliers_removed_datacube))
    perfect_outliers_removed_interpolated_weighttypescube  = yatt.smooth.makeweighttypescube(perfect_outliers_removed_interpolated_datacube, aboutequalepsilon)
    perfect_outliers_removed_interpolated_swetsweightscube = yatt.smooth.makesimpleweightscube(perfect_outliers_removed_interpolated_weighttypescube, weightvalues=yatt.smooth.defaultswetsweightvalues)
    perfect_outliers_removed_interpolated_swetscube        = yatt.smooth.swets(regressionwindow, combinationwindow, perfect_outliers_removed_interpolated_datacube, perfect_outliers_removed_interpolated_swetsweightscube, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    #
    #    movingaverage  on perfect data without outliers
    #
    perfect_outliers_removed_movingaverage       = yatt.smooth.movingaverage(perfect_outliers_removed_datacube, 51)
    perfect_outliers_removed_linearinterpolation = yatt.smooth.linearinterpolation(numpy.copy(perfect_outliers_removed_datacube))
    perfect_outliers_removed_movingaverage_of_linearinterpolation = yatt.smooth.movingaverage(perfect_outliers_removed_linearinterpolation, 51)



    #
    #
    #
    rows = 2
    cols = 3
    subplots = numpy.empty( (rows,cols), dtype=object )

    figure = matplotlib.pyplot.figure(figsize=(16,6))
    for irow in range(rows):
        for icol in range(cols):
            subplots[irow, icol] = figure.add_subplot(rows, cols, 1 + icol + irow * cols)

    row = 0; col = 0
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_raw_data_whitcube,                  'Red'    ); line.set_label('whit.')  
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_raw_data_weightedwhitcube,          'Magenta'); line.set_label('whit.-weights')    
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_outliers_removed_whitcube,          'Green'  ); line.set_label('whit. no outliers')    
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_outliers_removed_weightedwhitcube,  'Blue'   ); line.set_label('whit.-weights no outliers')   
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_raw_data_datacube,                  'ro' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_outliers_removed_datacube,          'go' )  
    subplots[row, col].set_title("whittaker - all observations")
    subplots[row, col].legend()

    row = 1; col = 0
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_raw_data_whitcube,                  'Red' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_raw_data_weightedwhitcube,          'Magenta' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_outliers_removed_whitcube,          'Green' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_outliers_removed_weightedwhitcube,  'Blue' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_raw_data_datacube,                  'ro' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_outliers_removed_datacube,          'go' )  
    subplots[row, col].set_title("whittaker - 'perfect' observations")

    row = 0; col = 1
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_raw_data_swetscube,                     'Red'    ); line.set_label('swets')    
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_raw_data_interpolated_swetscube,        'Magenta'); line.set_label('interp-swets')     
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_outliers_removed_swetscube,             'Green'  ); line.set_label('swets no outliers')     
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_outliers_removed_interpolated_swetscube,'Blue'   ); line.set_label('interp-swets no outliers')   
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_raw_data_datacube,                      'ro' )
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_outliers_removed_datacube,              'go' )  
    subplots[row, col].set_title("swets - all observations")
    subplots[row, col].legend()

    row = 1; col = 1
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_raw_data_swetscube,                     'Red' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_raw_data_interpolated_swetscube,        'Magenta' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_outliers_removed_swetscube,             'Green' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_outliers_removed_interpolated_swetscube,'Blue' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_raw_data_datacube,                      'ro' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_outliers_removed_datacube,              'go' )  
    subplots[row, col].set_title("swets - 'perfect' observations")

    row = 0; col = 2
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_raw_data_movingaverage,                                'Red'    ); line.set_label('mov avg')    
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_raw_data_movingaverage_of_linearinterpolation,         'Magenta'); line.set_label('interp-mov avg')     
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_outliers_removed_movingaverage,                        'Green'  ); line.set_label('no outliers mov avg')     
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_outliers_removed_movingaverage_of_linearinterpolation , 'Blue'  ); line.set_label('no outliers interp-mov avg')   
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_raw_data_datacube,         'ro' )
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_outliers_removed_datacube, 'go' )  
    subplots[row, col].set_title("moving average - all observations")
    subplots[row, col].legend()

    row = 1; col = 2
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_raw_data_movingaverage,                                'Red' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_raw_data_movingaverage_of_linearinterpolation,         'Magenta' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_outliers_removed_movingaverage,                        'Green' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_outliers_removed_movingaverage_of_linearinterpolation, 'Blue' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_raw_data_datacube,         'ro' )  
    subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), perfect_outliers_removed_datacube, 'go' )  
    subplots[row, col].set_title("moving average - 'perfect' observations")

    for irow in range(rows):
        for icol in range(cols):
            subplots[irow, icol].xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d/%m'))
            subplots[irow, icol].set_ylim(-5, 205)
            for tick in subplots[irow, icol].get_xticklabels(): tick.set_rotation(45)

    matplotlib.pyplot.subplots_adjust(left = 0.02, right = 0.98, wspace=0.1, hspace=0.4)
    matplotlib.pyplot.suptitle("whittaker vs swets - all observations vs 'good' observations" )

    if bmakepng:
        matplotlib.pyplot.savefig(os.path.join(demo.testdata.sztestdatarootdirectory, os.path.basename(inputdirectory) + "_Smoothed_Profiles.png"), dpi=300)
    else:
        matplotlib.pyplot.show()

#
#
#
if __name__ == '__main__':
    #
    #
    #
    bmakepng = False
    doprofiles( os.path.join(demo.testdata.sztestdatarootdirectory, "2-AVy-ofdls9bS8_4_3GLH"  ), bmakepng)
    doprofiles( os.path.join(demo.testdata.sztestdatarootdirectory, "29-AV0TcoCXZjsFpiOBA3gL" ), bmakepng)
    doprofiles( os.path.join(demo.testdata.sztestdatarootdirectory, "190-AVzO_BSZZjsFpiOBRYcR"), bmakepng)

