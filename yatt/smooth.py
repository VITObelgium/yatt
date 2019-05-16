import logging
import numpy
import numbers

#
#
#
def makedatacube(listofdatarasters, listofflagrasters=None, minimumdatavalue=None, maximumdatavalue=None, verbose=True):
    """
    list of data rasters: periodic list containing either numpy.ndarray's containing the data or None for missing periods 
    list of flag rasters: periodic list containing either boolean numpy.ndarray's of identical shape as the data or None for missing periods
    minimum data value and maximum data value: indicating valid range of the values in the data rasters

    performs basic checks on input data. converts list of input rasters to numpy cube in which flagged values and values out
    of range are replaced with nan's and missing rasters are replaced with rasters filled with nan's
    """
    #
    #    no list of data, nothing to be done
    #
    if listofdatarasters is None or len(listofdatarasters) <= 0 : raise ValueError("list of data rasters cannot be None nor empty")
    #
    #    no valid rasters in list, nothing to be done
    #
    firstavailabledataraster = next((raster for raster in listofdatarasters if raster is not None), None)
    if firstavailabledataraster is None : raise ValueError("list of data rasters must contain at least one actual data raster")
    #
    #    reference shape from first data raster
    #
    datarastershape = numpy.asarray(firstavailabledataraster).shape
    #
    #    basic check on list of masks if it is there
    #
    if listofflagrasters is not None:
        if len(listofflagrasters) != len(listofdatarasters) : raise ValueError("list of data rasters and list of flag rasters must have identical size")
    #
    #    check minimum data value & maximum data value: at least strings will be thrown out
    #
    if minimumdatavalue is not None:
        if not isinstance(minimumdatavalue, numbers.Number): raise ValueError("minimum data value '{0}' must be number".format(minimumdatavalue))
    if maximumdatavalue is not None:
        if not isinstance(maximumdatavalue, numbers.Number): raise ValueError("maximum data value '{0}' must be number".format(maximumdatavalue))
    #
    #    allocate the cube
    #
    numpydatacube = numpy.full(( len(listofdatarasters), ) + datarastershape, numpy.nan, dtype=float)
    #
    #    fill it out 
    #
    for iIdx in range(len(listofdatarasters)):

        if listofdatarasters[iIdx] is not None:
            #
            #    available rasters are copied in to arrays of float
            #
            numpydataraster = numpy.array(listofdatarasters[iIdx], dtype=float)
            #
            #    verify dimensions
            #
            if numpydataraster.shape != datarastershape:raise ValueError("all data rasters in list of data rasters must have identical shapes")
            #
            #    allocate mask raster
            #
            numpymaskraster = numpy.full_like(numpydataraster, False, dtype=bool)
            #
            #    boolean raster to restrict operations to actual values
            #
            numpynotnanraster = ~numpy.isnan(numpydataraster)
            #
            #    mask flagged values
            #
            if listofflagrasters is not None and listofflagrasters[iIdx] is not None: 
                numpyflagraster = numpy.asarray(listofflagrasters[iIdx], dtype=bool)
                #
                #    verify dimensions
                #
                if numpyflagraster.shape != datarastershape:raise ValueError("data rasters and flag rasters must have identical shapes")
                #
                #    flag only where actual values are present
                #
                numpymaskraster[numpynotnanraster] |= numpyflagraster[numpynotnanraster] 
            #
            #    mask where actual values are out of range
            #
            if minimumdatavalue is not None: numpymaskraster[numpynotnanraster] |= numpydataraster[numpynotnanraster] < minimumdatavalue 
            if maximumdatavalue is not None: numpymaskraster[numpynotnanraster] |= numpydataraster[numpynotnanraster] > maximumdatavalue 
            #
            #    now apply mask
            #
            numpydataraster[numpymaskraster] = numpy.nan
            #
            #    copy result into the cube
            #
            if numpy.isscalar(numpydatacube[iIdx]):
                numpydatacube[iIdx] = numpydataraster
            else:
                numpydatacube[iIdx, :] = numpydataraster

    if verbose: logging.info("makedatacube - resulting shape:%s"%(numpydatacube.shape,))
    #
    #
    #
    return numpydatacube

#
#
#
def makesimplelimitscube(numpydatacube, limit=None):
    """
    """
    #
    #
    #
    if limit is None : return None
    #
    #
    #
    def simplelimitsrasterfunction(iIdx, numpydataraster ):
        numpylimitsraster = numpy.full_like(numpydataraster, numpy.nan, dtype=float)
        numpylimitsraster[~numpy.isnan(numpydataraster)] = limit
        return numpylimitsraster
    #
    #
    #
    return makelimitscube(numpydatacube, simplelimitsrasterfunction)

#
#
#
def makelimitscube(numpydatacube, zelimitsrasterfunction):
    """
    """
    #
    #
    #
    if zelimitsrasterfunction is None : return makesimplelimitscube(numpydatacube)
    #
    #
    #
    numberofrasters = numpydatacube.shape[0]
    #
    #
    #
    numpylimitsscube = numpy.full_like(numpydatacube, numpy.nan, dtype=float)
    #
    #
    #
    for iIdx in range(numberofrasters):
        if numpy.isscalar(numpydatacube[iIdx]):
            numpylimitsscube[iIdx] = zelimitsrasterfunction(iIdx, numpydatacube[iIdx])
        else:
            numpylimitsscube[iIdx, :] = zelimitsrasterfunction(iIdx, numpydatacube[iIdx])

    return numpylimitsscube

#
#
#    
def flaglocalminima(numpydatacube, maxdipvalueornumpycube=None, maxdifvalueornumpycube=None, maxgap=None, maxpasses=1, verbose=True):
    """
    """
    return _flaglocalextrema(numpydatacube, maxdipvalueornumpycube, maxdifvalueornumpycube, maxgap=maxgap, maxpasses=maxpasses, doflagmaxima=False, verbose=verbose)

#
#
#    
def flaglocalmaxima(numpydatacube, maxdipvalueornumpycube=None, maxdifvalueornumpycube=None, maxgap=None, maxpasses=1, verbose=True):
    """
    """
    return _flaglocalextrema(numpydatacube, maxdipvalueornumpycube, maxdifvalueornumpycube, maxgap=maxgap, maxpasses=maxpasses, doflagmaxima=True, verbose=verbose)

