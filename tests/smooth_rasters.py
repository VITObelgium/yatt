#
#
#
import logging
import os
import re
import numpy
import osgeo.gdal
import matplotlib.pyplot
import yatt.smooth
import yatt.mask
import yutils.dutils
import tests.testdata

#
#
#
def dorasters(inputdirectory, bmakepng = False, bmakeenvi = False, busemask = False):
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
    zefapars              = []
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
        zefapars.append(None)
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
        #
        #
        zefapars[iIdx] = fapar_numpyparray

        #
        #
        #
        if not busemask:
            #
            #    original implementation - alternative using scene classification masks below 
            #
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
            zeraster = numpy.copy(fapar_numpyparray)
            zeraster[ (fapar_numpyparray > tests.testdata.maximumdatavalue) | (cloud_numpyparray ==1) | (shadw_numpyparray==1) | (scene_numpyparray >= 8) | (scene_numpyparray <= 3)] = tests.testdata.nodatavalue
            zerasters[iIdx] = zeraster

            if 0 < total_pixels_fapar_perfect_data:

                numberofobservations += 1
    
                if True:
                    print ("observation %s:" % (date_yyyymmdd))
                    print ("total pixels in roi          %s" % (total_pixels_in_roi))
                    print ("total fapar as no data       %s" % (total_pixels_as_nodata))
                    print ("total fapar as data          %s" % (total_pixels_fapar_data))
                    print ("total pixels as cloud        %s" % (total_pixels_as_cloud))
                    print ("total pixels as shadow       %s" % (total_pixels_as_shadw))
                    print ("total fapar as unmasked data %s" % (total_pixels_fapar_unmasked_data))
                    print ("sum cloud and shadow         %s" % (total_pixels_as_cloud + total_pixels_as_shadw))
                    print ("total fapar perfect pixels   %s" % (total_pixels_fapar_perfect_data))
                    print
    
            print ("number of dates: %s - number of observations: %s" % (iIdx + 1, numberofobservations))
            print ("")

        else:
            #
            #    alternative using scene classification masks 
            #
            print ("observation %s:" % (date_yyyymmdd))
            #
            #    Convolve2dClassificationMask
            #
            zerasters[iIdx] = yatt.mask.Convolve2dClassificationMask([
                yatt.mask.Convolve2dClassificationMask.ConditionSpec(3,  [4, 5, 7],     -0.90),
                yatt.mask.Convolve2dClassificationMask.ConditionSpec(11, [3, 8, 9, 10],  0.05)
                ]).mask(fapar_numpyparray, scene_numpyparray, maskedvalue=tests.testdata.nodatavalue, copy=True)

    #
    #    outlier parameters
    #
    maxdip            = 0.005 * 200 #0.01 * 200  (we're using fapar values as is: 0-200; no scaling)
    maxdif            = 0.05  * 200 #0.1  * 200
    maxgap            = None
    maxpasses         = 999
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
    #
    #
    raw_data_numpydatacube            = yatt.smooth.makedatacube(zerasters, minimumdatavalue=tests.testdata.minimumdatavalue, maximumdatavalue=tests.testdata.maximumdatavalue)
    outliers_removed_numpydatacube    = yatt.smooth.flaglocalminima(numpy.copy(raw_data_numpydatacube), maxdip, maxdif, maxgap=maxgap, maxpasses=maxpasses)
    outliers_removed_weighttypescube  = yatt.smooth.makeweighttypescube(outliers_removed_numpydatacube, aboutequalepsilon)
    outliers_removed_swetsweightscube = yatt.smooth.makesimpleweightscube(outliers_removed_weighttypescube, weightvalues=yatt.smooth.defaultswetsweightvalues)
    outliers_removed_whittakercube    = yatt.smooth.whittaker_second_differences(lmbda, outliers_removed_numpydatacube, outliers_removed_swetsweightscube, minimumdatavalue=tests.testdata.minimumdatavalue, maximumdatavalue=tests.testdata.maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)
    outliers_removed_swetscube        = yatt.smooth.swets(regressionwindow, combinationwindow, outliers_removed_numpydatacube, outliers_removed_swetsweightscube, minimumdatavalue=tests.testdata.minimumdatavalue, maximumdatavalue=tests.testdata.maximumdatavalue)

    #
    #
    #
    zewhitresults = numpy.copy(outliers_removed_whittakercube)
    zeswetresults = numpy.copy(outliers_removed_swetscube)

    #
    #    dekadal envi images
    #
    if bmakeenvi:
        #
        #
        #
        zeresults = zeswetresults
        #zeresults = zewhitresults
        #
        #
        #
        do_envi_png = False
        #
        #
        #
        smoothedraster = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=numpy.uint8)
        notnanraster   = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=bool)
        for iIdx in range(zeresults.shape[0]):

            if not (~numpy.isnan(zeresults[iIdx])).any(): continue

            if zedates[iIdx].endswith("01") or zedates[iIdx].endswith("11") or zedates[iIdx].endswith("21"):
                #
                #    actually, on planet Herman one should probably select "05", "15" and  "25" and save them as "01", "11" and "21"
                #
                smoothedraster[:] = tests.testdata.nodatavalue
                notnanraster[:] = ~numpy.isnan(zeresults[iIdx])
                smoothedraster[notnanraster] = numpy.where(zeresults[iIdx][notnanraster]>tests.testdata.maximumdatavalue, tests.testdata.maximumdatavalue, numpy.rint(zeresults[iIdx][notnanraster])) 

                envi_name = os.path.join(tests.testdata.sztestdatarootdirectory,"fAPAR_%s.img"%(zedates[iIdx]))
                envi_gdaldataset = osgeo.gdal.GetDriverByName("ENVI").Create(envi_name, ref_rasterxsize, ref_rasterysize, 1, osgeo.gdalconst.GDT_Byte)
                envi_gdaldataset.SetMetadataItem('values', "{fapar, -, 0, 200, 0, 200, 0, 0.005}",      'ENVI')
                envi_gdaldataset.SetMetadataItem('flags',  "{" + str(tests.testdata.nodatavalue) + "}", 'ENVI')
                envi_gdaldataset.SetGeoTransform(ref_geotransform)
                envi_gdaldataset.SetProjection(ref_projection)
                envi_gdaldataset.GetRasterBand(1).WriteArray(smoothedraster)

                if do_envi_png :
                    png_name= os.path.join(tests.testdata.sztestdatarootdirectory,"fAPAR_%s.png"%(zedates[iIdx]))
                    osgeo.gdal.GetDriverByName('PNG').CreateCopy(png_name, envi_gdaldataset)


    #
    #    compare original, whittaker and swets
    #
    originalraster = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=numpy.uint8)
    originalisdata = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=bool)

    whitraster     = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=numpy.uint8)
    whitnotnan     = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=bool)
    swetsraster    = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=numpy.uint8)
    swetsnotnan    = numpy.empty((ref_rasterysize, ref_rasterxsize), dtype=bool)

    for iIdx in range(len(zerasters)):

        if zerasters[iIdx] is None: continue

        #
        #    original raster has values 0-200 + no data 255
        #
        originalraster[:] = tests.testdata.nodatavalue
        originalisdata[:] = (tests.testdata.minimumdatavalue <= zerasters[iIdx]) & (zerasters[iIdx] <= tests.testdata.maximumdatavalue)
        originalraster[originalisdata] = numpy.where(zerasters[iIdx][originalisdata]>tests.testdata.maximumdatavalue, tests.testdata.maximumdatavalue, numpy.rint(zerasters[iIdx][originalisdata]))
        #
        #    smoothed raster has (float) values  0-200 + nan's 
        #
        whitraster[:] = tests.testdata.nodatavalue
        whitnotnan[:] = ~numpy.isnan(zewhitresults[iIdx])
        whitraster[whitnotnan] = numpy.where(zewhitresults[iIdx][whitnotnan]>tests.testdata.maximumdatavalue, tests.testdata.maximumdatavalue, numpy.rint(zewhitresults[iIdx][whitnotnan]))
        #
        #    smoothed raster has (float) values  0-200 + nan's 
        #
        swetsraster[:] = tests.testdata.nodatavalue
        swetsnotnan[:] = ~numpy.isnan(zeswetresults[iIdx])
        swetsraster[swetsnotnan] = numpy.where(zeswetresults[iIdx][swetsnotnan]>tests.testdata.maximumdatavalue, tests.testdata.maximumdatavalue, numpy.rint(zeswetresults[iIdx][swetsnotnan]))
        #
        #
        #
        rows = 1
        cols = 4
        subplots = numpy.empty( (rows,cols), dtype=object )
        figure = matplotlib.pyplot.figure(figsize=(10,3))
        for irow in range(rows):
            for icol in range(cols):
                subplots[irow, icol] = figure.add_subplot(rows, cols, 1 + icol + irow * cols)
                subplots[irow, icol].set_xticklabels([])
                subplots[irow, icol].set_yticklabels([])

        row = 0; col = 0
        subplots[row, col].imshow(zefapars[iIdx], norm=tests.testdata.fapar_norm, cmap=tests.testdata.fapar_cmap)
        subplots[row, col].set_title("original")

        row = 0; col = 1
        #subplots[row, col].imshow(originalraster.astype(float), norm=tests.testdata.faparnorm, cmap=tests.testdata.faparcolormap)
        subplots[row, col].imshow(originalraster, norm=tests.testdata.fapar_norm, cmap=tests.testdata.fapar_cmap)
        subplots[row, col].set_title("masked")

        row = 0; col = 2
        #subplots[row, col].imshow(whitraster.astype(float), norm=tests.testdata.faparnorm, cmap=tests.testdata.faparcolormap)
        subplots[row, col].imshow(whitraster, norm=tests.testdata.fapar_norm, cmap=tests.testdata.fapar_cmap)
        subplots[row, col].set_title("whittaker")

        row = 0; col = 3
        #subplots[row, col].imshow(swetsraster.astype(float), norm=tests.testdata.faparnorm, cmap=tests.testdata.faparcolormap)
        subplots[row, col].imshow(swetsraster, norm=tests.testdata.fapar_norm, cmap=tests.testdata.fapar_cmap)
        subplots[row, col].set_title("swets")

        matplotlib.pyplot.subplots_adjust(left = 0.02, right = 0.98, wspace=0.1, hspace=0.2)
        matplotlib.pyplot.suptitle("Field: %s  -  Date: %s %s" % (os.path.basename(inputdirectory), zedates[iIdx], ('- using sc mask' if busemask else '')) )

        if bmakepng:
            matplotlib.pyplot.savefig(os.path.join(tests.testdata.sztestdatarootdirectory, os.path.basename(inputdirectory) + "_Smoothed_Raster_%s.png"%(zedates[iIdx])), dpi=300)
        else:
            matplotlib.pyplot.show()

        matplotlib.pyplot.close('all')

#
#
#
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname).3s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    #
    #
    #
    bmakepng  = False
    bmakeenvi = False
    busemask  = False
    dorasters( os.path.join(tests.testdata.sztestdatarootdirectory, "2-AVy-ofdls9bS8_4_3GLH"  ), bmakepng, bmakeenvi, busemask)
    dorasters( os.path.join(tests.testdata.sztestdatarootdirectory, "29-AV0TcoCXZjsFpiOBA3gL" ), bmakepng, bmakeenvi, busemask)
    dorasters( os.path.join(tests.testdata.sztestdatarootdirectory, "190-AVzO_BSZZjsFpiOBRYcR"), bmakepng, bmakeenvi, busemask)


