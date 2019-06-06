#
#
#
import os
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
    verbose = True

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
        fapar_gdaldataset = osgeo.gdal.Open(os.path.join(inputdirectory,szFAPARfilenames[0]))
        cloud_gdaldataset = osgeo.gdal.Open(os.path.join(inputdirectory,szCLOUDfilenames[0]))
        shadw_gdaldataset = osgeo.gdal.Open(os.path.join(inputdirectory,szSHADWfilenames[0]))
        scene_gdaldataset = osgeo.gdal.Open(os.path.join(inputdirectory,szSCENEfilenames[0]))

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
        #total_pixels_fapar_perfect_data  = fapar_numpyparray[(fapar_numpyparray <= demo.maximumdatavalue) & (scene_numpyparray < 8) & (scene_numpyparray > 3)].size    
        total_pixels_fapar_perfect_data  = fapar_numpyparray[(fapar_numpyparray <= demo.testdata.maximumdatavalue) & (cloud_numpyparray == 0) & (shadw_numpyparray == 0) & (scene_numpyparray < 8) & (scene_numpyparray > 3)].size    

        if verbose:
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
    #    remove outliers and simple smooth
    #
    maxdip        = 0.01 * 200 
    maxdif        = 0.1  * 200 
    maxgap        = None
    extremapasses = 999
    #
    #    whittaker parameters
    #
    lmbda        = 5
    passes       = 3
    dokeepmaxima = True
    #
    #
    #
    all_raw_data_datacube         = yatt.smooth.makedatacube(profile_avarage_pixels_fapar_data, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    pft_raw_data_datacube         = yatt.smooth.makedatacube(profile_avarage_pixels_fapar_perfect_data, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue)
    all_outliers_removed_datacube = yatt.smooth.flaglocalminima(numpy.copy(all_raw_data_datacube), maxdip, maxdif, maxgap=maxgap, maxpasses=extremapasses)
    pft_outliers_removed_datacube = yatt.smooth.flaglocalminima(numpy.copy(pft_raw_data_datacube), maxdip, maxdif, maxgap=maxgap, maxpasses=extremapasses)
    all_outliers_removed_whitcube = yatt.smooth.whittaker_second_differences(lmbda, all_outliers_removed_datacube, None, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    pft_outliers_removed_whitcube = yatt.smooth.whittaker_second_differences(lmbda, pft_outliers_removed_datacube, None, minimumdatavalue=demo.testdata.minimumdatavalue, maximumdatavalue=demo.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)

    #
    #    monthly composites
    #
    compostitedates  = []
    all_pixels_compostitemaximum = []
    all_pixels_compostiteminimum = []
    all_pixels_compostiteaverage = []
    pft_pixels_compostitemaximum = []
    pft_pixels_compostiteminimum = []
    pft_pixels_compostiteaverage = []
    smth_all_pixels_compostitemaximum = []
    smth_all_pixels_compostiteminimum = []
    smth_all_pixels_compostiteaverage = []
    smth_pft_pixels_compostitemaximum = []
    smth_pft_pixels_compostiteminimum = []
    smth_pft_pixels_compostiteaverage = []

    icurrent_year, icurrent_month, _ = yutils.dutils.iyear_imonth_iday_from_yyyymmdd(profile_zedates[0])

    iIdxFirstInCurrMonth  = 0
    iIdxFirstInNextMonth  = 0

    for iIdx in range(len(profile_zedates)):

        date_yyyymmdd    = profile_zedates[iIdx]
        iyear, imonth, _ = yutils.dutils.iyear_imonth_iday_from_yyyymmdd(date_yyyymmdd)

        if imonth == icurrent_month and iyear == icurrent_year:
            iIdxFirstInNextMonth = iIdx + 1
            if iIdxFirstInNextMonth < len(profile_zedates) : continue

        compostitedates.append(yutils.dutils.yyyymmdd_from_iyear_imonth_iday(icurrent_year, icurrent_month, 15)) # approximate center of month  

        if verbose: print ("month %s - [(%s) %s - (%s) %s[ - %s days" % (yutils.dutils.yyyymm_from_iyear_imonth(icurrent_year, icurrent_month), iIdxFirstInCurrMonth, profile_zedates[iIdxFirstInCurrMonth], iIdxFirstInNextMonth, profile_zedates[iIdxFirstInNextMonth], len(profile_avarage_pixels_fapar_data[iIdxFirstInCurrMonth: iIdxFirstInNextMonth])))

        all_pixels_profile = all_raw_data_datacube[iIdxFirstInCurrMonth: iIdxFirstInNextMonth]
        all_pixels_maximum = yatt.smooth.compostitemaximum(all_pixels_profile)
        all_pixels_minimum = yatt.smooth.compostiteminimum(all_pixels_profile)
        all_pixels_average = yatt.smooth.compostiteaverage(all_pixels_profile)  
        all_pixels_compostitemaximum.append(all_pixels_maximum) 
        all_pixels_compostiteminimum.append(all_pixels_minimum) 
        all_pixels_compostiteaverage.append(all_pixels_average) 
        if verbose: print ("                       all pix: obs(%2s) min(% 7.4f) avg(% 7.4f) max(% 7.4f)" % (sum( (not numpy.isnan(val)) for val in all_pixels_profile), all_pixels_minimum, all_pixels_average, all_pixels_maximum))

        pft_pixels_profile = pft_raw_data_datacube[iIdxFirstInCurrMonth: iIdxFirstInNextMonth]
        pft_pixels_maximum = yatt.smooth.compostitemaximum(pft_pixels_profile)
        pft_pixels_minimum = yatt.smooth.compostiteminimum(pft_pixels_profile)
        pft_pixels_average = yatt.smooth.compostiteaverage(pft_pixels_profile)  
        pft_pixels_compostitemaximum.append(pft_pixels_maximum) 
        pft_pixels_compostiteminimum.append(pft_pixels_minimum) 
        pft_pixels_compostiteaverage.append(pft_pixels_average) 
        if verbose: print ("                   perfect pix: obs(%2s) min(% 7.4f) avg(% 7.4f) max(% 7.4f)" % (sum( (not numpy.isnan(val)) for val in pft_pixels_profile), pft_pixels_minimum, pft_pixels_average, pft_pixels_maximum))

        smth_all_pixels_profile = all_outliers_removed_whitcube[iIdxFirstInCurrMonth: iIdxFirstInNextMonth]
        smth_all_pixels_maximum = yatt.smooth.compostitemaximum(smth_all_pixels_profile)
        smth_all_pixels_minimum = yatt.smooth.compostiteminimum(smth_all_pixels_profile)
        smth_all_pixels_average = yatt.smooth.compostiteaverage(smth_all_pixels_profile)  
        smth_all_pixels_compostitemaximum.append(smth_all_pixels_maximum) 
        smth_all_pixels_compostiteminimum.append(smth_all_pixels_minimum) 
        smth_all_pixels_compostiteaverage.append(smth_all_pixels_average) 
        if verbose: print ("              smoothed all pix: obs(%2s) min(% 7.4f) avg(% 7.4f) max(% 7.4f)" % (sum( (not numpy.isnan(val)) for val in smth_all_pixels_profile), smth_all_pixels_minimum, smth_all_pixels_average, smth_all_pixels_maximum))

        smth_pft_pixels_profile = pft_outliers_removed_whitcube[iIdxFirstInCurrMonth: iIdxFirstInNextMonth]
        smth_pft_pixels_maximum = yatt.smooth.compostitemaximum(smth_pft_pixels_profile)
        smth_pft_pixels_minimum = yatt.smooth.compostiteminimum(smth_pft_pixels_profile)
        smth_pft_pixels_average = yatt.smooth.compostiteaverage(smth_pft_pixels_profile)  
        smth_pft_pixels_compostitemaximum.append(smth_pft_pixels_maximum) 
        smth_pft_pixels_compostiteminimum.append(smth_pft_pixels_minimum) 
        smth_pft_pixels_compostiteaverage.append(smth_pft_pixels_average) 
        if verbose: print ("          smoothed perfect pix: obs(%2s) min(% 7.4f) avg(% 7.4f) max(% 7.4f)" % (sum( (not numpy.isnan(val)) for val in smth_pft_pixels_profile), smth_pft_pixels_minimum, smth_pft_pixels_average, smth_pft_pixels_maximum))

        if verbose: print("")

        icurrent_month       = imonth
        icurrent_year        = iyear
        iIdxFirstInCurrMonth = iIdxFirstInNextMonth

    #
    #
    #
    if True:
        #
        #
        #
        rows = 2
        cols = 2
        subplots = numpy.empty( (rows,cols), dtype=object )

        figure = matplotlib.pyplot.figure(figsize=(16,6))
        for irow in range(rows):
            for icol in range(cols):
                subplots[irow, icol] = figure.add_subplot(rows, cols, 1 + icol + irow * cols)

        row = 0; col = 0
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), all_pixels_compostitemaximum,          'bo' ); #line.set_label('max.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), all_pixels_compostitemaximum,          'b'  );
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), all_pixels_compostiteaverage,          'mo' ); #line.set_label('avg')    
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), all_pixels_compostiteaverage,          'm'  );
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), all_pixels_compostiteminimum,          'go' ); #line.set_label('min')    
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), all_pixels_compostiteminimum,          'g'  );
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), profile_avarage_pixels_fapar_data,     'ro' )  
        subplots[row, col].set_title("all observations")
        #subplots[row, col].legend()

        row = 1; col = 0
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), pft_pixels_compostitemaximum,               'bo' )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), pft_pixels_compostitemaximum,               'b'  )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), pft_pixels_compostiteaverage,               'mo' )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), pft_pixels_compostiteaverage,               'm'  )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), pft_pixels_compostiteminimum,               'go' )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), pft_pixels_compostiteminimum,               'g'  )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), profile_avarage_pixels_fapar_perfect_data,  'ro' )  
        subplots[row, col].set_title("'perfect' observations")

        row = 0; col = 1
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_all_pixels_compostitemaximum,          'bo' ); line.set_label('max.')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_all_pixels_compostitemaximum,          'b'  );
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_all_pixels_compostiteaverage,          'mo' ); line.set_label('avg')    
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_all_pixels_compostiteaverage,          'm'  );
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_all_pixels_compostiteminimum,          'go' ); line.set_label('min')    
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_all_pixels_compostiteminimum,          'g'  );
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), profile_avarage_pixels_fapar_data,          'k+' ); line.set_label('outlier')  
        line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), all_outliers_removed_datacube,              'ro' )  
        subplots[row, col].set_title("all observations- smoothed")
        subplots[row, col].legend()

        row = 1; col = 1
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_pft_pixels_compostitemaximum,               'bo' )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_pft_pixels_compostitemaximum,               'b'  )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_pft_pixels_compostiteaverage,               'mo' )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_pft_pixels_compostiteaverage,               'm'  )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_pft_pixels_compostiteminimum,               'go' )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (compostitedates), smth_pft_pixels_compostiteminimum,               'g'  )
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), profile_avarage_pixels_fapar_perfect_data,       'k+' )  
        subplots[row, col].plot_date(matplotlib.dates.datestr2num (profile_zedates), pft_outliers_removed_datacube,                   'ro' )  
        subplots[row, col].set_title("'perfect' observations - smoothed")
        for irow in range(rows):
            for icol in range(cols):
                subplots[irow, icol].xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d/%m'))
                subplots[irow, icol].set_ylim(-5, 205)
                subplots[irow, icol].set_xlim(matplotlib.dates.datestr2num (profile_zedates[0]), matplotlib.dates.datestr2num (profile_zedates[-1]))
                for tick in subplots[irow, icol].get_xticklabels(): tick.set_rotation(45)

        matplotlib.pyplot.subplots_adjust(wspace=0.1, hspace=0.4)
        matplotlib.pyplot.suptitle("%s - Monthly composite - all observations vs 'good' observations" % (os.path.basename(inputdirectory)))
        if bmakepng:
            matplotlib.pyplot.savefig(os.path.join(demo.testdata.sztestdatarootdirectory, os.path.basename(inputdirectory) + "_S30_composite" + ".png"), dpi=300)
        else :
            matplotlib.pyplot.show()
        matplotlib.pyplot.close('all')        


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
