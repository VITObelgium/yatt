import logging
import numpy
import random
import scipy.signal
import matplotlib.pyplot
import yatt.mask

#
#
#
def showkernels(bmakepng):
    #
    #    <-buffersize-X-buffersize->
    #
    #    <-------windowsize-------->
    #
    #    .-------------------------.
    #    | kernel                  |
    #    |                         |
    #            centerrow
    #    |                         |
    #    |                         |
    #    .-------------------------.
    #
    convs = [
        {'buffersize' :   3, 'fthresholds' : 0.08000 },
        {'buffersize' :   3, 'fthresholds' : 0.08131 },
        {'buffersize' :   3, 'fthresholds' : 0.08200 },
        {'buffersize' :   3, 'fthresholds' : 0.10000 },

#        {'buffersize' :   4, 'fthresholds' : 0.05600 },
#        {'buffersize' :   4, 'fthresholds' : 0.05690 },
#        {'buffersize' :   4, 'fthresholds' : 0.05780 },

#         {'buffersize' :  30, 'fthresholds' : 0.0500 },
#         {'buffersize' :  30, 'fthresholds' : 0.0250 },
#         {'buffersize' :  30, 'fthresholds' : 0.0100 },
# 
#         {'buffersize' :  50, 'fthresholds' : 0.0500 },
#         {'buffersize' :  50, 'fthresholds' : 0.0250 },
#         {'buffersize' :  50, 'fthresholds' : 0.0100 },
        ]
    #
    #
    #
    for conv in convs: 
        buffersize = conv['buffersize']
        fthreshold = conv['fthresholds']
        iwindowsizeinpixels = 2*buffersize + 1
        #
        #    kernel
        #
        convkernel = yatt.mask.Convolve2dClassificationMask._makekernel(iwindowsizeinpixels, True)
        #
        #    sample scenes
        #
        onepixel = numpy.zeros_like(convkernel, dtype=int)
        onepixel[buffersize, buffersize] = 1
        twopixel = numpy.zeros_like(convkernel, dtype=int)
        twopixel[buffersize, int(buffersize/2)] = 1
        twopixel[buffersize, int(buffersize + 1 + buffersize/2)] = 1
        allpixel = numpy.ones_like(convkernel, dtype=int)

        rndpixel = numpy.zeros_like(convkernel, dtype=int)
        estmean = min( int(fthreshold/convkernel.mean() + 0.5), convkernel.size)
        count = 0
        while True:
            rndrow = random.randint(0, iwindowsizeinpixels-1)
            rndcol = random.randint(0, iwindowsizeinpixels-1)
            if 0 == rndpixel[rndrow, rndcol]:
                rndpixel[rndrow, rndcol] = 1
                count += 1
                if count >= estmean:
                    break
        #
        #    convolutions (this is the core code of the Convolve2dClassificationMask)
        #
        onepixel_convolution = scipy.signal.fftconvolve(onepixel.astype(numpy.int), convkernel, mode='same')
        twopixel_convolution = scipy.signal.fftconvolve(twopixel.astype(numpy.int), convkernel, mode='same')
        allpixel_convolution = scipy.signal.fftconvolve(allpixel.astype(numpy.int), convkernel, mode='same')
        rndpixel_convolution = scipy.signal.fftconvolve(rndpixel.astype(numpy.int), convkernel, mode='same')
        #
        #    masks - using the actual Convolve2dClassificationMask as intended
        #
        onepixel_convolutionmask = yatt.mask.Convolve2dClassificationMask([yatt.mask.Convolve2dClassificationMask.ConditionSpec(iwindowsizeinpixels, 1, fthreshold)]).makemask(onepixel)
        twopixel_convolutionmask = yatt.mask.Convolve2dClassificationMask([yatt.mask.Convolve2dClassificationMask.ConditionSpec(iwindowsizeinpixels, 1, fthreshold)]).makemask(twopixel)
        allpixel_convolutionmask = yatt.mask.Convolve2dClassificationMask([yatt.mask.Convolve2dClassificationMask.ConditionSpec(iwindowsizeinpixels, 1, fthreshold)]).makemask(allpixel)
        rndpixel_convolutionmask = yatt.mask.Convolve2dClassificationMask([yatt.mask.Convolve2dClassificationMask.ConditionSpec(iwindowsizeinpixels, 1, fthreshold)]).makemask(rndpixel)

        #
        #    special act. add pixels till cluster occurs
        #
        minpixel = numpy.zeros_like(convkernel, dtype=int)
        count = 0

        estmin   = min( int(fthreshold/convkernel.max() + 0.5), convkernel.size)
        while True:
            rndrow = random.randint(0, iwindowsizeinpixels-1)
            rndcol = random.randint(0, iwindowsizeinpixels-1)
            if 0 == minpixel[rndrow, rndcol]:
                minpixel[rndrow, rndcol] = 1
                count += 1
                if count >= estmin:
                    break

        while True:
            minpixel_convolutionmask = yatt.mask.Convolve2dClassificationMask([yatt.mask.Convolve2dClassificationMask.ConditionSpec(iwindowsizeinpixels, 1, fthreshold)]).makemask(minpixel)
            if count >= convkernel.size:
                break
            if (minpixel_convolutionmask == 1).sum() > 1:
                break
            rndrow = random.randint(0, iwindowsizeinpixels-1)
            rndcol = random.randint(0, iwindowsizeinpixels-1)
            if 0 == minpixel[rndrow, rndcol]:
                minpixel[rndrow, rndcol] = 1
                count += 1

        minpixel_convolution = scipy.signal.fftconvolve(minpixel.astype(numpy.int), convkernel, mode='same')

        #
        #    and now a long and sad story about pictures which never quite look like you'd expect
        #
        figure = matplotlib.pyplot.figure(figsize=(12,7))
        gridspec_rows = 4
        gridspec_cols = 6
        gridspec = matplotlib.gridspec.GridSpec(gridspec_rows, gridspec_cols)
        gridspec.update(top = .90, left = 0.10, bottom = 0.05, right = .99, wspace=0.10, hspace=0.50, )

        #
        #    kernel itself
        #
        axis = matplotlib.pyplot.subplot(gridspec[0, 0])
        axis.set_title("kernel(%s)"%(iwindowsizeinpixels))
        axis.imshow(convkernel, cmap='gray')
        refaxis = axis
    
        #
        #    scenes
        #
        axis = matplotlib.pyplot.subplot(gridspec[0, 1], sharex=refaxis, sharey=refaxis)
        axis.set_title("scenes (1 pix)")
        axis.imshow(onepixel, cmap='gray', vmin=0, vmax=1)

        axis = matplotlib.pyplot.subplot(gridspec[0, 2], sharex=refaxis, sharey=refaxis)
        axis.set_title("(2 pix)")
        axis.imshow(twopixel, cmap='gray', vmin=0, vmax=1)

        axis = matplotlib.pyplot.subplot(gridspec[0, 3], sharex=refaxis, sharey=refaxis)
        axis.set_title("(all-%spix)"%((allpixel==1).sum()))
        axis.imshow(allpixel, cmap='gray', vmin=0, vmax=1)

        axis = matplotlib.pyplot.subplot(gridspec[0, 4], sharex=refaxis, sharey=refaxis)
        axis.set_title("(rnd-%spix)"%((minpixel==1).sum()))
        axis.imshow(minpixel, cmap='gray', vmin=0, vmax=1)

        axis = matplotlib.pyplot.subplot(gridspec[0, 5], sharex=refaxis, sharey=refaxis)
        axis.set_title("(rnd-%spix)"%((rndpixel==1).sum()))
        axis.imshow(rndpixel, cmap='gray', vmin=0, vmax=1)

        #
        #    convolution of scenes
        #       
        axis = matplotlib.pyplot.subplot(gridspec[1, 1], sharex=refaxis, sharey=refaxis)
        axis.set_title("convolution")
        axis.imshow(onepixel_convolution, cmap='gray')

        axis = matplotlib.pyplot.subplot(gridspec[1, 2], sharex=refaxis, sharey=refaxis)
        axis.imshow(twopixel_convolution, cmap='gray')

        axis = matplotlib.pyplot.subplot(gridspec[1, 3], sharex=refaxis, sharey=refaxis)
        axis.imshow(allpixel_convolution, cmap='gray')

        axis = matplotlib.pyplot.subplot(gridspec[1, 4], sharex=refaxis, sharey=refaxis)
        axis.imshow(minpixel_convolution, cmap='gray')

        axis = matplotlib.pyplot.subplot(gridspec[1, 5], sharex=refaxis, sharey=refaxis)
        axis.imshow(rndpixel_convolution, cmap='gray')

        #
        #    masks (convolution of scene > threshold)
        #       
        axis = matplotlib.pyplot.subplot(gridspec[3, 1], sharex=refaxis, sharey=refaxis)
        axis.set_title("mask")
        axis.imshow(onepixel_convolutionmask, cmap='gray', vmin=0, vmax=1)

        axis = matplotlib.pyplot.subplot(gridspec[3, 2], sharex=refaxis, sharey=refaxis)
        axis.imshow(twopixel_convolutionmask, cmap='gray', vmin=0, vmax=1)

        axis = matplotlib.pyplot.subplot(gridspec[3, 3], sharex=refaxis, sharey=refaxis)
        axis.imshow(allpixel_convolutionmask, cmap='gray', vmin=0, vmax=1)

        axis = matplotlib.pyplot.subplot(gridspec[3, 4], sharex=refaxis, sharey=refaxis)
        axis.imshow(minpixel_convolutionmask, cmap='gray', vmin=0, vmax=1)

        axis = matplotlib.pyplot.subplot(gridspec[3, 5], sharex=refaxis, sharey=refaxis)
        axis.imshow(rndpixel_convolutionmask, cmap='gray', vmin=0, vmax=1)

        #
        #    horizontal center line of convolution
        #       
        axis = matplotlib.pyplot.subplot(gridspec[2, 0])
        axis.set_title("center row")
        axis.plot(convkernel[buffersize], 'ro-')
        axis.plot(numpy.full_like(convkernel[buffersize], fthreshold), 'b-')
        axis.set_aspect(numpy.diff(axis.get_xlim())[0] / numpy.diff(axis.get_ylim())[0])

        axis = matplotlib.pyplot.subplot(gridspec[2, 1])
        axis.plot(onepixel_convolution[buffersize], 'ro-')
        axis.plot(numpy.full_like(onepixel_convolution[buffersize], fthreshold), 'b-')
        axis.set_aspect(numpy.diff(axis.get_xlim())[0] / numpy.diff(axis.get_ylim())[0])

        axis = matplotlib.pyplot.subplot(gridspec[2, 2])
        axis.plot(twopixel_convolution[buffersize], 'ro-')
        axis.plot(numpy.full_like(twopixel_convolution[buffersize], fthreshold), 'b-')
        axis.set_aspect(numpy.diff(axis.get_xlim())[0] / numpy.diff(axis.get_ylim())[0])

        axis = matplotlib.pyplot.subplot(gridspec[2, 3])
        axis.plot(allpixel_convolution[buffersize], 'ro-')
        axis.plot(numpy.full_like(allpixel_convolution[buffersize], fthreshold), 'b-')
        axis.set_aspect(numpy.diff(axis.get_xlim())[0] / numpy.diff(axis.get_ylim())[0])
        axis.set_aspect(numpy.diff(axis.get_xlim())[0] / numpy.diff(axis.get_ylim())[0])

        axis = matplotlib.pyplot.subplot(gridspec[2, 4])
        axis.plot(minpixel_convolution[buffersize], 'ro-')
        axis.plot(numpy.full_like(minpixel_convolution[buffersize], fthreshold), 'b-')
        axis.set_aspect(numpy.diff(axis.get_xlim())[0] / numpy.diff(axis.get_ylim())[0])

        axis = matplotlib.pyplot.subplot(gridspec[2, 5])
        axis.plot(rndpixel_convolution[buffersize], 'ro-')
        axis.plot(numpy.full_like(rndpixel_convolution[buffersize], fthreshold), 'b-')
        axis.set_aspect(numpy.diff(axis.get_xlim())[0] / numpy.diff(axis.get_ylim())[0])


        matplotlib.pyplot.suptitle("convolution masks: iwindowsizeinpixels %s - fthreshold %s"%(iwindowsizeinpixels, fthreshold))
        matplotlib.pyplot.show()
        #
        #    close('all') should be enough, but somehow sometimes it still seams to leak
        #
        figure.clear()
        matplotlib.pyplot.close(figure)
        matplotlib.pyplot.close('all')

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
    showkernels(bmakepng)
