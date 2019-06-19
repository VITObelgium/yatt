#
#
#
import os
import re
import numpy
import osgeo.gdal
import matplotlib.pyplot
import matplotlib.colors
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
    return re.compile(szpattern, flags=re.RegexFlag.IGNORECASE)

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

scene_values = [
    scene_no_data_value,
    scene_saturated_or_defective_value,
    scene_dark_area_pixels_value,
    scene_cloud_shadows_value,
    scene_vegetation_value,
    scene_bare_soil_value,
    scene_water_value,
    scene_cloud_low_probability_value,
    scene_cloud_medium_probability_value,
    scene_cloud_high_probability_value,
    scene_thin_cirrus_value,
    scene_snow_value,
    ]

#
#    colors from cropsar inspector
#
fapar_rgb_int = [(168,  80,   0),
                 (189, 124,   0),
                 (211, 167,   0),
                 (233, 211,   0),
                 (255, 255,   0),
                 (200, 222,   0),
                 (145, 189,   0),
                 ( 91, 157,   0),
                 ( 36, 124,   0),
                 ( 51, 102,   0),
                 (210, 210,  210)]
#                 (  0,   0,   0)]

fapar_rgb  = [(r/255., g/255., b/255.) for (r, g, b) in fapar_rgb_int]
fapar_cmap = matplotlib.colors.ListedColormap(fapar_rgb)
#fapar_norm = matplotlib.colors.BoundaryNorm( [b/200. for b in [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 255]], fapar_cmap.N)
fapar_norm = matplotlib.colors.BoundaryNorm( [b - 0.5 for b in [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 201, 255]], fapar_cmap.N)

scene_rgb_int = [(scene_no_data_value,             (  0,   0,   0)),
          (scene_saturated_or_defective_value,     (255,   0,   0)),
          (scene_dark_area_pixels_value,           ( 51,  51,  51)),
          (scene_cloud_shadows_value,              (102,  51,   0)),
          (scene_vegetation_value,                 (  0, 255,   0)),
          (scene_bare_soil_value,                  (255, 255,   0)),
          (scene_water_value,                      (  0,   0, 255)),
          (scene_cloud_low_probability_value,      (128, 128, 128)),
          (scene_cloud_medium_probability_value,   (200, 200, 200)),
          (scene_cloud_high_probability_value,     (255, 255, 255)),
          (scene_thin_cirrus_value,                (102, 204, 255)),
          (scene_snow_value,                       (255, 153, 255)),
          (255,                                    (253, 106,   2))] # 'Tiger Orange'

scene_rgb  = [(s, (r/255., g/255., b/255.)) for (s, (r, g, b))     in scene_rgb_int]
scene_cmap = matplotlib.colors.ListedColormap([rgb for (s, rgb)    in scene_rgb])
scene_norm = matplotlib.colors.BoundaryNorm([center-0.5 for center in range(len(scene_rgb))]+[255], scene_cmap.N)

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

