#
#
#
import osgeo.gdal



"""
some misc gdal utilities - no rocket science, just tired of googling them each time. 
"""

#
#
#
def pixel2world(gdalgeotransformmatrix, pixelcolidx, pixelrowidx):
    """
    GDAL datasets GeoTransform describe the relationship between raster positions (in column/row coordinates) and georeferenced coordinates via an affine transform.
    Xgeo = GT(0) + Xcolidx*GT(1) + Yrowidx*GT(2)
    Ygeo = GT(3) + Xcolidx*GT(4) + Yrowidx*GT(5)
    In case of north up images, the GT(2) and GT(4) coefficients are zero, and the GT(1) is pixel width, and GT(5) is pixel height.
    The (GT(0),GT(3)) position is the top left corner of the top left pixel of the raster.
    Note that the column/row coordinates in the above are from:
        (0.0,0.0)                          at the TOP LEFT CORNER of the TOP LEFT PIXEL to 
        (width_in_pixels,height_in_pixels) at the BOTTOM RIGHT CORNER of the BOTTOM RIGHT pixel.
    The pixel/line location of the center of the top left pixel would therefore be (0.5,0.5).
    (from http://www.gdal.org/gdal_datamodel.html)

    BEWARE: for some mysterious reason "GT(5) is pixel height" results in NEGATIVE heights. 
    - looking at "Ygeo = GT(3) + Xcolidx*GT(4) + Yrowidx*GT(5)", and assuming top left corner is TOP LEFT for everybody, this seems logical
    - however, from the description "GT(5) is pixel height" this seems nonsense.
    - the "tutorial" http://www.gdal.org/gdal_tutorial.html contains the explicit comment /* n-s pixel resolution (negative value) */

    adfGeoTransform[0] /* top left x */
    adfGeoTransform[1] /* w-e pixel resolution */
    adfGeoTransform[2] /* 0 */
    adfGeoTransform[3] /* top left y */
    adfGeoTransform[4] /* 0 */
    adfGeoTransform[5] /* n-s pixel resolution (negative value) */

    Assuming north up images:
    """
    pixelxgeo = gdalgeotransformmatrix[0] + pixelcolidx * gdalgeotransformmatrix[1]
    pixelygeo = gdalgeotransformmatrix[3] + pixelrowidx * gdalgeotransformmatrix[5]
    return (pixelxgeo, pixelygeo)

#
#
#
def world2pixel(gdalgeotransformmatrix, pixelxgeo, pixelygeo):
    """
    (pixelcolidx, pixelrowidx) will be returned as floats; leave it to the client to decide what is actually needed.

    Assuming north up images:
    """
    pixelcolidx = (pixelxgeo - gdalgeotransformmatrix[0]) / gdalgeotransformmatrix[1]
    pixelrowidx = (pixelygeo - gdalgeotransformmatrix[3]) / gdalgeotransformmatrix[5]
    return (pixelcolidx, pixelrowidx)

#
#
#
def shiftgeotransform(tilegdalgeotransformmatrix, subtile_upper_left_pixel_columnindex, subtile_upper_left_pixel_rowindex):
    """
    adapt GeoTransform typically when dividing raster dataset in sub-tiles 
    """
    return (
        tilegdalgeotransformmatrix[0] + subtile_upper_left_pixel_columnindex * tilegdalgeotransformmatrix[1],
        tilegdalgeotransformmatrix[1],
        tilegdalgeotransformmatrix[2],
        tilegdalgeotransformmatrix[3] + subtile_upper_left_pixel_rowindex * tilegdalgeotransformmatrix[5],
        tilegdalgeotransformmatrix[4],
        tilegdalgeotransformmatrix[5]
        )

#
#
#
def resampleclassificationrasterfile(srcRasterFileName, refRasterFileName, dstRasterFileName):
    """
    """
    #
    #
    #
    src_rastr_gdaldataset = osgeo.gdal.Open(srcRasterFileName)
    ref_rastr_gdaldataset = osgeo.gdal.Open(refRasterFileName)
    return resampleclassificationrasterdataset(src_rastr_gdaldataset, ref_rastr_gdaldataset, dstRasterFileName=dstRasterFileName)

