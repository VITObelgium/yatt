import logging
import numpy
import scipy.signal



#
#
#
class Mask(object):
    '''
    '''
    
    def __init__(self, verbose):
        """
        """
        self._verbose = verbose
    

    def mask(self, data_numpyarray, scene_numpyparray, maskedvalue=numpy.nan, copy=True):
        '''
        '''
        #
        #    no list of data, nothing to be done
        #
        if data_numpyarray   is None or data_numpyarray.size <= 0   : raise ValueError("Mask - data raster cannot be None nor empty")
        if scene_numpyparray is None or scene_numpyparray.size <= 0 : raise ValueError("Mask - classification raster cannot be None nor empty")
        if not (data_numpyarray.shape == scene_numpyparray.shape)   : raise ValueError("Mask - data and classification rasters mus have same shape")
        #
        #
        #
        masked_numpyarray = data_numpyarray.copy() if copy else data_numpyarray
        masked_numpyarray[self.makemask(scene_numpyparray)] = maskedvalue
        return masked_numpyarray

#
#
#
class SimpleClassificationMask(Mask):
    '''
    create boolean mask by selecting the set of values(classes, to be masked) in a classification

    e.g.
    
    classification    values    result(mask)
       1 1 2 1 1                 F F T F F
       1 3 3 3 1      [2,3]      F T T T F
       1 1 2 1 4                 F F T F F
    '''

    def __init__(self, lstclassvalue, binvert=False, verbose = True):
        '''
        '''
        super().__init__(verbose=verbose)

        if lstclassvalue is None               : raise ValueError("SimpleClassificationMask - lstclassvalue not specified")
        if isinstance(lstclassvalue, int): 
            lstclassvalue = [lstclassvalue]
        for classvalue in lstclassvalue:
            if not isinstance(classvalue, int) : raise ValueError("SimpleClassificationMask - invalid value in class values list (%s)"%(str(classvalue),))
        
        self.lstclassvalue = lstclassvalue
        self.binvert       = bool(binvert)

        if self._verbose: 
            logging.info("SimpleClassificationMask(__init__) - masking %s: %s"%( ('all classes but' if binvert else 'classes'), ' '.join(map(str, lstclassvalue)),))


    def makemask(self, scene_numpyparray):
        '''
        '''

        mask = numpy.full_like(scene_numpyparray, self.binvert, dtype=bool)
        for classvalue in self.lstclassvalue:
            submask = scene_numpyparray == classvalue
            mask[submask] = not self.binvert
            if self._verbose:
                logging.info("SimpleClassificationMask.makemask: pixels total: %s - class(%s): %s (%0.0f%%) %s" % (
                    scene_numpyparray.size,
                    classvalue,
                    numpy.count_nonzero(submask), numpy.count_nonzero(submask)/scene_numpyparray.size*100,
                    ('allowed' if self.binvert else 'masked')))
  
        if self._verbose: 
            logging.info("SimpleClassificationMask.makemask: pixels total: %s - masked: %s (%0.0f%%) - remaining: %s (%0.0f%%)" % (
                scene_numpyparray.size,
                numpy.count_nonzero(mask==True), numpy.count_nonzero(mask==True)/scene_numpyparray.size*100,
                numpy.count_nonzero(mask!=True), numpy.count_nonzero(mask!=True)/scene_numpyparray.size*100))
        return mask

