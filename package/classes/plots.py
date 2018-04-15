import matplotlib.pyplot as plt
import numpy as np
from classes.widgets import CutOffCursor
from math import *
from matplotlib.ticker import FormatStrFormatter


class BaseFig(object):


    def __init__(self, xaxis=None, yaxis=None):
        "Init new figure"
        self.figure = plt.figure()
        self.closed = True
        self.xaxis = list(xaxis) if xaxis else None
        self.yaxis = list(yaxis) if yaxis else None
        self.setup_axes()

    def show(self):
        "Show figure and set open/closed state"
        self.figure.show()
        self.closed = False

    def close(self):
        "Close figure window"
        plt.close(self.figure)

    def init_events(self):
        "Capture window close event"
        self.figure.canvas.mpl_connect('close_event', self.on_close)
        self.figure.canvas.mpl_connect('draw_event', self.on_draw)

    def on_close(self, event):
        "Set closed state to true on window close"
        self.closed = True

## ------------------------
## Placeholders

    def setup_axes(self):
        """
        Should define subplots in figure as well as plotting data.
        Must be replaced in child classes.
        """
        pass

    def on_draw(self, event):
        pass



class BaseHist(BaseFig):
    """
    Base histogram class, providing interface to a matplotlib figure.
    """

    cutoff = None # flag for open/closed state

    def __init__(self, xaxis, yaxis):
        "Init new matplotlib figure, setup widget, events, and layout"

        # Tick every 10
        self.positionTicks=range(min(xaxis) - max(xaxis) % 5, max(xaxis)+10, 10)
        self.filtered = dict()
        self.bars = list()
        super().__init__(xaxis, yaxis)

        self.xlabel = self.figure.axes[-1].set_xlabel('Residue')
        self.ylabel = self.figure.text(0.04, 0.5, 'Chem Shift Intensity',
                            va='center', rotation='vertical')

        # Init cursor widget and connect it
        self.init_cursor()
        self.init_events()
        self.cutoffText = self.figure.text(0.13, 0.9, self.cutoff_str)

        # initial draw
        self.figure.canvas.draw()

    @property
    def cutoff_str(self):
        if self.cutoff is not None:
            return "Cut-off : {cutoff:.4f}".format(cutoff=self.cutoff)
        else:
            return "Cut-off : {cutoff}".format(cutoff=self.cutoff)

    def on_draw(self, event):
        "Prevent cut off hiding, e.g on window resize"
        self.cursor.visible = True
        self.cursor.update_lines(None, self.cutoff)

    def init_cursor(self):
        """
        Init cursor widget and connect it to self.on_cutoff_update
        """
        self.cursor = CutOffCursor(self.figure.canvas, self.figure.axes,
                                    color='r', linestyle='--', lw=0.8,
                                    horizOn=True, vertOn=False )
        self.cursor.on_changed(self.on_cutoff_update)
        if self.cutoff:
            self.set_cutoff(self.cutoff)

    def add_cutoff_listener(self, func, mouseUpdateOnly=False):
        "Add extra on_change cutoff event handlers"
        if mouseUpdateOnly:
            self.cursor.on_mouse_update(func)
        else:
            self.cursor.on_changed(func)

    def on_cutoff_update(self, cutoff):
        """
        Listener method to be connected to cursor widget
        """
        BaseHist.cutoff = cutoff
        self.cutoffText.set_text(self.cutoff_str)
        self.draw()

    def set_cutoff(self, cutoff):
        """
        Cut off setter.
        Triggers change of cut off cursor value, allowing to update figure content.
        kwargs are passed to cursor widget set_cutoff method.
        """
        BaseHist.cutoff = cutoff
        if not self.closed:
            self.cursor.set_cutoff(cutoff)

    def draw(self):
        """
        Updates bars color according to current cut off value.
        """
        for ax, axBar in zip(self.figure.axes, self.bars):
            for bar in axBar:
                if self.cutoff:
                    if bar.get_height() >= self.cutoff: # show high intensity residues
                        if not self.filtered.get(bar):
                            bar.set_facecolor('orange')
                            self.filtered[bar] = 1
                    else:
                        if self.filtered.get(bar):
                            bar.set_facecolor(None)
                            self.filtered[bar] = 0
        self.figure.canvas.draw()