#
#
#
def _flaglocalextrema(numpydatacube, maxdipvalueornumpycube, maxdifvalueornumpycube, maxgap=None, maxpasses=1, doflagmaxima=False, verbose=True):
    """
    """
    #
    #
    #
    if maxgap is not None and ( (int(maxgap) != maxgap) or (maxgap <= 0) ): raise ValueError("maxgap must be positive integer or None (is %s)" % (maxgap))
    #
    #
    #
    numpymaxdipcube = None
    if maxdipvalueornumpycube is not None:
        if numpy.isscalar(maxdipvalueornumpycube):
            numpymaxdipcube = makesimplelimitscube(numpydatacube, maxdipvalueornumpycube)
        else:
            numpymaxdipcube = maxdipvalueornumpycube
        if numpymaxdipcube.shape != numpydatacube.shape:                                       raise ValueError("maximum dip and data cube must have identical shapes")
        if not numpy.allclose(numpymaxdipcube.astype(float), numpymaxdipcube, equal_nan=True): raise ValueError("maximum dip cube must contain numeric values")
        if numpy.any((numpymaxdipcube[~numpy.isnan(numpymaxdipcube)] <= 0)):                   raise ValueError("maximum dip cube must contain positive values")

    numpymaxdifcube = None
    if maxdifvalueornumpycube is not None:
        if numpy.isscalar(maxdifvalueornumpycube):
            numpymaxdifcube = makesimplelimitscube(numpydatacube, maxdifvalueornumpycube)
        else:
            numpymaxdifcube = maxdifvalueornumpycube
        if numpymaxdifcube.shape != numpydatacube.shape:                                       raise ValueError("maximum dif and data cube must have identical shapes")
        if not numpy.allclose(numpymaxdifcube.astype(float), numpymaxdifcube, equal_nan=True): raise ValueError("maximum dif cube must contain numeric values")
        if numpy.any(numpymaxdifcube[~numpy.isnan(numpymaxdifcube)] <= 0):                     raise ValueError("maximum dif cube must contain positive values")
    #
    #
    #
    def masklocalminima(currentraster, neighbourraster, maxdifferenceraster):
        #
        #    in case of scalars, any nan's present will give no run-time-warning, and result in False
        #    in case of rasters, only indices without nan's will pass here - hence no run-time-warnings
        #
        return (neighbourraster - currentraster) > maxdifferenceraster
    def masklocalmaxima(currentraster, neighbourraster, maxdifferenceraster):
        return (currentraster - neighbourraster) > maxdifferenceraster
    if doflagmaxima: 
        maskextrema = masklocalmaxima
    else:
        maskextrema = masklocalminima
    #
    #
    #
    numberofrasters = numpydatacube.shape[0]
    #
    #
    #
    defaultindexraster = numpy.full_like(numpydatacube[0], -1, dtype=int)
    defaultvalueraster = numpy.full_like(numpydatacube[0], numpy.nan, dtype=float)

    initialnumberofvalues  = numpy.sum(~numpy.isnan(numpydatacube))
    previousnumberofvalues = initialnumberofvalues
    for iteration in range(maxpasses):
        for iIdx in range(numberofrasters):
            #
            #
            #
            notnansmask = ~numpy.isnan(numpydatacube[iIdx])
            if not notnansmask.any(): continue # save some time
            #
            #
            #
            prevrasterindiceschoicelist = range(iIdx)[::-1] # reversed
            prevrasterindicescondlist   = [~numpy.isnan(numpydatacube[i])      for i in prevrasterindiceschoicelist]
            prevrasterindices           = numpy.select(prevrasterindicescondlist, prevrasterindiceschoicelist, default=defaultindexraster)

            prevrastervalueschoicelist  = [numpydatacube[i]                    for i in prevrasterindiceschoicelist]
            prevrastervaluescondlist    = [prevrasterindices == i              for i in prevrasterindiceschoicelist]
            prevrastervalues            = numpy.select(prevrastervaluescondlist, prevrastervalueschoicelist, default=defaultvalueraster)


            nextrasterindiceschoicelist = range(iIdx+1,numberofrasters)
            nextrasterindicescondlist   = [~numpy.isnan(numpydatacube[i])      for i in nextrasterindiceschoicelist]
            nextrasterindices           = numpy.select(nextrasterindicescondlist, nextrasterindiceschoicelist, default=defaultindexraster)

            nextrastervalueschoicelist  = [numpydatacube[i]                    for i in nextrasterindiceschoicelist]
            nextrastervaluescondlist    = [nextrasterindices == i              for i in nextrasterindiceschoicelist]
            nextrastervalues            = numpy.select(nextrastervaluescondlist, nextrastervalueschoicelist, default=defaultvalueraster)

            prevrasterdistance          = iIdx - prevrasterindices
            nextrasterdistance          = nextrasterindices - iIdx
            #
            #
            #
            comparabletoprev = notnansmask & ~numpy.isnan(prevrastervalues)
            if maxgap is not None: comparabletoprev &= prevrasterdistance < maxgap

            comparabletonext = notnansmask & ~numpy.isnan(nextrastervalues)
            if maxgap is not None: comparabletonext &= nextrasterdistance < maxgap

            comparabletoboth = comparabletoprev & comparabletonext
            #
            #
            #
            isextremum = None
            isdip      = None
            #
            #
            #
            if numpy.isscalar(numpydatacube[iIdx]):

                if numpymaxdipcube is not None: 
                    isextremum = comparabletoboth
                    isextremum &= maskextrema(numpydatacube[iIdx], prevrastervalues, (prevrasterdistance * numpymaxdipcube[iIdx]))
                    isextremum &= maskextrema(numpydatacube[iIdx], nextrastervalues, (nextrasterdistance * numpymaxdipcube[iIdx]))

                if numpymaxdifcube is not None: 
                    isdip = False
                    isdip  = maskextrema(numpydatacube[iIdx], prevrastervalues, (prevrasterdistance * numpymaxdifcube[iIdx]))
                    isdip |= maskextrema(numpydatacube[iIdx], nextrastervalues, (nextrasterdistance * numpymaxdifcube[iIdx]))

                if isextremum or isdip : numpydatacube[iIdx] = numpy.nan

            else:
                #
                #    only raster indices without nan's in previous, current and next will be passed for comparison - hence no run-time-warnings
                #
                if numpymaxdipcube is not None: 
                    isextremum = numpy.copy(comparabletoboth)
                    isextremum[isextremum] &= maskextrema(numpydatacube[iIdx][isextremum], prevrastervalues[isextremum], (prevrasterdistance * numpymaxdipcube[iIdx])[isextremum])
                    isextremum[isextremum] &= maskextrema(numpydatacube[iIdx][isextremum], nextrastervalues[isextremum], (nextrasterdistance * numpymaxdipcube[iIdx])[isextremum])

                if numpymaxdifcube is not None: 
                    isdip = numpy.full_like(comparabletoboth, False, dtype=bool)
                    isdip[comparabletoboth]  = maskextrema(numpydatacube[iIdx][comparabletoboth], prevrastervalues[comparabletoboth], (prevrasterdistance *  numpymaxdifcube[iIdx])[comparabletoboth])
                    isdip[comparabletoboth] |= maskextrema(numpydatacube[iIdx][comparabletoboth], nextrastervalues[comparabletoboth], (nextrasterdistance *  numpymaxdifcube[iIdx])[comparabletoboth])

                if isextremum is not None : numpydatacube[iIdx][isextremum] = numpy.nan            
                if isdip      is not None : numpydatacube[iIdx][isdip]      = numpy.nan            

        remainingnumberofvalues = numpy.sum(~numpy.isnan(numpydatacube))
        removednumberofvalues   = previousnumberofvalues - remainingnumberofvalues
        if verbose: logging.info("flaglocalextrema pass : %s removed %s values. %s values remaining. %s values removed in total" % (iteration+1, removednumberofvalues, remainingnumberofvalues, initialnumberofvalues - remainingnumberofvalues))
        previousnumberofvalues = remainingnumberofvalues
        if removednumberofvalues <= 0 and 1 < maxpasses:
            if verbose: logging.info("flaglocalextrema pass : %s - exits" % (iteration+1))
            break

    #
    #
    #
    return numpydatacube

