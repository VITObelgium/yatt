#
#
#
import osgeo.gdal
import numpy
import math
import os



"""
some misc gdal utilities and snippets - no rocket science, just tired of googling them each time. 
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
    dst_rastr_gdaldataset = resampleclassificationrasterdataset(src_rastr_gdaldataset, ref_rastr_gdaldataset, dstRasterFileName=dstRasterFileName)
    if dstRasterFileName is None:
        return dst_rastr_gdaldataset
    else:
        dst_rastr_gdaldataset = None
        return osgeo.gdal.Open(dstRasterFileName)

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
def subsamplerasterdatafile(srcRasterFileName, iWindowSize, dstRasterFileName):
    """
    """
    src_rastr_gdaldataset = osgeo.gdal.Open(srcRasterFileName)
    return subsamplerasterdataset(src_rastr_gdaldataset, iWindowSize, dstRasterFileName=dstRasterFileName)

#
#
#
def subsamplerasterdataset(srcRasterDataset, iWindowSize, dstRasterFileName = None):
    """
    subsamples source to destination by averaging over a fixed window. 
    'degrade the resolution of an image'; actually simple Glimpse.IMGthin-alike.
    uses gdal.Translate with method 'GRA_Average' => do NOT use for classifications.
    """
    #
    # https://gdal.org/programs/gdal_translate.html : Target resolution must be expressed in georeferenced units. Both must be positive values.
    # https://gdal.org/api/gdalwarp_cpp.html?highlight=gra_mode
    # - use osgeo.gdalconst.GRA_Mode instead of osgeo.gdal.GRA_Average in case of classifications.
    # - try osgeo.gdalconst.GRA_Max as soon as our default mep gdal version supports it (version 2.2.3 ?).
    #
    dst_rastr_gdaldataset = osgeo.gdal.Translate(
        '' if dstRasterFileName is None else dstRasterFileName, 
        srcRasterDataset, 
        options=osgeo.gdal.TranslateOptions(
            format      = 'MEM' if dstRasterFileName is None else None,
            xRes        = abs(iWindowSize*srcRasterDataset.GetGeoTransform()[1]),
            yRes        = abs(iWindowSize*srcRasterDataset.GetGeoTransform()[5]),
            noData      = srcRasterDataset.GetRasterBand(1).GetNoDataValue(),
            resampleAlg = osgeo.gdal.GRA_Average ))

    if dstRasterFileName is None:
        return dst_rastr_gdaldataset
    else:
        dst_rastr_gdaldataset = None
        return osgeo.gdal.Open(dstRasterFileName)

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

    if srcRasterDataset.GetRasterBand(1).GetNoDataValue() is not None:
        dst_rastr_gdaldataset.GetRasterBand(1).SetNoDataValue(srcRasterDataset.GetRasterBand(1).GetNoDataValue())

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

    if dstRasterFileName is None:
        return dst_rastr_gdaldataset
    else:
        #
        #    force the file to be written before returning.
        #    yes, this costs computer time. yes, this saves human headaches.
        #
        dst_rastr_gdaldataset = None
        return osgeo.gdal.Open(dstRasterFileName)

#
#
#
def maskrasterfile(srcRasterFileName, mskRasterFileName, maskDataValue, dstRasterFileName):
    """
    """
    srcRasterDataset = osgeo.gdal.Open(srcRasterFileName)
    mskRasterDataset = osgeo.gdal.Open(mskRasterFileName)
    return maskrasterdataset(srcRasterDataset, mskRasterDataset, maskDataValue, dstRasterFileName)

#
#
#
def maskrasterdataset(srcRasterDataset, mskRasterDataset, maskDataValue, dstRasterFileName = None):
    """
    :param srcRasterDataset
    :param mskRasterDataset raster specifying pixels to be masked. interpreted as boolean via 'ReadAsArray().astype(numpy.bool)'
    :param maskDataValue will replace masked data values  
    assumes srcRasterDataset and mskRasterDataset have identical projection, framing, ...
    however, if sizes between src and msk does not match, a naive rescue is attempted via 'resampleclassificationrasterdataset'
    """
    if ( srcRasterDataset.RasterXSize != mskRasterDataset.RasterXSize or srcRasterDataset.RasterYSize != mskRasterDataset.RasterYSize ):
        mskRasterDataset = resampleclassificationrasterdataset(mskRasterDataset, srcRasterDataset)

    if dstRasterFileName is not None:
        dst_rastr_gdaldataset = srcRasterDataset.GetDriver().Create( dstRasterFileName, srcRasterDataset.RasterXSize, srcRasterDataset.RasterYSize, 1, srcRasterDataset.GetRasterBand(1).DataType)
    else:
        dst_rastr_gdaldataset = osgeo.gdal.GetDriverByName('MEM').Create( '', srcRasterDataset.RasterXSize, srcRasterDataset.RasterYSize, 1, srcRasterDataset.GetRasterBand(1).DataType)

    dst_rastr_gdaldataset.SetGeoTransform(srcRasterDataset.GetGeoTransform())
    dst_rastr_gdaldataset.SetProjection(srcRasterDataset.GetProjection())

    dst_numpyarray = srcRasterDataset.GetRasterBand(1).ReadAsArray()
    dst_numpyarray[mskRasterDataset.GetRasterBand(1).ReadAsArray().astype(numpy.bool)] = maskDataValue
    dst_rastr_gdaldataset.GetRasterBand(1).WriteArray(dst_numpyarray)
    dst_rastr_gdaldataset.GetRasterBand(1).SetNoDataValue(maskDataValue)  

    return dst_rastr_gdaldataset

#
#
#
def mosaicrasterfiles(lstSrcRasterFileNames, dstRasterFileName = None, missingDataValue = None):
    """
    mosaic files into dataset. assumes files of identical datatype, projection, framing, ...
    typically for recombining results when rasters have been divided in sub-tiles for processing

    rem: for the time being; only single band
    """

    bisfirstpass = True

    for srcRasterFileName in lstSrcRasterFileNames:
        src_gdaldataset  = osgeo.gdal.Open(srcRasterFileName)
        if src_gdaldataset is None: 
            continue

        src_rasterxsize  = src_gdaldataset.RasterXSize
        src_rasterysize  = src_gdaldataset.RasterYSize
        src_geotransform = src_gdaldataset.GetGeoTransform()
        src_projection   = src_gdaldataset.GetProjection()
        src_datatype     = src_gdaldataset.GetRasterBand(1).DataType
        src_nodatavalue  = src_gdaldataset.GetRasterBand(1).GetNoDataValue()
        src_ulx_geo      = src_geotransform[0]
        src_uly_geo      = src_geotransform[3]
        src_dx_geo       = src_geotransform[1]
        src_dy_geo       = src_geotransform[5]
        src_brx_geo      = src_ulx_geo + src_dx_geo * src_rasterxsize
        src_bry_geo      = src_uly_geo + src_dy_geo * src_rasterysize # src_dy_geo is negative

        if bisfirstpass:
            bisfirstpass    = False
            dst_projection  = src_projection  # won't change - assumed constant
            dst_datatype    = src_datatype    # won't change - assumed constant - checked
            dst_nodatavalue = src_nodatavalue # won't change - assumed constant (or none) - checked
            dst_ulx_geo     = src_ulx_geo
            dst_uly_geo     = src_uly_geo
            dst_dx_geo      = src_dx_geo      # won't change - assumed constant - checked (more or less)
            dst_dy_geo      = src_dy_geo      # won't change - assumed constant - checked (more or less) - dst_dy_geo is negative
            dst_brx_geo     = src_brx_geo
            dst_bry_geo     = src_bry_geo
            dst_rasterxsize = src_rasterxsize
            dst_rasterysize = src_rasterysize

        else:
            dst_ulx_geo     = min(dst_ulx_geo, src_ulx_geo)
            dst_uly_geo     = max(dst_uly_geo, src_uly_geo)
            dst_brx_geo     = max(dst_brx_geo, src_brx_geo)
            dst_bry_geo     = min(dst_bry_geo, src_bry_geo)
            dst_rasterxsize = int(round( (dst_brx_geo - dst_ulx_geo) / dst_dx_geo ))
            dst_rasterysize = int(round( (dst_bry_geo - dst_uly_geo) / dst_dy_geo ))  # dst_dy_geo is negative
            #
            #    some handwaving
            #
            if not dst_datatype == src_datatype:
                raise ValueError("deviant datatype in file '%s'" % (os.path.basename(srcRasterFileName),))
            if src_nodatavalue is not None:
                if not dst_nodatavalue == src_nodatavalue:
                    raise ValueError("deviant nodata value in file '%s'" % (os.path.basename(srcRasterFileName),))
            else:
                if dst_nodatavalue is not None:
                    raise ValueError("deviant None nodata value in file '%s'" % (os.path.basename(srcRasterFileName),))
            if not math.isclose(dst_dx_geo, src_dx_geo, rel_tol=0.01/src_rasterxsize):
                raise ValueError("deviant x-resolution in file '%s'" % (os.path.basename(srcRasterFileName),))
            if not math.isclose(dst_dy_geo, src_dy_geo, rel_tol=0.01/src_rasterxsize):
                raise ValueError("deviant y-resolution in file '%s'" % (os.path.basename(srcRasterFileName),))
            if not math.isclose(dst_rasterxsize, ((dst_brx_geo - dst_ulx_geo) / dst_dx_geo), abs_tol=0.01):
                raise ValueError("deviant x-framing in file '%s'" % (os.path.basename(srcRasterFileName),))
            if not math.isclose(dst_rasterysize, ((dst_bry_geo - dst_uly_geo) / dst_dy_geo), abs_tol=0.01):
                raise ValueError("deviant y-framing in file '%s'" % (os.path.basename(srcRasterFileName),))

        # close src
        src_gdaldataset = None

    #
    #    if still in bisfirstpass this means each file has been skipped
    #
    if bisfirstpass: raise ValueError("no datasets available")

    #
    #
    #
    dst_rastr_gdaldataset = None

    for srcRasterFileName in lstSrcRasterFileNames:
        src_gdaldataset  = osgeo.gdal.Open(srcRasterFileName)
        if src_gdaldataset is None: continue

        if dst_rastr_gdaldataset is None:
            if dstRasterFileName is not None:
                dst_rastr_gdaldataset = src_gdaldataset.GetDriver().Create( dstRasterFileName, dst_rasterxsize, dst_rasterysize, 1, dst_datatype)
            else:
                dst_rastr_gdaldataset = osgeo.gdal.GetDriverByName('MEM').Create( '', dst_rasterxsize, dst_rasterysize, 1, dst_datatype)
            dst_rastr_gdaldataset.SetGeoTransform([dst_ulx_geo, dst_dx_geo, 0, dst_uly_geo, 0, dst_dy_geo])
            dst_rastr_gdaldataset.SetProjection(dst_projection)

            dst_numpyarray = dst_rastr_gdaldataset.GetRasterBand(1).ReadAsArray()

            #
            #    the data arrays defaults to  missingDataValue if specified, else to dst_nodatavalue if available, else in gdal we trust 
            #    the nodatavalue defaults to  dst_nodatavalue if available, else to missingDataValue if, else in gdal we trust 
            #
            if missingDataValue is not None:
                dst_numpyarray.fill(missingDataValue)
                if dst_nodatavalue is None:
                    dst_rastr_gdaldataset.GetRasterBand(1).SetNoDataValue(missingDataValue)

            if dst_nodatavalue is not None:
                dst_rastr_gdaldataset.GetRasterBand(1).SetNoDataValue(dst_nodatavalue)
                if missingDataValue is None:
                    dst_numpyarray.fill(dst_nodatavalue)

        # target window
        src_rasterxsize  = src_gdaldataset.RasterXSize
        src_rasterysize  = src_gdaldataset.RasterYSize
        src_geotransform = src_gdaldataset.GetGeoTransform()
        src_ulx_geo      = src_geotransform[0]
        src_uly_geo      = src_geotransform[3]

        ulx_colidx, uly_rowidx = world2pixel(dst_rastr_gdaldataset.GetGeoTransform(), src_ulx_geo, src_uly_geo)
        ulx_colidx = int(round(ulx_colidx))
        uly_rowidx = int(round(uly_rowidx))

        # fill out dst
        dst_numpyarray[uly_rowidx:uly_rowidx+src_rasterysize, ulx_colidx:ulx_colidx+src_rasterxsize] = src_gdaldataset.ReadAsArray()
        # close src
        src_gdaldataset = None


    dst_rastr_gdaldataset.GetRasterBand(1).WriteArray(dst_numpyarray)
    return dst_rastr_gdaldataset