class Hist(BaseHist):
    """
    BaseHist child class for plotting single histogram
    """

    def __init__(self, xaxis, yaxis, step=None):
        """
        Sets title
        """
        super().__init__(xaxis, yaxis)
        if step:
            self.figure.suptitle('Titration step {step}'.format(step=step) )# set title

    def setup_axes(self):
        """
        Create a single subplot and set its layout and data.
        """
        self.figure.subplots(nrows=1, ncols=1, squeeze=True)
        ax = self.figure.axes[0]
        ax.set_xticks(self.positionTicks)
        maxVal = np.amax(self.yaxis)
        ax.set_ylim(0, np.round(maxVal + maxVal*0.1, decimals=1))
        #self.background.append(self.figure.canvas.copy_from_bbox(ax.bbox))
        self.bars.append(ax.bar(self.xaxis, self.yaxis, align='center', alpha=1))



class MultiHist(BaseHist):
    """
    BaseHist child class for plotting stacked hists.
    """

    def __init__(self, xaxis, yMatrix):
        """
        Sets title
        """
        super().__init__(xaxis, yMatrix)
        self.figure.suptitle('Titration : steps 1 to {last}'.format(last=len(yMatrix) ) )
        self.figure.text(0.96, 0.5, 'Titration step',
                        va='center', rotation='vertical')
    def setup_axes(self):
        """
        Creates a subplot for each line in yaxis matrix
        """
        self.figure.subplots(nrows=len(self.yaxis), ncols=1,
                            sharex=True, sharey=True, squeeze=True)
        # Set content and layout for each subplot.
        for index, ax in enumerate(self.figure.axes):
            ax.set_xticks(self.positionTicks)
            maxVal = np.amax(self.yaxis)
            ax.set_ylim(0, np.round(maxVal + maxVal*0.1, decimals=1))
            stepLabel = "{step}.".format(step=str(index+1))
            ax.set_ylabel(stepLabel, rotation="horizontal", labelpad=15)
            ax.yaxis.set_label_position('right')
            #ax.yaxis.label.set_color('red')
            #self.background.append(self.figure.canvas.copy_from_bbox(ax.bbox))
            self.bars.append(ax.bar(self.xaxis, self.yaxis[index], align='center', alpha=1))
        #self.figure.subplots_adjust(left=0.15)


class ShiftMap(BaseFig):

    def __init__(self, residues):

        if not residues:
            raise ValueError("No residues to plot as shiftmap.")
            return
        self.residues = list(residues)
        self.colormap = plt.cm.get_cmap('hsv', len(self.residues[0].chemshiftH))
        super().__init__()
        self.figure.suptitle('Chemical shifts 2D map')
        self.figure.text(0.5, 0.04, 'H Chemical Shift', ha='center')
        self.figure.text(0.04, 0.5, 'N Chemical Shift', va='center', rotation='vertical')

    def setup_axes(self):
        for res in self.residues :
            xaxis = res.chemshiftH
            yaxis = res.chemshiftN
            im=plt.scatter(xaxis, yaxis,
                        facecolors='none', cmap=self.colormap,
                        c = range(len(xaxis)), alpha=0.2)

        self.figure.subplots_adjust(left=0.15, top=0.90,
                            right=0.85, bottom=0.15) # make room for legend
        # Add colorbar legend for titration steps
        cbar_ax = self.figure.add_axes([0.90, 0.15, 0.02, 0.75])
        self.figure.colorbar(mappable=im, cax=cbar_ax).set_label("Titration steps")


