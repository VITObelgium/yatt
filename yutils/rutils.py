#
#
#
import collections
import logging



"""
raster utilities
"""


#
#
#
SubtileRasterInfo = collections.namedtuple('SubtileRasterInfo', [
    'fulltile_pixel_columns',                  # total number of pixel columns in the full tile (~ gdaldataset.RasterXSize)
    'fulltile_pixel_rows',                     # total number of pixel rows in the full tile (~ gdaldataset.RasterYSize)
    'fulltile_subtile_columns',                # total number of sub-tile columns or number of sub-tiles in X (horizontal) direction in the full tile 
    'fulltile_subtile_rows',                   # total number of sub-tile rows or number of sub-tiles in Y (vertical) direction in the full tile 
    'fulltile_subtile_columnindex',            # sub-tile column index (X index, horizontal direction) of this sub-tile in the sub-tiles raster of the full tile (0...fulltile_subtile_columns-1)
    'fulltile_subtile_rowindex',               # sub-tile row index (Y index, vertical direction) of this sub-tile in the sub-tiles raster of the full tile (0...fulltile_subtile_rows-1)  
    'subtile_pixel_columns',                   # number of pixel columns in this sub-tile (nobody said this would be constant over all sub-tiles in the tile!)
    'subtile_pixel_rows',                      # number of pixel rows in this sub-tile (nobody said this would be constant over all sub-tiles in the tile!)
    'subtile_upper_left_pixel_columnindex',    # column index of upper left pixel in this sub-tile  (in full tile pixel-coordinates: (0...fulltile_pixel_columns-1)
    'subtile_upper_left_pixel_rowindex',       # row index of upper left pixel in this sub-tile (in full full tile pixel-coordinates: (0...fulltile_pixel_rows-1)
    'subtile_bottom_right_pixel_columnindex',  # column index of bottom right pixel in this sub-tile  (in full tile pixel-coordinates: (0...fulltile_pixel_columns-1)
    'subtile_bottom_right_pixel_rowindex'])    # row index of bottom right pixel in this sub-tile (in full full tile pixel-coordinates: (0...fulltile_pixel_rows-1)

#
#
#
def g_subtiles_in_tile(fulltilecols, fulltilerows, maxcolsinsubtile, maxrowsinsubtile, verbose = False):
    """
    """
    #
    #
    #
    if ( (int(fulltilecols)     != fulltilecols)     or (fulltilecols     <= 0) ): raise ValueError("fulltilecols must be positive integer(is %s)" % (fulltilecols))
    if ( (int(fulltilerows)     != fulltilerows)     or (fulltilerows     <= 0) ): raise ValueError("fulltilerows must be positive integer(is %s)" % (fulltilerows))
    if ( (int(maxcolsinsubtile) != maxcolsinsubtile) or (maxcolsinsubtile <= 0) ): raise ValueError("maxcolsinsubtile must be positive integer(is %s)" % (maxcolsinsubtile))
    if ( (int(maxrowsinsubtile) != maxrowsinsubtile) or (maxrowsinsubtile <= 0) ): raise ValueError("maxrowsinsubtile must be positive integer(is %s)" % (maxrowsinsubtile))

    if maxcolsinsubtile > fulltilecols: maxcolsinsubtile = fulltilecols
    if maxrowsinsubtile > fulltilerows: maxrowsinsubtile = fulltilerows

    fulltile_pixel_columns   = fulltilecols
    fulltile_pixel_rows      = fulltilerows

    fulltile_subtile_columns = int(fulltile_pixel_columns/maxcolsinsubtile) if (fulltile_pixel_columns%maxcolsinsubtile == 0) else int(fulltile_pixel_columns/maxcolsinsubtile) + 1
    fulltile_subtile_rows    = int(fulltile_pixel_rows/maxrowsinsubtile)    if (fulltile_pixel_rows%maxrowsinsubtile    == 0) else int(fulltile_pixel_rows/maxrowsinsubtile) + 1

    for fulltile_subtile_rowindex in range(0, fulltile_subtile_rows):
        for fulltile_subtile_columnindex in range(0, fulltile_subtile_columns):

            subtile_upper_left_pixel_columnindex   = fulltile_subtile_columnindex * maxcolsinsubtile
            subtile_upper_left_pixel_rowindex      = fulltile_subtile_rowindex    * maxrowsinsubtile
            subtile_bottom_right_pixel_columnindex = subtile_upper_left_pixel_columnindex + maxcolsinsubtile - 1 if subtile_upper_left_pixel_columnindex + maxcolsinsubtile < fulltile_pixel_columns else fulltile_pixel_columns - 1
            subtile_bottom_right_pixel_rowindex    = subtile_upper_left_pixel_rowindex    + maxrowsinsubtile - 1 if subtile_upper_left_pixel_rowindex    + maxrowsinsubtile < fulltile_pixel_rows    else fulltile_pixel_rows    - 1
            subtile_pixel_columns                  = subtile_bottom_right_pixel_columnindex - subtile_upper_left_pixel_columnindex + 1
            subtile_pixel_rows                     = subtile_bottom_right_pixel_rowindex    - subtile_upper_left_pixel_rowindex    + 1

            if verbose: logging.info("Tile cols(%s) rows(%s) subtiles(%s x %s) : Subtile(%s, %s) ul(%s, %s)  br(%s, %s) - cols(%s) rows(%s)"%(fulltile_pixel_columns, fulltile_pixel_rows, fulltile_subtile_columns, fulltile_subtile_rows, fulltile_subtile_columnindex, fulltile_subtile_rowindex, subtile_upper_left_pixel_columnindex, subtile_upper_left_pixel_rowindex, subtile_bottom_right_pixel_columnindex, subtile_bottom_right_pixel_rowindex, subtile_pixel_columns, subtile_pixel_rows))
            yield SubtileRasterInfo(
                fulltile_pixel_columns,                 fulltile_pixel_rows,                 # count pixels in full tile 
                fulltile_subtile_columns,               fulltile_subtile_rows,               # count subtiles in full tile 
                fulltile_subtile_columnindex,           fulltile_subtile_rowindex,           # this subtile - indices in full tile
                subtile_pixel_columns,                  subtile_pixel_rows,                  # this subtile - count pixels in subtile
                subtile_upper_left_pixel_columnindex,   subtile_upper_left_pixel_rowindex,   # this subtile top left pixel     - indices in full tile    
                subtile_bottom_right_pixel_columnindex, subtile_bottom_right_pixel_rowindex) # this subtile bottom right pixel - indices in full tile       