#
#
#
def linearinterpolation(numpydatacube):
    """
    simple linear interpolation
    """
    #
    #
    #
    numberofrasters = numpydatacube.shape[0]
    #
    #
    #
    defaultindexraster = numpy.full_like(numpydatacube[0], -1, dtype=int)
    defaultvalueraster = numpy.full_like(numpydatacube[0], numpy.nan, dtype=float)
    #
    #
    #
    for iIdx in range(numberofrasters):
        #
        #
        #
        prevrasterindiceschoicelist = range(iIdx)[::-1] # reversed
        prevrasterindicescondlist   = [~numpy.isnan(numpydatacube[i])      for i in prevrasterindiceschoicelist]
        prevrasterindices           = numpy.select(prevrasterindicescondlist, prevrasterindiceschoicelist, default=defaultindexraster)

        prevrastervalueschoicelist  = [numpydatacube[i]                    for i in prevrasterindiceschoicelist]
        prevrastervaluescondlist    = [prevrasterindices == i              for i in prevrasterindiceschoicelist]
        prevrastervalues            = numpy.select(prevrastervaluescondlist, prevrastervalueschoicelist, default=defaultvalueraster)


        nextrasterindiceschoicelist = range(iIdx+1,numberofrasters)
        nextrasterindicescondlist   = [~numpy.isnan(numpydatacube[i])      for i in nextrasterindiceschoicelist]
        nextrasterindices           = numpy.select(nextrasterindicescondlist, nextrasterindiceschoicelist, default=defaultindexraster)

        nextrastervalueschoicelist  = [numpydatacube[i]                    for i in nextrasterindiceschoicelist]
        nextrastervaluescondlist    = [nextrasterindices == i              for i in nextrasterindiceschoicelist]
        nextrastervalues            = numpy.select(nextrastervaluescondlist, nextrastervalueschoicelist, default=defaultvalueraster)

        interpolatedrastervalues    = prevrastervalues + (nextrastervalues - prevrastervalues)/(nextrasterindices-prevrasterindices)*(iIdx - prevrasterindices)

        if numpy.isscalar(numpydatacube[iIdx]):
            if numpy.isnan(numpydatacube[iIdx]) :
                numpydatacube[iIdx] = interpolatedrastervalues
        else:
            numpydatacube[iIdx][numpy.isnan(numpydatacube[iIdx])] = interpolatedrastervalues[numpy.isnan(numpydatacube[iIdx])]
    #
    #
    #
    return numpydatacube

#
#
#
def movingaverage(numpydatacube, windowsize):
    """
    simple moving average using a sliding window.
    :param numpydatacube - can be a numpy array of scalars (including nan's) or a numpy array of rasters (preferably use the makedatacube function, and solve it there in case problems/bugs occur)
    :param windowsize - width of the sliding window, at least 2, preferably odd. In case windowsize is even, the left side will be 1 index greater than the right side.
    """
    #
    #    left and right distances for point in window
    #    odd  windows: 3,5,7,... => left == right = 1,2,3
    #    even windows: 2,4,6,... => left = 1,2,3 right = 0,1,2
    #
    if((int(windowsize)  != windowsize)  or (windowsize  < 2)): raise ValueError("windowsize must be an int >= 2")
    left_windowsize  = int(windowsize / 2) ; right_windowsize = left_windowsize
    if ( windowsize == 2 * right_windowsize ) : right_windowsize -= 1
    #
    #
    #
    numberofrasters = numpydatacube.shape[0]
    #
    #
    #
    numpynotnancube = ~numpy.isnan(numpydatacube)
    numpyzeroedcube = numpy.copy(numpydatacube) ; numpyzeroedcube[~numpynotnancube] = 0
    numpymovavgcube = numpy.full_like(numpydatacube, numpy.nan, dtype=float)
    numpymovcntcube = numpy.full_like(numpydatacube, 0,         dtype=int)
    #
    #
    #
    numpymovavgcube[0] = numpy.sum(numpyzeroedcube[0 : right_windowsize + 1], axis=0)
    numpymovcntcube[0] = numpy.sum(numpynotnancube[0 : right_windowsize + 1], axis=0)
    #
    #
    #
    for iIdx in range(1, numberofrasters):
        #
        #
        #
        toAddIdx = iIdx + right_windowsize
        toRemIdx = iIdx - left_windowsize - 1

        numpymovavgcube[iIdx] = numpymovavgcube[iIdx-1]
        numpymovcntcube[iIdx] = numpymovcntcube[iIdx-1]

        if toAddIdx < numberofrasters: 
            numpymovavgcube[iIdx] = numpymovavgcube[iIdx] + numpyzeroedcube[toAddIdx]
            numpymovcntcube[iIdx] = numpymovcntcube[iIdx] + numpynotnancube[toAddIdx]
        if 0 <= toRemIdx :  
            numpymovavgcube[iIdx] = numpymovavgcube[iIdx] - numpyzeroedcube[toRemIdx]
            numpymovcntcube[iIdx] = numpymovcntcube[iIdx] - numpynotnancube[toRemIdx]
    #
    #
    #
    numpymovavgcube[numpymovcntcube != 0] /= numpymovcntcube[numpymovcntcube != 0]
    numpymovavgcube[numpymovcntcube == 0] = numpy.nan
    #
    #
    #
    return numpymovavgcube

#
#
#
class WeightTypeId(object):
    """
    keys to be used in dicts etc.
    """
    MAXIMUM     = 1 
    MINIMUM     = 2
    POSSLOPE    = 3
    NEGSLOPE    = 4
    ABOUTEQUAL  = 5
    DEFAULT     = 99

