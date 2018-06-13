#
#
#
import os
import re
import numpy
import osgeo.gdal
import matplotlib.pyplot
import matplotlib.colors
import yatt.smooth
import yutils.futils
import yutils.dutils

#
#    test data location
#
#sztestdatarootdirectory = yutils.futils.parentFromExistingDirectory(yutils.futils.directoryFromFile(__file__))
sztestdatarootdirectory = yutils.futils.directoryFromFile(__file__)
sztestdatarootdirectory = os.path.join(sztestdatarootdirectory, "data")

#
#    test data files
#
def makefilenamepattern(date_yyyymmdd, sztype):
    szpattern = "S2[AB]_" + date_yyyymmdd + "T.*?Z_" + sztile_ttttt + "_" + sztype + "_" + szversion_vvvv + ".tif"
    return re.compile(szpattern, flags=re.IGNORECASE)

#
#    some params about the test data
#
sztile_ttttt     = "31UFS"
szversion_vvvv   = "V101"
minimumdatavalue = 0
maximumdatavalue = 200
nodatavalue      = 255

scene_no_data_value                  = 0
scene_saturated_or_defective_value   = 1
scene_dark_area_pixels_value         = 2
scene_cloud_shadows_value            = 3
scene_vegetation_value               = 4
scene_bare_soil_value                = 5
scene_water_value                    = 6
scene_cloud_low_probability_value    = 7
scene_cloud_medium_probability_value = 8
scene_cloud_high_probability_value   = 9
scene_thin_cirrus_value              = 10
scene_snow_value                     = 11
scene_max_value                      = scene_snow_value

#
#    misc
#
_faparcolordict = {
    'red':   [(  0/255.0,  100.0/255.0, 100.0/255.0),
              ( 50/255.0,  255.0/255.0, 255.0/255.0),
              (100/255.0,  255.0/255.0, 255.0/255.0),
              (150/255.0,    0.0/255.0,   0.0/255.0),
              (201/255.0,    0.0/255.0, 210.0/255.0),
              (255/255.0,  210.0/255.0, 210.0/255.0)],
       
    'green': [(  0/255.0,  100.0/255.0, 100.0/255.0),
              ( 50/255.0,  255.0/255.0, 255.0/255.0),
              (100/255.0,  255.0/255.0, 255.0/255.0),
              (150/255.0,  255.0/255.0, 255.0/255.0),
              (201/255.0,  100.0/255.0, 210.0/255.0),
              (255/255.0,  210.0/255.0, 210.0/255.0)],
       
    'blue':  [(  0/255.0,    0.0/255.0,   0.0/255.0),
              ( 50/255.0,  100.0/255.0, 100.0/255.0),
              (100/255.0,  255.0/255.0, 255.0/255.0),
              (150/255.0,    0.0/255.0,   0.0/255.0),
              (201/255.0,   50.0/255.0,  210.0/255.0),
              (255/255.0,  210.0/255.0,  210.0/255.0)]}
 
faparcolormap = matplotlib.colors.LinearSegmentedColormap('fAPAR', _faparcolordict, N=256)
faparnorm     = matplotlib.pyplot.Normalize(0, 255)

#
#
#
defaultswetsweightvalues = yatt.smooth.WeightValues(
    maximum    =  1.5,
    minimum    =  0.005,
    posslope   =  0.5,
    negslope   =  0.5,
    aboutequal =  1.0,
    default    =  0.0)