#
#
#
def g_subtiles_in_roi(fulltilecols, fulltilerows, roiulcolindex, roiulrowindex, roicols, roirows, maxcolsinsubtile, maxrowsinsubtile, verbose = False):
    """
    """
    #
    #
    #
    if ( (int(fulltilecols)     != fulltilecols)     or (fulltilecols     <= 0) ): raise ValueError("fulltilecols must be positive integer(is %s)" % (fulltilecols))
    if ( (int(fulltilerows)     != fulltilerows)     or (fulltilerows     <= 0) ): raise ValueError("fulltilerows must be positive integer(is %s)" % (fulltilerows))
    if ( (int(roiulcolindex)    != roiulcolindex)    or (roiulcolindex    <  0) ): raise ValueError("roiulcolindex must be positive integer or 0 (is %s)" % (roiulcolindex))
    if ( (int(roiulrowindex)    != roiulrowindex)    or (roiulrowindex    <  0) ): raise ValueError("roiulrowindex must be positive integer or 0 (is %s)" % (roiulrowindex))
    if ( (int(roicols)          != roicols)          or (roicols          <= 0) ): raise ValueError("roicols must be positive integer(is %s)" % (roicols))
    if ( (int(roirows)          != roirows)          or (roirows          <= 0) ): raise ValueError("roirows must be positive integer(is %s)" % (roirows))
    if ( (int(maxcolsinsubtile) != maxcolsinsubtile) or (maxcolsinsubtile <= 0) ): raise ValueError("maxcolsinsubtile must be positive integer(is %s)" % (maxcolsinsubtile))
    if ( (int(maxrowsinsubtile) != maxrowsinsubtile) or (maxrowsinsubtile <= 0) ): raise ValueError("maxrowsinsubtile must be positive integer(is %s)" % (maxrowsinsubtile))

    if fulltilecols <= roiulcolindex: raise ValueError("roiulcolindex outside roi (must be < %s, is %s)" % (fulltilecols, roiulcolindex))
    if fulltilerows <= roiulrowindex: raise ValueError("roiulrowindex outside roi (must be < %s, is %s)" % (fulltilerows, roiulrowindex))

    if fulltilecols < roiulcolindex + roicols: roicols = fulltilecols - roiulcolindex  
    if fulltilerows < roiulrowindex + roirows: roirows = fulltilerows - roiulrowindex  

    for s in g_subtiles_in_tile(roicols, roirows, maxcolsinsubtile, maxrowsinsubtile, False):
        r = SubtileRasterInfo(
            s.fulltile_pixel_columns,                                 s.fulltile_pixel_rows,
            s.fulltile_subtile_columns,                               s.fulltile_subtile_rows,
            s.fulltile_subtile_columnindex,                           s.fulltile_subtile_rowindex,
            s.subtile_pixel_columns,                                  s.subtile_pixel_rows,
            s.subtile_upper_left_pixel_columnindex   + roiulcolindex, s.subtile_upper_left_pixel_rowindex   + roiulrowindex,
            s.subtile_bottom_right_pixel_columnindex + roiulcolindex, s.subtile_bottom_right_pixel_rowindex + roiulrowindex)
        if verbose: logging.info("Tile cols(%s) rows(%s) Roi ul(%s, %s) cols(%s) rows(%s) subtiles(%s x %s) : Subtile(%s, %s) ul(%s, %s)  br(%s, %s) - cols(%s) rows(%s)"%(fulltilecols, fulltilerows, roiulcolindex, roiulrowindex, r.fulltile_pixel_columns, r.fulltile_pixel_rows, r.fulltile_subtile_columns, r.fulltile_subtile_rows, r.fulltile_subtile_columnindex, r.fulltile_subtile_rowindex, r.subtile_upper_left_pixel_columnindex, r.subtile_upper_left_pixel_rowindex, r.subtile_bottom_right_pixel_columnindex, r.subtile_bottom_right_pixel_rowindex, r.subtile_pixel_columns, r.subtile_pixel_rows))
        yield r