class SplitShiftMap(ShiftMap):

    MAXSUBPLOTS = 36

    def __init__(self, residues):
        self.resCount = len(residues)
        if self.resCount > self.MAXSUBPLOTS:
            raise ValueError("Refusing to plot too many ({count}) residues in split mode. Sorry.".format(
                                count=self.resCount))
        elif self.resCount == 1:
            raise ValueError("Refusing to plot in split mode for only one residue. Please use ShiftMap class instead.")
        super().__init__(residues)

    def setup_axes(self):
        self.axes = self.figure.subplots(nrows=ceil(sqrt(self.resCount)),
                                    ncols=round(sqrt(self.resCount)),
                                    sharex=False, sharey=False, squeeze=True)
        # iterate over each created cell
        for index, ax in enumerate(self.axes.flat):
            if index < self.resCount:
                res = self.residues[index]
                xaxis = res.chemshiftH
                yaxis = res.chemshiftN
                # Trace chem shifts for current residu in new graph cell
                im = ax.scatter(xaxis, yaxis,
                                facecolors='none', cmap=self.colormap,
                                c = range(len(xaxis)), alpha=0.2)
                # ax.set_title("Residue %s " % res.position, fontsize=10)
                # print xticks as 2 post-comma digits float
                ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
                ax.tick_params(labelsize=8)
            else:
                ax.remove() # remove extra subplots

        # scale
        self.scale()
        # annotate
        for index, ax in enumerate(self.axes.flat):
            if index < self.resCount:
                self.annotate_chemshift(self.residues[index], ax)

        # display them nicely
        self.figure.tight_layout()
        # Add colorbar legend for titration steps using last plot cell data
        self.figure.subplots_adjust(left=0.12, top=0.9,
                            right=0.85,bottom=0.15) # make room for legend
        cbar_ax = self.figure.add_axes([0.90, 0.15, 0.02, 0.75])
        self.figure.colorbar(mappable=im, cax=cbar_ax).set_label("Titration steps")

    def scale(self):
        "Scales subplots when plotting splitted shift map"
        xMaxRange, yMaxRange = np.array(self.get_max_range_NH()) * 1.5
        for ax in self.axes.flat:
            currentXRange = ax.get_xlim()
            currentYRange = ax.get_ylim()
            xMiddle = sum(currentXRange) / 2
            yMiddle = sum(currentYRange) / 2
            ax.set_xlim(xMiddle - xMaxRange/2, xMiddle + xMaxRange/2)
            ax.set_ylim(yMiddle - yMaxRange/2, yMiddle + yMaxRange/2)

    def get_max_range_NH(self):
        "Returns max range tuple for N and H among residues in residueSet"
        return (max([res.rangeH for res in self.residues]),
                max([res.rangeN for res in self.residues]))

    def annotate_chemshift(self, residue, ax):
        "Adds chem shift vector and residue position for current residue in current subplot"
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        xrange, yrange = (xlim[1] - xlim[0], ylim[1] - ylim[0])

        shiftVector = np.array(residue.arrow[2:])
        orthoVector = np.array([1.0,1.0])
        # make orthogonal
        orthoVector -= orthoVector.dot(shiftVector) * shiftVector / np.linalg.norm(shiftVector)**2
        # scale ratio
        orthoVector *= np.array([xrange/yrange, 1.0])
        # normalize
        orthoVector /= (np.linalg.norm(orthoVector) * 10)

        """
        # plot using mpl arrow
        ax.arrow(*np.array(residue.arrow[:2]) + x, *residue.arrow[2:],
                head_width=0.07, head_length=0.1, fc='red', ec='red', lw=0.5,
                length_includes_head=True, linestyle='-', alpha=0.7, overhang=0.7)
        """
        arrowStart = np.array(residue.arrow[:2]) + orthoVector
        ax.annotate("", xy=arrowStart + shiftVector, xytext=arrowStart,
                    arrowprops=dict(arrowstyle="->", fc="red", ec='red', lw=0.5))
        """
        # show orthogonal vector
        ax.arrow(*residue.arrow[:2], *x, head_width=0.02, head_length=0.02, fc='black', ec='green',
                length_includes_head=True, linestyle=':', alpha=0.6, overhang=0.5)
        """
        horAlign = "left" if orthoVector[0] <=0 else "right"
        vertAlign = "top" if orthoVector[1] >=0 else "bottom"
        ax.annotate(str(residue.position), xy=residue.chemshift[0],
                    xytext=residue.chemshift[0]-0.8*orthoVector,
                    xycoords='data', textcoords='data',
                    fontsize=7, ha=horAlign, va=vertAlign)

class TitrationCurve(BaseFig):

    def __init__(self, titrationSteps, residue, titrant='titrant', analyte='analyte'):
        self.residue = residue
        self.titrant = titrant
        self.analyte = analyte
        xaxis = titrationSteps
        yaxis = list(residue.chemshiftIntensity)
        super().__init__(xaxis, yaxis)
        # set title
        self.figure.suptitle('Titration curve of residue {pos}'.format(
                            pos=residue.position, fontsize=13))


    def setup_axes(self):
        im = plt.scatter(self.xaxis, self.yaxis, alpha=1)
        plt.xlabel("[{titrant}]/[{analyte}]".format(
            titrant=self.titrant, analyte=self.analyte))

        self.figure.text(0.04, 0.5, 'Chem Shift Intensity',
                va='center', rotation='vertical', fontsize=11)
        """
        z = np.polyfit(xAxis, yAxis, 4)
        f = np.poly1d(z)

        xnew = np.linspace(0,max(xAxis),100)
        ynew = f(xnew)
        plt.plot(xnew, ynew)
        """
        """
        fig.subplots_adjust(left=0.12, top=0.90,
                            right=0.85,bottom=0.14) # make room for legend
        # Add colorbar legend for titration steps
        cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.75])
        fig.colorbar(mappable=im, cax=cbar_ax).set_label("Titration steps")
        """
