#
#
#
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
#
#
#
import logging
import numpy
import osgeo.gdal
import matplotlib.pyplot
import yatt.mask
import yutils.gutils
import demo.testdata

#
#
#
def domasks(bmakepng):

    fapar_filename = os.path.join(demo.testdata.sztestdatarootdirectory,"31UFS/small_subset_S2B_20180705T105029Z_31UFS_FAPAR_10M_V102.tif")
    scene_filename = os.path.join(demo.testdata.sztestdatarootdirectory,"31UFS/small_subset_S2B_20180705T105029Z_31UFS_SCENECLASSIFICATION_20M_V102.tif")
    band4_filename = os.path.join(demo.testdata.sztestdatarootdirectory,"31UFS/small_subset_S2B_20180705T105029Z_31UFS_TOC-B04_10M_V102.tif")
    band3_filename = os.path.join(demo.testdata.sztestdatarootdirectory,"31UFS/small_subset_S2B_20180705T105029Z_31UFS_TOC-B03_10M_V102.tif")
    band2_filename = os.path.join(demo.testdata.sztestdatarootdirectory,"31UFS/small_subset_S2B_20180705T105029Z_31UFS_TOC-B02_10M_V102.tif")
    ignre_filename = os.path.join(demo.testdata.sztestdatarootdirectory,"31UFS/small_subset_S2X_20160101_20190531_31UFS_IGNORE_10M_V102.tif")

    #
    #    fapar & rgb
    #
    fapar_gdaldataset  = osgeo.gdal.Open(fapar_filename)
    fapar_numpyparray  = fapar_gdaldataset.ReadAsArray()

    r_band4_dataset    = osgeo.gdal.Open(band4_filename)
    g_band3_dataset    = osgeo.gdal.Open(band3_filename)
    b_band2_dataset    = osgeo.gdal.Open(band2_filename)
    r_band4_numpyarray = r_band4_dataset.ReadAsArray().astype(numpy.float32)
    g_band3_numpyarray = g_band3_dataset.ReadAsArray().astype(numpy.float32)
    b_band2_numpyarray = b_band2_dataset.ReadAsArray().astype(numpy.float32)
    #
    #    32767 no data ?
    #
    rgb_nodata_numpyarray = numpy.logical_and(b_band2_numpyarray > 32766, g_band3_numpyarray > 32766)
    rgb_nodata_numpyarray = numpy.logical_and(r_band4_numpyarray > 32766, rgb_nodata_numpyarray)

    #
    #    scene: resample scene - in 'MEM' - to 10M (as fapar and toc's)
    #
    scene_gdaldataset = yutils.gutils.resampleclassificationrasterdataset(osgeo.gdal.Open(scene_filename), fapar_gdaldataset)
    scene_numpyparray = scene_gdaldataset.ReadAsArray()
    #
    #    SimpleClassificationMask - allow 4,5,7 - since V102 water (6) cannot be trusted
    #
    simple_mask_numpyparray = yatt.mask.SimpleClassificationMask([0,1,2,3,6,8,9,10,11], binvert=False).makemask(scene_numpyparray)
    #
    #    Convolve2dClassificationMask
    #
    conv_mask_numpyparray = yatt.mask.Convolve2dClassificationMask([
        yatt.mask.Convolve2dClassificationMask.ConditionSpec(3,  [4, 5],        -0.19),
        yatt.mask.Convolve2dClassificationMask.ConditionSpec(61, [3, 8, 9, 10],  0.05)
        ]).makemask(scene_numpyparray)
    #
    #    Convolve2dClassificationMask - using ignored mask
    #
    ignre_gdaldataset = osgeo.gdal.Open(ignre_filename)
    ignre_numpyarray  = ignre_gdaldataset.ReadAsArray().astype(numpy.bool)
    ignre_mask_numpyparray = yatt.mask.Convolve2dClassificationMask([
        yatt.mask.Convolve2dClassificationMask.ConditionSpec(3,  [4, 5],        -0.19),
        yatt.mask.Convolve2dClassificationMask.ConditionSpec(61, [3, 8, 9, 10],  0.05)
        ]).makemask(scene_numpyparray, ignre_numpyarray)
    #
    #
    #
    maxcolsinsubtile = 100 #11000 #500 # 11000
    maxrowsinsubtile = 100 #11000 #500 # 11000
    #
    #    process in subtiles
    #
    for subtileRasterInfo in yutils.rutils.g_subtiles_in_tile(fapar_gdaldataset.RasterXSize, fapar_gdaldataset.RasterYSize, maxcolsinsubtile, maxrowsinsubtile, verbose = True):

        #
        #    using extractroirasterdataset => sub tile can be written as file
        #
        fapar_subtile_filename = None # os.path.join(demo.sztestdatarootdirectory, "tmp_fapar_X%03dY%03d.tif"%(subtileRasterInfo.fulltile_subtile_columnindex, subtileRasterInfo.fulltile_subtile_rowindex))
        fapar_subtile_dataset  = yutils.gutils.extractroirasterdataset(
            fapar_gdaldataset,
            subtileRasterInfo.subtile_upper_left_pixel_columnindex,
            subtileRasterInfo.subtile_upper_left_pixel_rowindex,
            subtileRasterInfo.subtile_pixel_columns,
            subtileRasterInfo.subtile_pixel_rows,
            fapar_subtile_filename)
        #
        #
        #
        fapar_subtile = fapar_subtile_dataset.ReadAsArray()

        scene_subtile = scene_numpyparray[
            subtileRasterInfo.subtile_upper_left_pixel_rowindex    : subtileRasterInfo.subtile_upper_left_pixel_rowindex    + subtileRasterInfo.subtile_pixel_rows, 
            subtileRasterInfo.subtile_upper_left_pixel_columnindex : subtileRasterInfo.subtile_upper_left_pixel_columnindex + subtileRasterInfo.subtile_pixel_columns]

        simple_mask = simple_mask_numpyparray[
            subtileRasterInfo.subtile_upper_left_pixel_rowindex    : subtileRasterInfo.subtile_upper_left_pixel_rowindex    + subtileRasterInfo.subtile_pixel_rows, 
            subtileRasterInfo.subtile_upper_left_pixel_columnindex : subtileRasterInfo.subtile_upper_left_pixel_columnindex + subtileRasterInfo.subtile_pixel_columns]

        conv_mask = conv_mask_numpyparray[
            subtileRasterInfo.subtile_upper_left_pixel_rowindex    : subtileRasterInfo.subtile_upper_left_pixel_rowindex    + subtileRasterInfo.subtile_pixel_rows, 
            subtileRasterInfo.subtile_upper_left_pixel_columnindex : subtileRasterInfo.subtile_upper_left_pixel_columnindex + subtileRasterInfo.subtile_pixel_columns]

        ignre_subtile = ignre_numpyarray[
            subtileRasterInfo.subtile_upper_left_pixel_rowindex    : subtileRasterInfo.subtile_upper_left_pixel_rowindex    + subtileRasterInfo.subtile_pixel_rows, 
            subtileRasterInfo.subtile_upper_left_pixel_columnindex : subtileRasterInfo.subtile_upper_left_pixel_columnindex + subtileRasterInfo.subtile_pixel_columns]

        ignre_mask = ignre_mask_numpyparray[
            subtileRasterInfo.subtile_upper_left_pixel_rowindex    : subtileRasterInfo.subtile_upper_left_pixel_rowindex    + subtileRasterInfo.subtile_pixel_rows, 
            subtileRasterInfo.subtile_upper_left_pixel_columnindex : subtileRasterInfo.subtile_upper_left_pixel_columnindex + subtileRasterInfo.subtile_pixel_columns]

        r_subtile = r_band4_numpyarray[
            subtileRasterInfo.subtile_upper_left_pixel_rowindex    : subtileRasterInfo.subtile_upper_left_pixel_rowindex    + subtileRasterInfo.subtile_pixel_rows, 
            subtileRasterInfo.subtile_upper_left_pixel_columnindex : subtileRasterInfo.subtile_upper_left_pixel_columnindex + subtileRasterInfo.subtile_pixel_columns]
        g_subtile = g_band3_numpyarray[
            subtileRasterInfo.subtile_upper_left_pixel_rowindex    : subtileRasterInfo.subtile_upper_left_pixel_rowindex    + subtileRasterInfo.subtile_pixel_rows, 
            subtileRasterInfo.subtile_upper_left_pixel_columnindex : subtileRasterInfo.subtile_upper_left_pixel_columnindex + subtileRasterInfo.subtile_pixel_columns]
        b_subtile = b_band2_numpyarray[
            subtileRasterInfo.subtile_upper_left_pixel_rowindex    : subtileRasterInfo.subtile_upper_left_pixel_rowindex    + subtileRasterInfo.subtile_pixel_rows, 
            subtileRasterInfo.subtile_upper_left_pixel_columnindex : subtileRasterInfo.subtile_upper_left_pixel_columnindex + subtileRasterInfo.subtile_pixel_columns]

        figure = matplotlib.pyplot.figure(figsize=(4.8,8))
        gridspec_rows = 5
        gridspec_cols = 3
        gridspec = matplotlib.gridspec.GridSpec(gridspec_rows, gridspec_cols)
        gridspec.update(top = .95, left = 0.01, bottom = 0.01, right = .95, wspace=0.01, hspace=0.01, )

        # [0,0] full scene

        axis = matplotlib.pyplot.subplot(gridspec[0, 0])
        fulltilerefaxis = axis
        axis.set_xticklabels([]); axis.set_yticklabels([])
        scene_fulltile_numpyarray = scene_numpyparray.copy()
        scene_fulltile_numpyarray[
            subtileRasterInfo.subtile_upper_left_pixel_rowindex    : subtileRasterInfo.subtile_upper_left_pixel_rowindex    + subtileRasterInfo.subtile_pixel_rows, 
            subtileRasterInfo.subtile_upper_left_pixel_columnindex : subtileRasterInfo.subtile_upper_left_pixel_columnindex + subtileRasterInfo.subtile_pixel_columns] = demo.testdata.scene_saturated_or_defective_value # red
        axis.imshow(scene_fulltile_numpyarray, norm=demo.testdata.scene_norm, cmap=demo.testdata.scene_cmap)

        # [0,1] full fapar

        axis = matplotlib.pyplot.subplot(gridspec[0, 1], sharex=fulltilerefaxis, sharey=fulltilerefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        fapar_fulltile_numpyarray = fapar_numpyparray.copy()
        fapar_fulltile_numpyarray[
            subtileRasterInfo.subtile_upper_left_pixel_rowindex    : subtileRasterInfo.subtile_upper_left_pixel_rowindex    + subtileRasterInfo.subtile_pixel_rows, 
            subtileRasterInfo.subtile_upper_left_pixel_columnindex : subtileRasterInfo.subtile_upper_left_pixel_columnindex + subtileRasterInfo.subtile_pixel_columns] = demo.testdata.nodatavalue # grey
        axis.imshow(fapar_fulltile_numpyarray, norm=demo.testdata.fapar_norm, cmap=demo.testdata.fapar_cmap)

        # [0,2] full rgb

        axis = matplotlib.pyplot.subplot(gridspec[0, 2], sharex=fulltilerefaxis, sharey=fulltilerefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        #
        #    values 0-10000. clipping @ 2000 (because somebody said so, and somebody is an honorable man) 
        #
        clip_max = 2000
        r_band4_numpyarray[rgb_nodata_numpyarray] = clip_max # => no data as pure red
        g_band3_numpyarray[rgb_nodata_numpyarray] = 0
        b_band2_numpyarray[rgb_nodata_numpyarray] = 0
        axis.imshow(numpy.stack(
            (
                numpy.clip(r_band4_numpyarray / clip_max, 0.0, 1.0), 
                numpy.clip(g_band3_numpyarray / clip_max, 0.0, 1.0), 
                numpy.clip(b_band2_numpyarray / clip_max, 0.0, 1.0)), 
            axis=2))

        # [1,0]

        axis = matplotlib.pyplot.subplot(gridspec[1, 0])
        subtilesrefaxis = axis
        axis.set_xticklabels([]); axis.set_yticklabels([])
        axis.imshow(scene_subtile, norm=demo.testdata.scene_norm, cmap=demo.testdata.scene_cmap)

        # [1,1]

        axis = matplotlib.pyplot.subplot(gridspec[1, 1], sharex=subtilesrefaxis, sharey=subtilesrefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        axis.imshow(fapar_subtile, norm=demo.testdata.fapar_norm, cmap=demo.testdata.fapar_cmap)

        # [1,2]

        axis = matplotlib.pyplot.subplot(gridspec[1, 2], sharex=subtilesrefaxis, sharey=subtilesrefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        #
        #    values 0-10000. normal clipping @ 2000 (because somebody said so, and somebody is an honorable man) - here 1000 to compare 
        #
        clip_max = 1000
        r_band4_numpyarray[rgb_nodata_numpyarray] = clip_max # => no data as pure red
        g_band3_numpyarray[rgb_nodata_numpyarray] = 0
        b_band2_numpyarray[rgb_nodata_numpyarray] = 0
        axis.imshow(numpy.stack(
            (
                numpy.clip(r_subtile / clip_max, 0.0, 1.0), 
                numpy.clip(g_subtile / clip_max, 0.0, 1.0), 
                numpy.clip(b_subtile / clip_max, 0.0, 1.0)), 
            axis=2))

        # [2,0]

        axis = matplotlib.pyplot.subplot(gridspec[2, 0], sharex=subtilesrefaxis, sharey=subtilesrefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        axis.imshow(simple_mask, cmap='gray', vmin=0, vmax=1)

        # [2,1]

        axis = matplotlib.pyplot.subplot(gridspec[2, 1], sharex=subtilesrefaxis, sharey=subtilesrefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        masked_fapar = fapar_subtile.copy()
        masked_fapar[simple_mask] = demo.testdata.nodatavalue
        axis.imshow(masked_fapar,  norm=demo.testdata.fapar_norm, cmap=demo.testdata.fapar_cmap)

        # [2,2]

        axis = matplotlib.pyplot.subplot(gridspec[2, 2], sharex=subtilesrefaxis, sharey=subtilesrefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        #
        #    values 0-10000. normal clipping @ 2000 (because somebody said so, and somebody is an honorable man)
        #
        clip_max = 2000
        r_band4_numpyarray[rgb_nodata_numpyarray] = clip_max # => no data as pure red
        g_band3_numpyarray[rgb_nodata_numpyarray] = 0
        b_band2_numpyarray[rgb_nodata_numpyarray] = 0
        axis.imshow(numpy.stack(
            (
                numpy.clip(r_subtile / clip_max, 0.0, 1.0), 
                numpy.clip(g_subtile / clip_max, 0.0, 1.0), 
                numpy.clip(b_subtile / clip_max, 0.0, 1.0)), 
            axis=2))

        # [3,0]

        axis = matplotlib.pyplot.subplot(gridspec[3, 0], sharex=subtilesrefaxis, sharey=subtilesrefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        axis.imshow(conv_mask, cmap='gray', vmin=0, vmax=1)

        # [3,1]

        axis = matplotlib.pyplot.subplot(gridspec[3, 1], sharex=subtilesrefaxis, sharey=subtilesrefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        masked_fapar = fapar_subtile.copy()
        masked_fapar[conv_mask] = demo.testdata.nodatavalue
        axis.imshow(masked_fapar,  norm=demo.testdata.fapar_norm, cmap=demo.testdata.fapar_cmap)

        # [3,2]

        axis = matplotlib.pyplot.subplot(gridspec[3, 2], sharex=subtilesrefaxis, sharey=subtilesrefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        #
        #    values 0-10000. normal clipping @ 2000 (because somebody said so, and somebody is an honorable man) - here 5000 to compare 
        #
        clip_max = 5000
        r_band4_numpyarray[rgb_nodata_numpyarray] = clip_max # => no data as pure red
        g_band3_numpyarray[rgb_nodata_numpyarray] = 0
        b_band2_numpyarray[rgb_nodata_numpyarray] = 0
        axis.imshow(numpy.stack(
            (
                numpy.clip(r_subtile / clip_max, 0.0, 1.0), 
                numpy.clip(g_subtile / clip_max, 0.0, 1.0), 
                numpy.clip(b_subtile / clip_max, 0.0, 1.0)), 
            axis=2))

        # [4,0]

        axis = matplotlib.pyplot.subplot(gridspec[4, 0], sharex=subtilesrefaxis, sharey=subtilesrefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        axis.imshow(ignre_mask, cmap='gray', vmin=0, vmax=1)

        # [4,1]

        axis = matplotlib.pyplot.subplot(gridspec[4, 1], sharex=subtilesrefaxis, sharey=subtilesrefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        masked_fapar = fapar_subtile.copy()
        masked_fapar[ignre_mask] = demo.testdata.nodatavalue
        axis.imshow(masked_fapar, norm=demo.testdata.fapar_norm, cmap=demo.testdata.fapar_cmap)

        # [4,2]

        axis = matplotlib.pyplot.subplot(gridspec[4, 2], sharex=subtilesrefaxis, sharey=subtilesrefaxis)
        axis.set_xticklabels([]); axis.set_yticklabels([])
        axis.imshow(ignre_subtile, cmap='gray', vmin=0, vmax=1)
 
        #
        #
        #
        matplotlib.pyplot.suptitle("Subtile X%03d x Y%03d from 0..%s x 0..%s" % (
            subtileRasterInfo.fulltile_subtile_columnindex, 
            subtileRasterInfo.fulltile_subtile_rowindex,
            subtileRasterInfo.fulltile_subtile_columns, 
            subtileRasterInfo.fulltile_subtile_rows) )

        if bmakepng:
            matplotlib.pyplot.savefig(os.path.join(demo.testdata.sztestdatarootdirectory, "Masking_X%03dY%03d.png"%(subtileRasterInfo.fulltile_subtile_columnindex,subtileRasterInfo.fulltile_subtile_rowindex)), dpi=300)
        else:
            matplotlib.pyplot.show()
        #
        #    close('all') should be enough, but somehow sometimes it still seams to leak
        #
        figure.clear()
        matplotlib.pyplot.close(figure)
        matplotlib.pyplot.close('all')

        fapar_subtile_dataset   = None

    fapar_gdaldataset = None
    scene_gdaldataset = None
    r_band4_dataset   = None
    g_band3_dataset   = None
    b_band2_dataset   = None


#
#
#
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname).3s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    #
    #
    #
    bmakepng = False
    #
    #
    #
    domasks(bmakepng)