#
#
#
def resampleclassificationrasterdataset(srcRasterDataset, refRasterFileDataset, dstRasterFileName = None):
    """
    resample/reproject source to destination according to reference file
    method is GRA_Mode - as suited for classifications (e.g. S2 SCENECLASSIFICATION from _20M to _10M)
    rem: for the time being; only single band
    
    TODO: introduce (or check) explicit driver (e.g. 'by name' ?) -> in case srcRasterDataset driver is 'MEM', the dst cannot be written to file
    """
    #
    #
    #
    src_rastr_gdaldataset = srcRasterDataset
    ref_rastr_gdaldataset = refRasterFileDataset
    if dstRasterFileName is not None:
        dst_rastr_gdaldataset = src_rastr_gdaldataset.GetDriver().Create( dstRasterFileName, ref_rastr_gdaldataset.RasterXSize, ref_rastr_gdaldataset.RasterYSize, 1, src_rastr_gdaldataset.GetRasterBand(1).DataType)
    else:
        dst_rastr_gdaldataset = osgeo.gdal.GetDriverByName('MEM').Create( '', ref_rastr_gdaldataset.RasterXSize, ref_rastr_gdaldataset.RasterYSize, 1, src_rastr_gdaldataset.GetRasterBand(1).DataType)
    dst_rastr_gdaldataset.SetGeoTransform(ref_rastr_gdaldataset.GetGeoTransform())
    dst_rastr_gdaldataset.SetProjection(ref_rastr_gdaldataset.GetProjection())
    osgeo.gdal.ReprojectImage(src_rastr_gdaldataset, dst_rastr_gdaldataset, src_rastr_gdaldataset.GetProjection(), ref_rastr_gdaldataset.GetProjection(), osgeo.gdalconst.GRA_Mode)
    return dst_rastr_gdaldataset

#
#
#
def extractroirasterfile(srcRasterFileName, upper_left_pixel_columnindex, upper_left_pixel_rowindex, pixel_columns, pixel_rows, dstRasterFileName):
    """
    """
    #
    #
    #
    src_rastr_gdaldataset = osgeo.gdal.Open(srcRasterFileName)
    return extractroirasterdataset(src_rastr_gdaldataset, upper_left_pixel_columnindex, upper_left_pixel_rowindex, pixel_columns, pixel_rows, dstRasterFileName=dstRasterFileName)

#
#
#
def extractroirasterdataset(srcRasterDataset, upperleftpixelcolumnindex, upperleftpixelrowindex, pixelcolumns, pixelrows, dstRasterFileName = None):
    """
    extract roi from dataset
    rem: for the time being; only single band
    rem: yes I know. gdal.Translate can do more and better. I'll only hit until you cry, After that you don't ask why.

    TODO: introduce (or check) explicit driver (e.g. 'by name' ?) -> in case srcRasterDataset driver is 'MEM', the dst cannot be written to file
    """
    if dstRasterFileName is not None:
        dst_rastr_gdaldataset = srcRasterDataset.GetDriver().Create( dstRasterFileName, pixelcolumns, pixelrows, 1, srcRasterDataset.GetRasterBand(1).DataType)
    else:
        dst_rastr_gdaldataset = osgeo.gdal.GetDriverByName('MEM').Create( '', pixelcolumns, pixelrows, 1, srcRasterDataset.GetRasterBand(1).DataType)

    dst_rastr_gdaldataset.SetProjection(srcRasterDataset.GetProjection())

    dst_rastr_gdaldataset.SetGeoTransform(shiftgeotransform(
        srcRasterDataset.GetGeoTransform(), 
        upperleftpixelcolumnindex, 
        upperleftpixelrowindex))

    dst_rastr_gdaldataset.GetRasterBand(1).WriteArray(
        srcRasterDataset.ReadAsArray(
            xoff  = upperleftpixelcolumnindex,
            yoff  = upperleftpixelrowindex,
            xsize = pixelcolumns,
            ysize = pixelrows))

    return dst_rastr_gdaldataset


