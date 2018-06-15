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
import tests.testdata

#
#
#
def dorasters(inputdirectory, bdoperfectpixels = False, bmakepng = False, bmakeenvi = False):
    #
    #
    #
    doverbose       = True

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

    #
    #
    #
    zedates               = []
    zerasters             = []
    iIdx                  = - 1
    numberofobservations  = 0

    ref_geotransform      = None
    ref_projection        = None
    ref_rasterxsize       = None
    ref_rasterysize       = None

    #
    #
    #
    for date_yyyymmdd in yutils.dutils.g_yyyymmdd_interval(yyyymmddfirst, yyyymmddlast):

        zedates.append(date_yyyymmdd)
        zerasters.append(None)
        iIdx += 1

        ptFAPARpattern = tests.testdata.makefilenamepattern(date_yyyymmdd, "FAPAR_10M")
        ptCLOUDpattern = tests.testdata.makefilenamepattern(date_yyyymmdd, "CLOUDMASK_10M")
        ptSHADWpattern = tests.testdata.makefilenamepattern(date_yyyymmdd, "SHADOWMASK_10M")
        ptSCENEpattern = tests.testdata.makefilenamepattern(date_yyyymmdd, "SCENECLASSIFICATION_10M")

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
        #    just once, for later use - one might be tempted to check successive files for consistency
        #
        if ref_rasterxsize is None:
            ref_rasterxsize  = fapar_gdaldataset.RasterXSize
            ref_rasterysize  = fapar_gdaldataset.RasterYSize
            ref_geotransform = fapar_gdaldataset.GetGeoTransform()
            ref_projection   = fapar_gdaldataset.GetProjection()

        #
        #
        #
        fapar_numpyparray = fapar_gdaldataset.ReadAsArray()
        cloud_numpyparray = cloud_gdaldataset.ReadAsArray()
        shadw_numpyparray = shadw_gdaldataset.ReadAsArray()
        scene_numpyparray = scene_gdaldataset.ReadAsArray()

        #
        #    some statistics
        #    - it is hard to find out what exactly is flagged as no data in fapar. (probably cloudmask and shadowmask. but what about snow...)
        #    - using the scene classification requires converting to 10meter resolution
        #    - scene classification "low probability clouds" seems to have problems; some fields sometimes match exactly the low probability clouds? (hence, reluctantly we allow scenes 4,5,6 AND 7)
        #
        total_pixels_in_roi              = fapar_numpyparray.size
        total_pixels_as_cloud            = cloud_numpyparray[cloud_numpyparray != 0].size
        total_pixels_as_shadw            = shadw_numpyparray[shadw_numpyparray != 0].size
        total_pixels_as_nodata           = fapar_numpyparray[fapar_numpyparray > tests.testdata.maximumdatavalue].size

        total_pixels_fapar_data          = fapar_numpyparray[(fapar_numpyparray <= tests.testdata.maximumdatavalue)].size
        total_pixels_fapar_unmasked_data = fapar_numpyparray[(fapar_numpyparray <= tests.testdata.maximumdatavalue) & (cloud_numpyparray == 0) & (shadw_numpyparray == 0)].size
        #
        #    we'd prefer (scene_numpyparray < 7) but we'll allow 'low probability' clouds,
        #    since in some cases they seem to match our field exactly, which seems to be some bug
        #
        #total_pixels_fapar_perfect_data  = fapar_numpyparray[(fapar_numpyparray <= tests.testdata.maximumdatavalue) & (scene_numpyparray < 8) & (scene_numpyparray > 3)].size    
        #
        #    actually, at the moment CLOUDMASK_10M and SHADOWMASK_10M are burned 
        #    in FAPAR_10M as no-data but who knows what happens in next version
        #
        total_pixels_fapar_perfect_data  = fapar_numpyparray[(fapar_numpyparray <= tests.testdata.maximumdatavalue) & (cloud_numpyparray == 0) & (shadw_numpyparray == 0) & (scene_numpyparray < 8) & (scene_numpyparray > 3)].size    
        #
        #
        #
        if bdoperfectpixels:
            #
            #    perfect pixels only
            #
            if 0 < total_pixels_fapar_perfect_data:

                numberofobservations += 1

                zeraster = numpy.copy(fapar_numpyparray)

                zeraster[ (fapar_numpyparray > tests.testdata.maximumdatavalue) | (cloud_numpyparray ==1) | (shadw_numpyparray==1) | (scene_numpyparray >= 8) | (scene_numpyparray <= 3)] = tests.testdata.nodatavalue
                zerasters[iIdx] = zeraster
        else:
            #
            #    all data pixels (at the moment total_pixels_fapar_data == total_pixels_fapar_unmasked_data)
            #
            if 0 < total_pixels_fapar_unmasked_data:

                numberofobservations += 1

                zeraster = numpy.copy(fapar_numpyparray)

                zeraster[ (fapar_numpyparray > tests.testdata.maximumdatavalue) | (cloud_numpyparray ==1) | (shadw_numpyparray==1)] = tests.testdata.nodatavalue
                zerasters[iIdx] = zeraster

        if doverbose:
            print ("observation %s:" % (date_yyyymmdd))
            print ("total pixels in roi          %s" % (total_pixels_in_roi))
            print ("total fapar as no data       %s" % (total_pixels_as_nodata))
            print ("total fapar as data          %s" % (total_pixels_fapar_data))
            print ("total pixels as cloud        %s" % (total_pixels_as_cloud))
            print ("total pixels as shadow       %s" % (total_pixels_as_shadw))
            print ("total fapar as unmasked data %s" % (total_pixels_fapar_unmasked_data))
            print ("sum cloud and shadow         %s" % (total_pixels_as_cloud + total_pixels_as_shadw))
            print ("total fapar perfect pixels   %s" % (total_pixels_fapar_perfect_data))
            print ("")

    print ("number of dates: %s - number of observations: %s" % (iIdx + 1, numberofobservations))
    print ("")



    #
    #
    #

    ###########################################################################
    #
    #    make composites
    #
    ###########################################################################

    #
    #
    #

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
    #    raw rasters and smoothed rasters
    #
    raw_data_datacube         = yatt.smooth.makedatacube(zerasters, minimumdatavalue=tests.testdata.minimumdatavalue, maximumdatavalue=tests.testdata.maximumdatavalue)
    outliers_removed_datacube = yatt.smooth.flaglocalminima(numpy.copy(raw_data_datacube), maxdip, maxdif, maxgap=maxgap, maxpasses=extremapasses)
    outliers_removed_whitcube = yatt.smooth.whittaker_second_differences(lmbda, outliers_removed_datacube, None, minimumdatavalue=tests.testdata.minimumdatavalue, maximumdatavalue=tests.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)

    #
    #    monthly composites
    #
    compostitedates  = []
    raw_compostitemaximum = []
    raw_compostiteminimum = []
    raw_compostiteaverage = []
    smt_compostitemaximum = []
    smt_compostiteminimum = []
    smt_compostiteaverage = []

    icurrent_year, icurrent_month, _ = yutils.dutils.iyear_imonth_iday_from_yyyymmdd(zedates[0])

    iIdxFirstInCurrMonth  = 0
    iIdxFirstInNextMonth  = 0

    for iIdx in range(len(zedates)):

        date_yyyymmdd    = zedates[iIdx]
        iyear, imonth, _ = yutils.dutils.iyear_imonth_iday_from_yyyymmdd(date_yyyymmdd)

        if imonth == icurrent_month and iyear == icurrent_year:
            iIdxFirstInNextMonth = iIdx + 1
            if iIdxFirstInNextMonth < len(zedates) : continue

        compostitedates.append(yutils.dutils.yyyymmdd_from_iyear_imonth_iday(icurrent_year, icurrent_month, 1)) # Hermans S30 naming convention 

        raw_rasters_profile = raw_data_datacube[iIdxFirstInCurrMonth: iIdxFirstInNextMonth]
        raw_rasters_maximum = yatt.smooth.compostitemaximum(raw_rasters_profile)
        raw_rasters_minimum = yatt.smooth.compostiteminimum(raw_rasters_profile)
        raw_rasters_average = yatt.smooth.compostiteaverage(raw_rasters_profile)  
        raw_compostitemaximum.append(raw_rasters_maximum) 
        raw_compostiteminimum.append(raw_rasters_minimum) 
        raw_compostiteaverage.append(raw_rasters_average) 

        smt_rasters_profile = outliers_removed_whitcube[iIdxFirstInCurrMonth: iIdxFirstInNextMonth]
        smt_rasters_maximum = yatt.smooth.compostitemaximum(smt_rasters_profile)
        smt_rasters_minimum = yatt.smooth.compostiteminimum(smt_rasters_profile)
        smt_rasters_average = yatt.smooth.compostiteaverage(smt_rasters_profile)  
        smt_compostitemaximum.append(smt_rasters_maximum) 
        smt_compostiteminimum.append(smt_rasters_minimum) 
        smt_compostiteaverage.append(smt_rasters_average) 

        icurrent_month       = imonth
        icurrent_year        = iyear
        iIdxFirstInCurrMonth = iIdxFirstInNextMonth

    #
    #    monthly envi images
    #
    if bmakeenvi:
        #
        #
        #
        #zeresults = raw_compostitemaximum
        #zeresults = raw_compostiteaverage
        #zeresults = raw_compostiteminimum
        zeresults = smt_compostitemaximum
        #zeresults = smt_compostiteaverage
        #zeresults = smt_compostiteminimum
        #
        #
        #
        do_envi_png = False
        #
        #
        #
        smoothedraster = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=numpy.uint8)
        notnanraster   = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=bool)

        for iIdx in range(len(compostitedates)):

            if not (~numpy.isnan(zeresults[iIdx])).any(): continue

            smoothedraster[:] = tests.testdata.nodatavalue
            notnanraster[:] = ~numpy.isnan(zeresults[iIdx])
            smoothedraster[notnanraster] = numpy.where(zeresults[iIdx][notnanraster]>tests.testdata.maximumdatavalue, tests.testdata.maximumdatavalue, numpy.rint(zeresults[iIdx][notnanraster])) 

            envi_name = os.path.join(tests.testdata.sztestdatarootdirectory,os.path.basename(inputdirectory) + "_S30_composite_%s.img"%(zedates[iIdx]))
            envi_gdaldataset = osgeo.gdal.GetDriverByName("ENVI").Create(envi_name, ref_rasterxsize, ref_rasterysize, 1, osgeo.gdalconst.GDT_Byte)
            envi_gdaldataset.SetGeoTransform(ref_geotransform)
            envi_gdaldataset.SetProjection(ref_projection)
            envi_gdaldataset.GetRasterBand(1).WriteArray(smoothedraster)

            if do_envi_png :
                png_name= os.path.join(tests.testdata.sztestdatarootdirectory,os.path.basename(inputdirectory) + "_S30_composite_%s.png"%(zedates[iIdx]))
                osgeo.gdal.GetDriverByName('PNG').CreateCopy(png_name, envi_gdaldataset)

    #
    #    raw and smoothed S30
    #
    raw_max_raster = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=numpy.uint8)
    raw_max_notnan = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=bool)
    raw_avg_raster = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=numpy.uint8)
    raw_avg_notnan = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=bool)
    raw_min_raster = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=numpy.uint8)
    raw_min_notnan = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=bool)

    smt_max_raster = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=numpy.uint8)
    smt_max_notnan = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=bool)
    smt_avg_raster = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=numpy.uint8)
    smt_avg_notnan = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=bool)
    smt_min_raster = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=numpy.uint8)
    smt_min_notnan = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=bool)

    for iIdx in range(len(compostitedates)):

        #
        #
        #
        raw_max_raster[:] = tests.testdata.nodatavalue
        raw_max_notnan[:] =  ~numpy.isnan(raw_compostitemaximum[iIdx])
        raw_max_raster[raw_max_notnan] = numpy.where(raw_compostitemaximum[iIdx][raw_max_notnan]>tests.testdata.maximumdatavalue, tests.testdata.maximumdatavalue, numpy.rint(raw_compostitemaximum[iIdx][raw_max_notnan]))

        raw_avg_raster[:] = tests.testdata.nodatavalue
        raw_avg_notnan[:] =  ~numpy.isnan(raw_compostiteaverage[iIdx])
        raw_avg_raster[raw_avg_notnan] = numpy.where(raw_compostiteaverage[iIdx][raw_avg_notnan]>tests.testdata.maximumdatavalue, tests.testdata.maximumdatavalue, numpy.rint(raw_compostiteaverage[iIdx][raw_avg_notnan]))

        raw_min_raster[:] = tests.testdata.nodatavalue
        raw_min_notnan[:] =  ~numpy.isnan(raw_compostiteminimum[iIdx])
        raw_min_raster[raw_min_notnan] = numpy.where(raw_compostiteminimum[iIdx][raw_min_notnan]>tests.testdata.maximumdatavalue, tests.testdata.maximumdatavalue, numpy.rint(raw_compostiteminimum[iIdx][raw_min_notnan]))
        #
        #    smoothed raster has (float) values  0-200 + nan's 
        #
        smt_max_raster[:] = tests.testdata.nodatavalue
        smt_max_notnan[:] =  ~numpy.isnan(smt_compostitemaximum[iIdx])
        smt_max_raster[smt_max_notnan] = numpy.where(smt_compostitemaximum[iIdx][smt_max_notnan]>tests.testdata.maximumdatavalue, tests.testdata.maximumdatavalue, numpy.rint(smt_compostitemaximum[iIdx][smt_max_notnan]))

        smt_avg_raster[:] = tests.testdata.nodatavalue
        smt_avg_notnan[:] =  ~numpy.isnan(smt_compostiteaverage[iIdx])
        smt_avg_raster[smt_avg_notnan] = numpy.where(smt_compostiteaverage[iIdx][smt_avg_notnan]>tests.testdata.maximumdatavalue, tests.testdata.maximumdatavalue, numpy.rint(smt_compostiteaverage[iIdx][smt_avg_notnan]))

        smt_min_raster[:] = tests.testdata.nodatavalue
        smt_min_notnan[:] =  ~numpy.isnan(smt_compostiteminimum[iIdx])
        smt_min_raster[smt_min_notnan] = numpy.where(smt_compostiteminimum[iIdx][smt_min_notnan]>tests.testdata.maximumdatavalue, tests.testdata.maximumdatavalue, numpy.rint(smt_compostiteminimum[iIdx][smt_min_notnan]))
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
        subplots[row, col].imshow(raw_max_raster.astype(float), norm=tests.testdata.faparnorm, cmap=tests.testdata.faparcolormap)
        subplots[row, col].set_title("raw data - max composite")
        row = 0; col = 1
        subplots[row, col].imshow(raw_avg_raster.astype(float), norm=tests.testdata.faparnorm, cmap=tests.testdata.faparcolormap)
        subplots[row, col].set_title("raw data - avg composite")
        row = 0; col = 2
        subplots[row, col].imshow(raw_min_raster.astype(float), norm=tests.testdata.faparnorm, cmap=tests.testdata.faparcolormap)
        subplots[row, col].set_title("raw data - min composite")

        row = 1; col = 0
        subplots[row, col].imshow(smt_max_raster.astype(float), norm=tests.testdata.faparnorm, cmap=tests.testdata.faparcolormap)
        subplots[row, col].set_title("smoothed data - max composite")
        row = 1; col = 1
        subplots[row, col].imshow(smt_avg_raster.astype(float), norm=tests.testdata.faparnorm, cmap=tests.testdata.faparcolormap)
        subplots[row, col].set_title("smoothed data - avg composite")
        row = 1; col = 2
        subplots[row, col].imshow(smt_min_raster.astype(float), norm=tests.testdata.faparnorm, cmap=tests.testdata.faparcolormap)
        subplots[row, col].set_title("smoothed data - min composite")


        matplotlib.pyplot.suptitle("Field: %s  - S30: %s" % (os.path.basename(inputdirectory), zedates[iIdx]) )
 
        if bmakepng:
            matplotlib.pyplot.savefig(os.path.join(tests.testdata.sztestdatarootdirectory, os.path.basename(inputdirectory) + "_S30_Raster_%s.png"%(compostitedates[iIdx])), dpi=300)
        else:
            matplotlib.pyplot.show()

        matplotlib.pyplot.close('all')

#
#
#
if __name__ == '__main__':
    #
    #
    #
    bdoperfectpixels = False
    bmakepng         = False
    bmakeenvi        = False

    dorasters( os.path.join(tests.testdata.sztestdatarootdirectory, "2-AVy-ofdls9bS8_4_3GLH"  ), bdoperfectpixels, bmakepng, bmakeenvi)
    dorasters( os.path.join(tests.testdata.sztestdatarootdirectory, "29-AV0TcoCXZjsFpiOBA3gL" ), bdoperfectpixels, bmakepng, bmakeenvi)
    dorasters( os.path.join(tests.testdata.sztestdatarootdirectory, "190-AVzO_BSZZjsFpiOBRYcR"), bdoperfectpixels, bmakepng, bmakeenvi)