#
#
#
class Convolve2dClassificationMask(Mask):
    '''
    create boolean mask from convolutions around a set of values(classes, to be masked) in a classification

    e.g. mask = Convolve2dClassificationMask(Convolve2dClassificationMask.ConditionSpec(5, [1,2], .5)).makemask(classification)

    classification
    [[0 0 0 0 0]
     [0 0 0 0 0]
     [0 0 1 0 2]
     [0 0 0 0 0]
     [0 0 0 0 0]]

    mask
    [[0 0 0 0 0]
     [0 0 1 0 1]
     [0 1 1 1 1]
     [0 0 1 0 1]
     [0 0 0 0 0]]
    '''

    class ConditionSpec(object):
        '''
        '''

        def __init__(self, iwindowsize, lstclassvalue, fthreshold, verbose = False):
            '''
            '''
            if iwindowsize is None: 
                iwindowsize = 0
            if not isinstance(iwindowsize, int)                  : raise ValueError("Convolve2dClassificationMask.ConditionSpec - invalid iwindowsize (%s)"%(str(iwindowsize),))
            if lstclassvalue is None                             : raise ValueError("Convolve2dClassificationMask.ConditionSpec - lstclassvalue not specified")
            if isinstance(lstclassvalue, int): 
                lstclassvalue = [lstclassvalue]
            for classvalue in lstclassvalue:
                if not isinstance(classvalue, int)               : raise ValueError("Convolve2dClassificationMask.ConditionSpec - invalid value in class values list (%s)"%(str(classvalue),))
            if fthreshold is None                                : raise ValueError("Convolve2dClassificationMask.ConditionSpec - fthreshold not specified")
            if not isinstance(fthreshold, (int, float))          : raise ValueError("Convolve2dClassificationMask.ConditionSpec - invalid fthreshold parameter (%s)"%(str(fthreshold),))

            self.iwindowsize   = iwindowsize
            self.lstclassvalue = lstclassvalue
            self.fthreshold    = fthreshold
            if verbose: logging.info("Convolve2dClassificationMask.ConditionSpec(__init__) - iwindowsize(%3s) classes(%s) fthreshold(%s)"%(self.iwindowsize, ' '.join(map(str,self.lstclassvalue)), self.fthreshold))

    def __init__(self, lstConditionSpec, verbose = True):
        '''
        '''
        super().__init__(verbose=verbose)

        if lstConditionSpec is None:
            raise ValueError("Convolve2dClassificationMask - lstConditionSpec not specified")
        if isinstance(lstConditionSpec, Convolve2dClassificationMask.ConditionSpec): 
            lstConditionSpec = [lstConditionSpec]
        for conditionSpec in lstConditionSpec:
            if not isinstance(conditionSpec, Convolve2dClassificationMask.ConditionSpec): 
                raise ValueError("Convolve2dClassificationMask - invalid object in condition specs list (%s)"%(str(conditionSpec),))

        self.lstConditionSpec = lstConditionSpec
        if self._verbose: 
            logging.info("Convolve2dClassificationMask(__init__) - %s conditions:"%(len(self.lstConditionSpec)))
            for conditionSpec in self.lstConditionSpec:
                logging.info("    - ConditionSpec - iwindowsize(%s) classes(%s) fthreshold(%s)"%(conditionSpec.iwindowsize, ' '.join(map(str,conditionSpec.lstclassvalue)), conditionSpec.fthreshold))

    def makemask(self, scene_numpyparray):
        '''
        '''

        def makekernel(iwindowsize):
            # using a boxcar (flat) kernel would relate to %-of-surface thresholds
            # using a gaussian compromises between this and smoother masks
            kernel_vect = scipy.signal.windows.gaussian(iwindowsize, std = iwindowsize/6.0, sym=True)
            kernel = numpy.outer(kernel_vect, kernel_vect)
            kernel = kernel / kernel.sum()
            if self._verbose: logging.info("Convolve2dClassificationMask.makemask: kernel size %s - weights: max(%0.5f) - min(%0.5f)" % (iwindowsize, kernel.max(), kernel.min()))
            return kernel

        mask = numpy.zeros_like(scene_numpyparray, dtype=bool)

        if self._verbose: logging.info("Convolve2dClassificationMask.makemask:")

        for conditionSpec in self.lstConditionSpec:

            submask = numpy.zeros_like(scene_numpyparray, dtype=bool)
 
            if conditionSpec.fthreshold > 0:
                srcmask = numpy.zeros_like(scene_numpyparray, dtype=bool)
                for classvalue in conditionSpec.lstclassvalue:
                    srcmask[scene_numpyparray == classvalue] = True
            else:
                srcmask = numpy.ones_like(scene_numpyparray, dtype=bool)
                for classvalue in conditionSpec.lstclassvalue:
                    srcmask[scene_numpyparray == classvalue] = False

            convkernel  = makekernel(conditionSpec.iwindowsize)
            convolution = scipy.signal.fftconvolve(srcmask, convkernel, mode='same')

            submask[convolution > abs(conditionSpec.fthreshold)] = True
            mask[submask] = True

            if self._verbose: 
                logging.info("Convolve2dClassificationMask.makemask: pixels total: %s - %sin classes(%s): %s - convoluted(min %0.3f, max %0.3f): %s - masked(above(%0.3f)): %s (%0.0f%%)" % (
                    scene_numpyparray.size,
                    ('' if conditionSpec.fthreshold > 0 else 'NOT '),
                    (' '.join(map(str,conditionSpec.lstclassvalue))),
                    numpy.count_nonzero(srcmask==True),
                    convolution.min(), convolution.max(), numpy.count_nonzero(convolution>0), 
                    abs(conditionSpec.fthreshold), numpy.count_nonzero(submask==True), numpy.count_nonzero(submask==True)/scene_numpyparray.size*100))

        if self._verbose: 
            logging.info("Convolve2dClassificationMask.makemask: pixels total: %s - masked: %s (%0.0f%%) - remaining: %s (%0.0f%%)" % (
                scene_numpyparray.size,
                numpy.count_nonzero(mask==True), numpy.count_nonzero(mask==True)/scene_numpyparray.size*100,
                numpy.count_nonzero(mask!=True), numpy.count_nonzero(mask!=True)/scene_numpyparray.size*100))

        return mask