#
#
#
class WeightValues(object):
    """
    """

    #
    #
    #
    _defaultweightvalue = 1.0

    #
    #
    #
    @staticmethod
    def defaultWeightValues():
        """"
        returns WeightValues instance 
        """
        return WeightValues(
            maximum    = WeightValues._defaultweightvalue, 
            minimum    = WeightValues._defaultweightvalue, 
            posslope   = WeightValues._defaultweightvalue, 
            negslope   = WeightValues._defaultweightvalue, 
            aboutequal = WeightValues._defaultweightvalue, 
            default    = WeightValues._defaultweightvalue)

    #
    #
    #
    def __init__(self, maximum, minimum, posslope, negslope, aboutequal, default):

        if maximum    is not None and ( (float(maximum)    != maximum)    or (maximum    < 0) ): raise ValueError(" weight for 'maximum' must be positive value or None (is %s)"  % (maximum))
        if minimum    is not None and ( (float(minimum)    != minimum)    or (minimum    < 0) ): raise ValueError(" weight for 'minimum' must be positive value or None (is %s)"  % (minimum))
        if posslope   is not None and ( (float(posslope)   != posslope)   or (posslope   < 0) ): raise ValueError(" weight for 'positive slope' must be positive value or None (is %s)" % (posslope))
        if negslope   is not None and ( (float(negslope)   != negslope)   or (negslope   < 0) ): raise ValueError(" weight for 'negative slope' must be positive value or None (is %s)" % (negslope))
        if aboutequal is not None and ( (float(aboutequal) != aboutequal) or (aboutequal < 0) ): raise ValueError(" weight for 'equal' must be positive value or None (is %s)" % (aboutequal))
        if default    is not None and ( (float(default)    != default)    or (default    < 0) ): raise ValueError(" weight for 'default' must be positive value, nan or None (is %s)" % (default))


        self._weightsdict = dict({
            WeightTypeId.MAXIMUM    :  WeightValues._defaultweightvalue if maximum    is None else maximum,
            WeightTypeId.MINIMUM    :  WeightValues._defaultweightvalue if minimum    is None else minimum,
            WeightTypeId.POSSLOPE   :  WeightValues._defaultweightvalue if posslope   is None else posslope, 
            WeightTypeId.NEGSLOPE   :  WeightValues._defaultweightvalue if negslope   is None else negslope,
            WeightTypeId.ABOUTEQUAL :  WeightValues._defaultweightvalue if aboutequal is None else aboutequal,
            WeightTypeId.DEFAULT    :  WeightValues._defaultweightvalue if default    is None else default,
            })
    #
    #
    #
    def copy(self, maximum=None, minimum=None, posslope=None, negslope=None, aboutequal=None, default=None):
        """
        """
        if maximum    is not None and ( (float(maximum)    != maximum)    or (maximum    < 0) ):    raise ValueError(" weight for 'maximum' must be positive value or None (is %s)"  % (maximum))
        if minimum    is not None and ( (float(minimum)    != minimum)    or (minimum    < 0) ):    raise ValueError(" weight for 'minimum' must be positive value or None (is %s)"  % (minimum))
        if posslope   is not None and ( (float(posslope)   != posslope)   or (posslope   < 0) ):    raise ValueError(" weight for 'positive slope' must be positive value or None (is %s)" % (posslope))
        if negslope   is not None and ( (float(negslope)   != negslope)   or (negslope   < 0) ):    raise ValueError(" weight for 'negative slope' must be positive value or None (is %s)" % (negslope))
        if aboutequal is not None and ( (float(aboutequal) != aboutequal) or (aboutequal < 0) ):    raise ValueError(" weight for 'equal' must be positive value or None (is %s)" % (aboutequal))
        if default    is not None and ( (float(default)    != default)    or (default    < 0) ):    raise ValueError(" weight for 'default' must be positive value or None (is %s)" % (default))

        return WeightValues(self._weightsdict[WeightTypeId.MAXIMUM]    if maximum    is None else maximum,
                            self._weightsdict[WeightTypeId.MINIMUM]    if minimum    is None else minimum,
                            self._weightsdict[WeightTypeId.POSSLOPE]   if posslope   is None else posslope,
                            self._weightsdict[WeightTypeId.NEGSLOPE]   if negslope   is None else negslope,
                            self._weightsdict[WeightTypeId.ABOUTEQUAL] if aboutequal is None else aboutequal,
                            self._weightsdict[WeightTypeId.DEFAULT]    if default    is None else default)

    #
    #
    #
    def getweightsdict(self):
        return self._weightsdict.copy()

    #
    #
    #
    def getweight(self, weighttypeid):
        """
        will throw on invalid key. any compiler could prevent this.
        """
        return self._weightsdict[weighttypeid]

#
#
#
defaultswetsweightvalues = WeightValues(
    maximum    =  1.5,
    minimum    =  0.005,
    posslope   =  0.5,
    negslope   =  0.5,
    aboutequal =  1.0,
    default    =  0.0)