#
#    helper for reverse engineering of the data
#
def makeflaggedenvi():

    #
    #
    #
    inputdirectory   = os.path.join(sztestdatarootdirectory, "2-AVy-ofdls9bS8_4_3GLH")
    yyyymmddfirst    = 20170101
    yyyymmddlast     = 20180101

    #
    #
    #    
    for date_yyyymmdd in yutils.dutils.g_yyyymmdd_interval(yyyymmddfirst, yyyymmddlast):

        ptFAPARpattern = makefilenamepattern(date_yyyymmdd, "FAPAR_10M")
        ptCLOUDpattern = makefilenamepattern(date_yyyymmdd, "CLOUDMASK_10M")
        ptSHADWpattern = makefilenamepattern(date_yyyymmdd, "SHADOWMASK_10M")
        ptSCENEpattern = makefilenamepattern(date_yyyymmdd, "SCENECLASSIFICATION_10M")
        
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
        #
        #         
        fapar_numpyparray = fapar_gdaldataset.ReadAsArray()
        cloud_numpyparray = cloud_gdaldataset.ReadAsArray()
        shadw_numpyparray = shadw_gdaldataset.ReadAsArray()
        scene_numpyparray = scene_gdaldataset.ReadAsArray()

        #
        #
        #
        mask_fapar_data                     = (minimumdatavalue <= fapar_numpyparray) & (fapar_numpyparray <= maximumdatavalue)
        mask_fapar_no_data                  = ~mask_fapar_data
        mask_scene_no_data                  = scene_numpyparray == scene_no_data_value
        mask_scene_saturated_or_defective   = scene_numpyparray == scene_saturated_or_defective_value
        mask_scene_dark_area_pixels         = scene_numpyparray == scene_dark_area_pixels_value
        mask_scene_cloud_shadows            = scene_numpyparray == scene_cloud_shadows_value
        mask_scene_vegetation               = scene_numpyparray == scene_vegetation_value
        mask_scene_bare_soil                = scene_numpyparray == scene_bare_soil_value
        mask_scene_water                    = scene_numpyparray == scene_water_value
        mask_scene_cloud_low_probability    = scene_numpyparray == scene_cloud_low_probability_value
        mask_scene_cloud_medium_probability = scene_numpyparray == scene_cloud_medium_probability_value
        mask_scene_cloud_high_probability   = scene_numpyparray == scene_cloud_high_probability_value
        mask_scene_thin_cirrus              = scene_numpyparray == scene_thin_cirrus_value
        mask_scene_snow                     = scene_numpyparray == scene_snow_value
        mask_scene_undefined                = scene_numpyparray >  scene_max_value

        #
        #
        #
        flagged_numpyparray = numpy.copy(fapar_numpyparray)


        flagged_numpyparray[mask_fapar_no_data & mask_scene_no_data]                   = 210 + scene_no_data_value
        flagged_numpyparray[mask_fapar_no_data & mask_scene_saturated_or_defective]    = 210 + scene_saturated_or_defective_value
        flagged_numpyparray[mask_fapar_no_data & mask_scene_dark_area_pixels]          = 210 + scene_dark_area_pixels_value
        flagged_numpyparray[mask_fapar_no_data & mask_scene_cloud_shadows]             = 210 + scene_cloud_shadows_value
        #
        flagged_numpyparray[mask_fapar_no_data & mask_scene_cloud_medium_probability]  = 210 + scene_cloud_medium_probability_value
        flagged_numpyparray[mask_fapar_no_data & mask_scene_cloud_high_probability]    = 210 + scene_cloud_high_probability_value
        flagged_numpyparray[mask_fapar_no_data & mask_scene_thin_cirrus]               = 210 + scene_thin_cirrus_value
        flagged_numpyparray[mask_fapar_no_data & mask_scene_snow]                      = 210 + scene_snow_value
 

        flagged_numpyparray[mask_fapar_data & mask_scene_no_data]                      = 230 + scene_no_data_value
        flagged_numpyparray[mask_fapar_data & mask_scene_saturated_or_defective]       = 230 + scene_saturated_or_defective_value
        flagged_numpyparray[mask_fapar_data & mask_scene_dark_area_pixels]             = 230 + scene_dark_area_pixels_value
        flagged_numpyparray[mask_fapar_data & mask_scene_cloud_shadows]                = 230 + scene_cloud_shadows_value
        #
        flagged_numpyparray[mask_fapar_data & mask_scene_cloud_medium_probability]     = 230 + scene_cloud_medium_probability_value
        flagged_numpyparray[mask_fapar_data & mask_scene_cloud_high_probability]       = 230 + scene_cloud_high_probability_value
        flagged_numpyparray[mask_fapar_data & mask_scene_thin_cirrus]                  = 230 + scene_thin_cirrus_value
        flagged_numpyparray[mask_fapar_data & mask_scene_snow]                         = 230 + scene_snow_value

        raw_numpyparray = numpy.copy(fapar_numpyparray)
        raw_numpyparray[mask_fapar_no_data] = 255
        #
        #
        #
        flagged_name = os.path.join(sztestdatarootdirectory,"flagged_fAPAR_%s.img" % (date_yyyymmdd))
        flagged_gdaldataset = osgeo.gdal.GetDriverByName("ENVI").Create(flagged_name, fapar_gdaldataset.RasterXSize, fapar_gdaldataset.RasterYSize, 1, osgeo.gdalconst.GDT_Byte)
        flagged_gdaldataset.SetGeoTransform(fapar_gdaldataset.GetGeoTransform())
        flagged_gdaldataset.SetProjection(fapar_gdaldataset.GetProjection())
        flagged_gdaldataset.GetRasterBand(1).WriteArray(flagged_numpyparray)
        #
        #
        #
        raw_name = os.path.join(sztestdatarootdirectory,"raw_fAPAR_%s.img" % (date_yyyymmdd))
        raw_gdaldataset = osgeo.gdal.GetDriverByName("ENVI").Create(raw_name, fapar_gdaldataset.RasterXSize, fapar_gdaldataset.RasterYSize, 1, osgeo.gdalconst.GDT_Byte)
        raw_gdaldataset.SetGeoTransform(fapar_gdaldataset.GetGeoTransform())
        raw_gdaldataset.SetProjection(fapar_gdaldataset.GetProjection())
        raw_gdaldataset.GetRasterBand(1).WriteArray(raw_numpyparray)

#
#
#
if __name__ == '__main__':
    makeflaggedenvi()
    