#
#
#
def makeweighttypescube(numpydatacube, aboutequalepsilon=0):
    """
    """

    #
    #
    #
    if aboutequalepsilon is not None and ( (float(aboutequalepsilon) != aboutequalepsilon) or (aboutequalepsilon < 0) ): raise ValueError("'about equal epsilon' must be positive value or None (is %s)"   % (aboutequalepsilon))
    #
    #
    #
    epsilon = aboutequalepsilon if aboutequalepsilon is not None else 0
    #
    #    ! will be used in numpy.select statement => sequence matters
    #
    weighttypeslist = [
        WeightTypeId.ABOUTEQUAL, 
        WeightTypeId.MAXIMUM, 
        WeightTypeId.MINIMUM, 
        WeightTypeId.POSSLOPE,
        WeightTypeId.NEGSLOPE]
    #
    #
    #
    numpyweighttypescube = numpy.full_like(numpydatacube, WeightTypeId.DEFAULT, dtype = int)

    curr_GT_prev     = numpy.empty_like(numpydatacube[0], dtype=bool)
    curr_GT_next     = numpy.empty_like(numpydatacube[0], dtype=bool)
    curr_LT_prev     = numpy.empty_like(numpydatacube[0], dtype=bool)
    curr_LT_next     = numpy.empty_like(numpydatacube[0], dtype=bool)
    curr_EQ_prev     = numpy.empty_like(numpydatacube[0], dtype=bool)
    curr_EQ_next     = numpy.empty_like(numpydatacube[0], dtype=bool)

    #
    #
    #
    numberofrasters = numpydatacube.shape[0]
    #
    #
    #
    defaultweightraster = numpy.full_like(numpydatacube[0], WeightTypeId.DEFAULT, dtype = int)
    #
    #
    #
    for iIdx in range(numberofrasters):

        #
        #    'previous' raster values can be obtained from leading rasters
        #
        leadingavailableindices    = range(iIdx)[::-1]
        prevvaluesrasterchoicelist = [numpydatacube[i]                    for i in leadingavailableindices]
        prevvaluesrastercondlist   = [~numpy.isnan(numpydatacube[i])      for i in leadingavailableindices]
        prevvaluesraster           = numpy.select(prevvaluesrastercondlist, prevvaluesrasterchoicelist, default=numpydatacube[iIdx])    #defaults to current raster - stretching (could contain nan's)
        #
        #    'next' raster values can be obtained from trailing rasters
        #
        trailingavailableindices   = range(iIdx+1,numberofrasters)
        nextvaluesrasterchoicelist = [numpydatacube[i]                    for i in trailingavailableindices]
        nextvaluesrastercondlist   = [~numpy.isnan(numpydatacube[i])      for i in trailingavailableindices]
        nextvaluesraster           = numpy.select(nextvaluesrastercondlist, nextvaluesrasterchoicelist, default=numpydatacube[iIdx])    #defaults to current raster - stretching (could contain nan's)
        #
        #    
        #
        notnanmask    = ~numpy.isnan(numpydatacube[iIdx])   
        deltacurrprev = numpydatacube[iIdx][notnanmask] - prevvaluesraster[notnanmask] # prevvaluesraster can contain nan's only where numpydatacube[iIdx] does due to default selection above
        deltacurrnext = numpydatacube[iIdx][notnanmask] - nextvaluesraster[notnanmask] # nextvaluesraster can contain nan's only where numpydatacube[iIdx] does due to default selection above

        curr_GT_prev.fill(False);  curr_GT_prev[notnanmask] = deltacurrprev > 0.
        curr_GT_next.fill(False);  curr_GT_next[notnanmask] = deltacurrnext > 0.
        curr_LT_prev.fill(False);  curr_LT_prev[notnanmask] = deltacurrprev < 0.
        curr_LT_next.fill(False);  curr_LT_next[notnanmask] = deltacurrnext < 0.
        curr_EQ_prev.fill(False);  curr_EQ_prev[notnanmask] = numpy.absolute(deltacurrprev) < epsilon
        curr_EQ_next.fill(False);  curr_EQ_next[notnanmask] = numpy.absolute(deltacurrnext) < epsilon

        weightcondlist = [
            (curr_EQ_prev & curr_EQ_next),
            (curr_GT_prev & curr_GT_next),
            (curr_LT_prev & curr_LT_next),
            (curr_GT_prev | curr_LT_next),
            (curr_LT_prev | curr_LT_next)]

        numpyweighttypescube[iIdx] = numpy.select(weightcondlist, weighttypeslist, defaultweightraster) 

    return numpyweighttypescube

#
#
#
def makesimpleweightscube(weighttypescube, weightvalues = WeightValues.defaultWeightValues()):
    """
    """

    #
    #
    #
    if weightvalues is None : weightvalues = WeightValues.defaultWeightValues()
    #
    #
    #
    numpyweightscube = numpy.full_like(weighttypescube, numpy.nan, dtype=float)

    numpyweightscube[weighttypescube == WeightTypeId.MAXIMUM]    = weightvalues.getweight(WeightTypeId.MAXIMUM)
    numpyweightscube[weighttypescube == WeightTypeId.MINIMUM]    = weightvalues.getweight(WeightTypeId.MINIMUM)
    numpyweightscube[weighttypescube == WeightTypeId.POSSLOPE]   = weightvalues.getweight(WeightTypeId.POSSLOPE)
    numpyweightscube[weighttypescube == WeightTypeId.NEGSLOPE]   = weightvalues.getweight(WeightTypeId.NEGSLOPE)
    numpyweightscube[weighttypescube == WeightTypeId.ABOUTEQUAL] = weightvalues.getweight(WeightTypeId.ABOUTEQUAL)
    numpyweightscube[weighttypescube == WeightTypeId.DEFAULT]    = weightvalues.getweight(WeightTypeId.DEFAULT)

    return numpyweightscube

#
#
#
def makeweightscube(weighttypescube, zeweightsrasterfunction):
    """
    zeweightsrasterfunction: called with parameters (iIdx,weighttypescube[iIdx]),
    is assumed to return a raster, with shape identical to weighttypescube[iIdx],
    and containing the actual weight values per each pixel in the raster, for this index.
    client is assumed to know relation between index and e.g. data, so temporal weights could be implemented 
    client is assumed to know the spatial info about the raster, so land-use dependent weights could be implemented   
    """
    #
    #
    #
    if zeweightsrasterfunction is None : return makesimpleweightscube(weighttypescube)
    #
    #
    #
    numberofrasters = weighttypescube.shape[0]
    #
    #
    #
    numpyweightscube = numpy.full_like(weighttypescube, numpy.nan, dtype=float)
    #
    #
    #
    for iIdx in range(numberofrasters):
        if numpy.isscalar(numpyweightscube[iIdx]):
            numpyweightscube[iIdx] = zeweightsrasterfunction(iIdx, weighttypescube[iIdx])
        else:
            numpyweightscube[iIdx, :] = zeweightsrasterfunction(iIdx, weighttypescube[iIdx])

    return numpyweightscube

#
#
#
def weightedlinearregression(numpydatacube, numpyweightscube=None, minimumdatavalue=None, maximumdatavalue=None):
    """
    weighted linear regression

    minimum data value and maximum data value: indicating valid range in the data rasters
    """
    #
    #    allocate weights cube
    #
    if numpyweightscube is None:
        #
        #    all equal weights - own allocation
        #
        numpyweightscube = numpy.full_like(numpydatacube, 1.0, dtype=float)
    else :
        #
        #    basic check on list of weights
        #
        if numpyweightscube.shape != numpydatacube.shape: raise ValueError("weights cube and data cube must have identical shapes")
        #
        #    allocate own version since we're going to mess with it
        #
        numpyweightscube = numpy.copy(numpyweightscube)
    #
    #
    #
    numberofrasters = numpydatacube.shape[0]
    #
    #    there must be a better way !
    #
    xindicescube = numpy.array( [ numpy.full_like(numpydatacube[0], i, dtype=float) for i in range(numberofrasters) ])
    xdatacube    = numpy.copy(xindicescube)

    isnanscube = numpy.isnan(numpydatacube)
    xdatacube[isnanscube]        = 0
    numpyweightscube[isnanscube] = 0
    #
    #
    #
    while True:
        sw  = numpy.sum(numpyweightscube, axis = 0)
        sy  = numpy.nansum(numpyweightscube * numpydatacube, axis = 0)
        sx  = numpy.sum(numpyweightscube * xdatacube, axis = 0)
        sxy = numpy.nansum(numpyweightscube * numpydatacube * xdatacube, axis = 0)
        sxx = numpy.nansum(numpyweightscube * xdatacube * xdatacube, axis = 0)
        #
        #
        #
        bn = (sw*sxx - sx*sx)
        if numpy.isscalar(bn):
            if bn == 0: bn = numpy.nan
        else:
            bn[(bn == 0)] = numpy.nan
        #
        #
        #
        b = (sw*sxy - sx*sy)/bn
        a = (sy - b*sx)/sw
        numpyregressioncube = a + b * xindicescube
        break
    #
    #    clip regression (non-nan) values to valid range
    #
    notnancube = ~numpy.isnan(numpyregressioncube)
    if maximumdatavalue is not None: 
        exeedingmaximum = numpy.full_like(numpyregressioncube, False, dtype=bool)
        exeedingmaximum[notnancube] = numpyregressioncube[notnancube] > maximumdatavalue
        numpyregressioncube[exeedingmaximum] = maximumdatavalue
    if minimumdatavalue is not None: 
        exeedingminimum = numpy.full_like(numpyregressioncube, False, dtype=bool)
        exeedingminimum[notnancube] = numpyregressioncube[notnancube] < minimumdatavalue
        numpyregressioncube[exeedingminimum] = minimumdatavalue
    #
    #
    #
    return numpyregressioncube

#
#
#
def swets(regressionwindow, combinationwindow, numpydatacube, numpyweightscube= None, minimumdatavalue=None, maximumdatavalue=None):
    """
    """
    #
    #    left and right distances for point in regression window
    #    odd  regression windows: 3,5,7,... => left == right = 1,2,3
    #    even regression windows: 2,4,6,... => left = 1,2,3 right = 0,1,2
    #
    if((int(regressionwindow)  != regressionwindow)  or (regressionwindow  < 2)): 
        raise ValueError("regressionwindow must be an int >= 2")
    left_regression_size  = int(regressionwindow / 2) ; right_regression_size = left_regression_size
    if ( regressionwindow == 2 * right_regression_size ) : right_regression_size -= 1
    #
    #    left and right distances for point in combination window
    #    odd  regression windows: 3,5,7,... => left == right = 1,2,3
    #    even regression windows: 2,4,6,... => left = 1,2,3 right = 0,1,2
    #
    if((int(combinationwindow) != combinationwindow) or (combinationwindow < 1) or (regressionwindow < combinationwindow) ): 
        raise ValueError("combinationwindow must be an int >= 1 and <= regressionwindow (%s)" % (regressionwindow,))
    left_combination_size  = int(combinationwindow / 2) ; right_combination_size = left_combination_size
    if ( combinationwindow == 2 * right_combination_size ) : right_combination_size -= 1
    #
    #
    #
    if numpyweightscube is None:
        numpyweightscube = numpy.full_like(numpydatacube, 1.0)
    else:
        if numpydatacube.shape != numpyweightscube.shape:
            raise ValueError("data cube and weights cube must have identical shapes")
    #
    #
    #
    numberofrasters = numpydatacube.shape[0]

    #
    #
    #
    numpycombinedcube = numpy.zeros_like(numpydatacube, dtype=float)
    numpycountscube   = numpy.zeros_like(numpydatacube, dtype=int)
    #
    #
    #
    for iIdx in range(0,numberofrasters):

        iRegressionFirst = iIdx - left_regression_size
        iRegressionLast  = iIdx + right_regression_size

        if iRegressionFirst < 0 :               iRegressionFirst = 0
        if numberofrasters <= iRegressionLast : iRegressionLast  = numberofrasters - 1

        regressiondatacube    = numpydatacube[iRegressionFirst:iRegressionLast+1]
        regressionweightscube = numpyweightscube[iRegressionFirst:iRegressionLast+1]

        regressionvaluescube = weightedlinearregression(regressiondatacube, regressionweightscube, minimumdatavalue=minimumdatavalue, maximumdatavalue=maximumdatavalue)

        iCombinationFirst = iIdx - left_combination_size
        iCombinationLast  = iIdx + right_combination_size

        #
        #    we assume combinationwindow <= regressionwindow
        #
        if iCombinationFirst < iRegressionFirst : iCombinationFirst = iRegressionFirst
        if iCombinationLast  > iRegressionLast :  iCombinationLast  = iRegressionLast
        #
        #
        #
        combinationvaluescube = regressionvaluescube[iCombinationFirst-iRegressionFirst:iCombinationLast+1-iRegressionFirst]
        combinationnotnancube = ~numpy.isnan(combinationvaluescube)
        numpycombinedcube[iCombinationFirst:iCombinationLast+1][combinationnotnancube] += combinationvaluescube[combinationnotnancube]
        numpycountscube[iCombinationFirst:iCombinationLast+1][combinationnotnancube]   += 1

    #
    #
    #
    numpycombinedcube[numpycountscube==0] = numpy.nan
    numpycombinedcube[numpycountscube!=0] = numpycombinedcube[numpycountscube!=0] / numpycountscube[numpycountscube!=0]
    #
    #
    #
    return numpycombinedcube

#
#
#
def whittaker_first_differences(lmbda, numpydatacube, numpyweightscube=None, minimumdatavalue=None, maximumdatavalue=None, passes=1, dokeepmaxima=False):
    """
    numpydatacubecube data, flagged values and values out of range are indicated with nan's
    """
    return _dowhittaker(lmbda, 1, numpydatacube, numpyweightscube=numpyweightscube, minimumdatavalue=minimumdatavalue, maximumdatavalue=maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)

#
#
#
def whittaker_second_differences(lmbda, numpydatacube, numpyweightscube=None, minimumdatavalue=None, maximumdatavalue=None, passes=1, dokeepmaxima=False):
    """
    """
    return _dowhittaker(lmbda, 2, numpydatacube, numpyweightscube=numpyweightscube, minimumdatavalue=minimumdatavalue, maximumdatavalue=maximumdatavalue, passes=passes, dokeepmaxima=dokeepmaxima)



#
#    hack: act as if available data equidistant - do NOT use this; this is the emulation of a faulty implementation in the initial WIG (before may 2018)
#
def wig_whittaker(lmbda, numpydatacube, numpyweightscube=None, minimumdatavalue=None, maximumdatavalue=None, passes=1, dokeepmaxima=False):
    """
    """
    #
    #
    #
    countRasters = 0
    for iIdx in range(len (numpydatacube) ):
        if not (~numpy.isnan(numpydatacube[iIdx])).any(): continue
        countRasters +=1

    #
    #    reference shape from first data raster
    #
    numpydatarastershape = numpy.asarray(numpydatacube[0]).shape
    #
    #
    #
    zenewnumpydatacube    = numpy.full(( countRasters, ) + numpydatarastershape, numpy.nan, dtype=float)
    zenewnumpyweightscube = numpy.full(( countRasters, ) + numpydatarastershape, numpy.nan, dtype=float) if numpyweightscube is not None else None
    #
    #
    #
    zenewrasterIdx = 0
    for iIdx in range(len (numpydatacube) ):
        if not (~numpy.isnan(numpydatacube[iIdx])).any(): continue
        if numpy.isscalar(numpydatacube[iIdx]):
            zenewnumpydatacube[zenewrasterIdx]    = numpydatacube[iIdx]
            if numpyweightscube is not None: zenewnumpyweightscube[zenewrasterIdx] = numpyweightscube[iIdx]
        else:
            zenewnumpydatacube[zenewrasterIdx][:]    = numpydatacube[iIdx]
            if numpyweightscube is not None: zenewnumpyweightscube[zenewrasterIdx][:] = numpyweightscube[iIdx]
        zenewrasterIdx +=1
    #
    #
    #
    zenewwhittakercube =  _dowhittaker(lmbda, 2, zenewnumpydatacube, zenewnumpyweightscube, minimumdatavalue, maximumdatavalue, passes, dokeepmaxima)
    #
    #
    #
    zewhittakercube = numpy.full_like(numpydatacube, numpy.nan, dtype=float)
    zenewrasterIdx = 0
    for iIdx in range(len (numpydatacube) ):
        if not (~numpy.isnan(numpydatacube[iIdx])).any(): continue
        if numpy.isscalar(numpydatacube[iIdx]):
            zewhittakercube[iIdx] = zenewwhittakercube[zenewrasterIdx]
        else:
            zewhittakercube[iIdx][:] = zenewwhittakercube[zenewrasterIdx]
        zenewrasterIdx +=1
    #
    #
    #
    return linearinterpolation(zewhittakercube)

#
#
#
def _dowhittaker(lmbda, orderofdifferences, numpydatacube, numpyweightscube=None, minimumdatavalue=None, maximumdatavalue=None, passes=1, dokeepmaxima=False):
    """
    """
    #
    #
    #
    if ( (lmbda is None) or (float(lmbda) != lmbda) or (lmbda <= 0) ): raise ValueError("lmbda must be positive value (is %s)" % (lmbda))
    if passes is None : 
        passes = 1
    else:
        if ( (int(passes) != passes) or (passes <= 0) ): raise ValueError("passes must be positive integer or None (is %s)" % (passes))
    #
    #
    #
    if numpyweightscube is None:
        weightscube = numpy.full_like(numpydatacube, 1.0)
    else:
        weightscube = numpy.copy(numpyweightscube)

    
    #
    #    allocate intermediates
    #
    smoothedcube    = numpy.copy(numpydatacube)
    notnandatacube  = ~numpy.isnan(numpydatacube)
    notnancube      = numpy.copy(notnandatacube)
    exeedingmaximum = numpy.empty_like(numpydatacube, dtype=bool)
    exeedingminimum = numpy.empty_like(numpydatacube, dtype=bool)

    #
    #
    #
    if numpydatacube.shape[0] < 4:
        return smoothedcube  # plain copy from input
    #
    #
    #
    for iteration in range(passes):

        #
        #    'keeping the maximum values' is only applied in case of intermediate iterations, not for the 'last' (or only - in case passes = 1)
        #    this means that the maximum values are not actually retained in the end result
        #    reason is that otherwise we get devils-horns at actual maximum values instead of a smooth transition  
        #                
        if iteration > 0 and dokeepmaxima:
            originalgreater = numpy.full_like(smoothedcube, False, dtype=bool)
            originalgreater[notnandatacube] = smoothedcube[notnandatacube]<numpydatacube[notnandatacube]
            smoothedcube[originalgreater]   = numpydatacube[originalgreater]

        #
        #    we expect this to be obsolete after first pass, since all nan's would be removed
        #    but just to keep things save for future modifications we'll explicitly exclude nan's 
        #
        smoothedcube[~notnancube] = 0.0
        weightscube[~notnancube]  = 0.0

        #
        #    call actual Whittaker algorithm, only first and second order differences are implemented
        #
        if orderofdifferences == 1:
            smoothedcube[:] = _whittaker_first_differences(lmbda, smoothedcube, weightscube)
        elif orderofdifferences == 2:
            smoothedcube[:] = _whittaker_second_differences(lmbda, smoothedcube, weightscube)
        else: raise ValueError("orderofdifferences: only 1 and 2 supported (is %s)" % (orderofdifferences))

        #
        #    update the nan's raster, we expect this to be all True
        #
        notnancube[:] = ~numpy.isnan(smoothedcube)

        #
        #    clip results to valid data range
        #
        if maximumdatavalue is not None: 
            exeedingmaximum.fill(False)
            exeedingmaximum[notnancube]   = smoothedcube[notnancube] > maximumdatavalue
            smoothedcube[exeedingmaximum] = maximumdatavalue

        if minimumdatavalue is not None: 
            exeedingminimum.fill(False)
            exeedingminimum[notnancube]   = smoothedcube[notnancube] < minimumdatavalue
            smoothedcube[exeedingminimum] = minimumdatavalue
    #
    #
    #
    return smoothedcube


#
#
#
def _whittaker_first_differences(lmbda, y, w):
    """
    """
    #
    #
    #
    numberofrasters = y.shape[0]
    #
    #
    #
    d = numpy.full_like(y, numpy.nan, dtype=float)
    c = numpy.full_like(y, numpy.nan, dtype=float)
    z = numpy.full_like(y, numpy.nan, dtype=float)
    #
    #
    #
    d[0] = w[0] + lmbda
    c[0] = - 1.0 * lmbda / d[0]
    z[0] = w[0] * y[0]

    for iIdx in range (1, numberofrasters-1):
        d[iIdx] = w[iIdx] + 2.0 * lmbda - c[iIdx-1] * c[iIdx-1] * d[iIdx-1];
        c[iIdx] = - lmbda / d[iIdx]
        z[iIdx] = w[iIdx] * y[iIdx] - c[iIdx-1] * z[iIdx-1];

    d[numberofrasters-1] =  w[numberofrasters-1] + lmbda - c[numberofrasters-2] * c[numberofrasters-2] * d[numberofrasters-2];
    z[numberofrasters-1] = (w[numberofrasters-1] * y[numberofrasters-1]         - c[numberofrasters-2] * z[numberofrasters-2]) / d[numberofrasters-1]

    for iIdx in range (numberofrasters-1)[::-1] :
        z[iIdx] = z[iIdx] / d[iIdx] - c[iIdx] * z[iIdx+1];
    
    #
    #
    #
    return z

#
#
#
def _whittaker_second_differences(lmbda, y, w):
    """
    """
    #
    #
    #
    numberofrasters = y.shape[0]
    #
    #
    #
    d = numpy.full_like(y, numpy.nan, dtype=float)
    c = numpy.full_like(y, numpy.nan, dtype=float)
    e = numpy.full_like(y, numpy.nan, dtype=float)
    z = numpy.full_like(y, numpy.nan, dtype=float)
    #
    #
    #
    d[0] = w[0] + lmbda
    c[0] = -2.0 * lmbda / d[0]
    e[0] = lmbda / d[0] 
    z[0] = w[0] * y[0]

    d[1] = w[1] + 5 * lmbda - d[0] * c[0] *  c[0];
    c[1] = (-4 * lmbda - d[0] * c[0] * e[0]) / d[1];
    e[1] = lmbda / d[1];
    z[1] = w[1] * y[1] - c[0] * z[0];

    for iIdx in range (2, numberofrasters-2):
        i = iIdx; i1 = iIdx - 1; i2 = iIdx - 2;
        d[i]= w[i] + 6.0 * lmbda - c[i1] * c[i1] * d[i1] - e[i2] * e[i2] * d[i2];
        c[i] = (-4.0 * lmbda -d[i1] * c[i1] * e[i1]) / d[i];
        e[i] = lmbda / d[i];
        z[i] = w[i] * y[i] - c[i1] * z[i1] - e[i2] * z[i2];

    m = numberofrasters-1; i1 = m - 2; i2 = m - 3;
    d[m - 1] = w[m - 1] + 5.0 * lmbda -c[i1] * c[i1] * d[i1] - e[i2] * e[i2] * d[i2];
    c[m - 1] = (-2 * lmbda - d[i1] * c[i1] * e[i1]) / d[m - 1];
    z[m - 1] = w[m - 1] * y[m - 1] - c[i1] * z[i1] - e[i2] * z[i2];

    i1 = m - 1; i2 = m - 2;
    d[m] = w[m] + lmbda - c[i1] * c[i1] * d[i1] - e[i2] * e[i2] * d[i2];
    z[m] = (w[m] * y[m] - c[i1] * z[i1] - e[i2] * z[i2]) / d[m];
    z[m - 1] = z[m - 1] / d[m - 1] - c[m - 1] * z[m];

    for iIdx in range (numberofrasters-2)[::-1] :
        z[iIdx] = z[iIdx] / d[iIdx] - c[iIdx] * z[iIdx + 1] - e[iIdx] * z[iIdx + 2];

    #
    #
    #
    return z

#
#    Composites
#
class CompositeType(object):

    """
    ids or keys to be used in dicts etc.
    """
    MAX = 1 
    MIN = 2
    AVG = 3

    def __init__(self, icompositetypeid):
        """
        """
        self.id = icompositetypeid

#
#
#
CompositeType.MAXCOMPOSITE = CompositeType(CompositeType.MAX)
CompositeType.MINCOMPOSITE = CompositeType(CompositeType.MIN)
CompositeType.AVGCOMPOSITE = CompositeType(CompositeType.AVG)

#
#
#
def compostitemaximum(numpydatacube): return composite(numpydatacube, CompositeType.MAXCOMPOSITE)
def compostiteminimum(numpydatacube): return composite(numpydatacube, CompositeType.MINCOMPOSITE)
def compostiteaverage(numpydatacube): return composite(numpydatacube, CompositeType.AVGCOMPOSITE)

#
#
#
def composite(numpydatacube, compositetype):
    """
    minimum, maximum or average composites from the data cube passed in - can be a numpy array of scalars (including nan's) or a numpy array of rasters
    (preferably use the makedatacube function, and solve it there in case problems/bugs occur)
    """
    #
    #
    #
    if not isinstance(compositetype, CompositeType): raise ValueError(" compositetype must be an actual CompositeType instance")
    #
    #    reference shape from first data raster
    #
    numpydatarastershape = numpy.asarray(numpydatacube[0]).shape
    #
    #
    #
    if compositetype == CompositeType.MAXCOMPOSITE : maxcompositedataraster = numpy.full(numpydatarastershape, numpy.nan, dtype=float)
    if compositetype == CompositeType.MINCOMPOSITE : mincompositedataraster = numpy.full(numpydatarastershape, numpy.nan, dtype=float)
    if compositetype == CompositeType.AVGCOMPOSITE : 
        sumcompositedataraster = numpy.full(numpydatarastershape, numpy.nan, dtype=float)
        cntcompositedataraster = numpy.full(numpydatarastershape, 0,         dtype=int)
    #
    #
    #
    numberofrasters = numpydatacube.shape[0]
    #
    #
    #
    for iIdx in range(0,numberofrasters):
        #
        #
        #
        if compositetype == CompositeType.MAXCOMPOSITE : 
            compositeisnanraster = numpy.isnan(maxcompositedataraster)
            datanotnanraster     = ~numpy.isnan(numpydatacube[iIdx])
            bothnotnanraster     = ~compositeisnanraster & datanotnanraster
            maxcompositedataraster[compositeisnanraster] = numpydatacube[iIdx][compositeisnanraster]
            maxcompositedataraster[bothnotnanraster] = numpy.where( maxcompositedataraster[bothnotnanraster] < numpydatacube[iIdx][bothnotnanraster], numpydatacube[iIdx][bothnotnanraster], maxcompositedataraster[bothnotnanraster])

        if compositetype == CompositeType.MINCOMPOSITE : 
            compositeisnanraster = numpy.isnan(mincompositedataraster)
            datanotnanraster     = ~numpy.isnan(numpydatacube[iIdx])
            bothnotnanraster     = ~compositeisnanraster & datanotnanraster
            mincompositedataraster[compositeisnanraster] = numpydatacube[iIdx][compositeisnanraster]
            mincompositedataraster[bothnotnanraster] = numpy.where( mincompositedataraster[bothnotnanraster] > numpydatacube[iIdx][bothnotnanraster], numpydatacube[iIdx][bothnotnanraster], mincompositedataraster[bothnotnanraster])

        if compositetype == CompositeType.AVGCOMPOSITE :
            compositeisnanraster = numpy.isnan(sumcompositedataraster)
            datanotnanraster     = ~numpy.isnan(numpydatacube[iIdx])
            bothnotnanraster     = ~compositeisnanraster & datanotnanraster
            sumcompositedataraster[compositeisnanraster] = numpydatacube[iIdx][compositeisnanraster]
            cntcompositedataraster[datanotnanraster] += 1
            sumcompositedataraster[bothnotnanraster] += numpydatacube[iIdx][bothnotnanraster]

    if compositetype == CompositeType.MAXCOMPOSITE: return maxcompositedataraster
    if compositetype == CompositeType.MINCOMPOSITE: return mincompositedataraster
    if compositetype == CompositeType.AVGCOMPOSITE:
        sumcompositedataraster[cntcompositedataraster != 0] /= cntcompositedataraster[cntcompositedataraster != 0]
        return sumcompositedataraster

    raise ValueError("unsupported operation")





