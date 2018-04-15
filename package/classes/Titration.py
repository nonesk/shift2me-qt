""" Titration class module

Titration allows manipulating chemical shift data measured with 2D NMR
Input is a set of `.list` tabular files with one residue per line, e.g output of Sparky
It calculates chemical shift variation at each titration step using the first step as reference.
They are transformed into a single 'intensity' value, associated to a residue.
The class provides matplotlib wrapping functions, allowing to display the data from the analysis,
as well as setting a cut-off to filter residues having high intensity values.
"""

import os
import glob
import pickle
import re
import sys
import csv
import json
import yaml
from collections import OrderedDict
from math import *

import pandas as pd

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FormatStrFormatter

from classes.AminoAcid import AminoAcid
from classes.protocole import TitrationProtocole
from classes.plots import Hist, MultiHist, ShiftMap, SplitShiftMap, TitrationCurve
from classes.widgets import CutOffCursor

##----------------------------------------------------------------------------------------------------------
##         Classe titration
##----------------------------------------------------------------------------------------------------------

class Titration(object):
    """
    Class Titration.
    Contains a list of aminoacid objects
    Provides methods for accessing each titration step datas.
    """
    # accepted file path pattern
    PATH_PATTERN = re.compile(r'(.+/)?(.*[^\d]+)(?P<step>[0-9]+)\.list')
    # accepted lines pattern
    LINE_PATTERN = re.compile(r'^(?P<position>\d+)(\S*)?\s+'
                            r'(?P<chemshiftN>\d+\.\d+)\s+'
                            r'(?P<chemshiftH>\d+\.\d+)$')
    # ignored lines pattern
    IGNORE_LINE_PATTERN = re.compile(r"^\d.*")


    def __init__(self, name=None, cutoff=None, **kwargs):
        """
        Load titration files, check their integrity
        `source` is either a directory containing `.list` file, or is a list of `.list` files
        Separate complete vs incomplete data
        """

        self.protocole = TitrationProtocole()

        self.working_directory = None

        self.name = ""

        self.residues = dict() # all residues {position:AminoAcid object}
        self.complete = dict() # complete data residues
        self.incomplete = dict() # incomplete data residues
        self.selected = dict() # selected residues
        self.intensities = list() # 2D array of intensities

        self.dataSteps = 0
        self.cutoff = None

        self.files = []

        ## INIT CUTOFF
        if cutoff: self.set_cutoff(cutoff)

        ## finish
        self.set_name(name)


## ---------------------------------------------
##      Titration + RMN Analysis
## ---------------------------------------------
    def set_name(self, name=None):
        "Sets Titration instance name"
        self.name = str(name) if name is not None else self.name or "Unnamed Titration"
        return self.name

    def set_directory(self, dirPath):
        if (not os.path.isdir(dirPath)):
            raise IOError("{} is not a directory.".format(dirPath))
         
        self.working_directory = dirPath
        

    def set_sequence(self, sequence, offset=0):
        raise NotImplementedError

    def add_step(self, fileName, titrationStream, volume=None):
        "Adds a titration step described in file-like obj `titrationStream`"

        print("[Step {step}]\tLoading NMR data from {titration_file}".format(
            step=self.dataSteps, titration_file=fileName),
            file=sys.stderr)

        # verify file
        step = self.validate_filepath(fileName, verifyStep=True)
        # parse it
        try:
            self.parse_titration_file(titrationStream)
        except ValueError as parseError:
            print("{error} in file {file}.".format(
                error=parseError, file=fileName),
                file=sys.stderr)
            return

        self.dataSteps += 1
        self.files.append(fileName)

        if volume is not None:
            if self.steps < self.dataSteps:
                self.protocole.add_volume(volume)
            else:
                self.protocole.update_volumes({step:volume})


        # create residues with no data for missing positions
        for pos in range(min(self.residues), max(self.residues)):
            if pos not in self.residues:
                self.residues.update({pos: AminoAcid(position=pos)})

        # reset complete residues and update
        self.complete = dict()
        for pos, res in self.residues.items():
            if res.validate(self.dataSteps):
                self.complete.update({pos:res})
            else:
                self.incomplete.update({pos:res})

        print("\t\t{incomplete} incomplete residue out of {total}".format(
             incomplete=len(self.incomplete), total=len(self.residues)),
             file=sys.stderr)

        # Recalculate (position, chem shift intensity) coordinates for histogram plot
        self.intensities = [] # 2D array, by titration step then residu position
        for step in range(self.dataSteps): # intensity is null for reference step, ignoring
            self.intensities.append([self.complete[pos].chemshiftIntensity[step] for pos in sorted(self.complete.keys())])

    def set_cutoff(self, cutoff):
        "Sets cut off for all titration steps"
        raise NotImplementedError

    def validate_filepath(self, filePath, verifyStep=False):
        """
        Given a file path, checks if it has `.list` extension and if it is numbered after the titration step.
        If `step` arg is provided, validation will enforce that parsed file number matches `step`.
        Returns the titration step number if found, IOError is raised otherwise
        """
        matching = self.PATH_PATTERN.match(filePath) # attempt to match
        if matching:
            if verifyStep and int(matching.group("step")) != self.dataSteps:
                raise IOError("File {file} expected to contain data for titration step #{step}."
                                "Are you sure this is the file you want ?"
                                "In this case it must be named like (name){step}.list".format(
                                    file=filePath, step=self.dataSteps))
            # retrieve titration step number parsed from file name
            return int(matching.group("step"))
        else:
            # found incorrect line format
            raise IOError("Refusing to parse file {file}.\nPlease check it is named like (name)(step).list".format(
                file=filePath))

    def parse_titration_file(self, stream):
        """
        Titration file parser.
        Returns a new dict which keys are residues' position and values are AminoAcid objects.
        If residues argument is provided, updates AminoAcid by adding parsed chemical shift values.
        Throws ValueError if incorrect lines are encountered in file.
        """
        for lineNb, line in enumerate(stream) :
            try:
                chemshifts = self.parse_line(line)
                if chemshifts is not None:
                    self.add_chemshifts(chemshifts)
            except ValueError as parseError:
                parseError.args = ("{error} at line {line}".format(
                    error=parseError, line=lineNb), )
                raise
                continue

    def parse_line(self, line):
        "Parses a line from titration file, returning a dictionnaryof parsed data"
        line = line.strip()
        # ignore empty lines and header lines
        if self.IGNORE_LINE_PATTERN.match(line):
            # attempt to match to expected format
            match = self.LINE_PATTERN.match(line)
            if match: # parse as dict
                chemshifts = match.groupdict()
                # Convert parsed str to number types
                for castFunc, key in zip((float, float, int), sorted(chemshifts)):
                    chemshifts[key] = castFunc(chemshifts[key])
                # add or update residue
                return chemshifts
            else:
                # non parsable, non ignorable line
                raise ValueError("Found unparsable line")

    def add_chemshifts(self, chemshifts):
        "Arg chemshifts is a dict with keys position, chemshiftH, chemshiftN"
        position = chemshifts["position"]
        if self.residues.get(position):
            # update AminoAcid object in residues dict
            self.residues[position].add_chemshifts(**chemshifts)
        else:
            # create AminoAcid object in residues dict
            self.residues[position] = AminoAcid(**chemshifts)
        return self.residues[position]




## -------------------------
##    Utils
## -------------------------

    def select_residues(self, *positions):
        "Select a subset of residues"
        for pos in positions:
            try:
                self.selected[pos] = self.residues[pos]
            except KeyError:
                print("Residue at position {pos} does not exist. Skipping selection.".format(
                    pos=pos), file=sys.stderr)
                continue
        return self.selected


    def deselect_residues(self, *positions):
        "Deselect some residues. Calling with no arguments will deselect all."
        try:
            if not positions:
                self.selected = dict()
            else:
                for pos in positions:
                    self.selected.pop(pos)
            return self.selected
        except KeyError:
            pass


## --------------------------
##    Properties
## --------------------------

    @property
    def filtered(self):
        "Returns list of filtered residue having last intensity >= cutoff value"
        if self.cutoff is not None:
            return dict([(res.position, res) for res in self.complete.values() if res.chemshiftIntensity[-1] >= self.cutoff])
        else:
            return dict()

    @property
    def sortedSteps(self):
        """Sorted list of titration steps, beginning at step 1.
        Reference step 0 is ignored.
        """
        return list(range(1,self.dataSteps))


class TitrationCLI(Titration):

    def __init__(self, working_directory, name=None, cutoff=None, initFile=None, **kwargs):

        if not os.path.isdir(working_directory):
            raise IOError("{dir} does not exist")
            exit(1)

        self.dirPath = working_directory

        Titration.__init__(self, name=name, **kwargs)

        # init plots
        self.stackedHist = None
        self.hist = dict()
        ## FILE PATH PROCESSING
        # fetch all .list files in source dir, parse
        # add a step for each file
        try:
            self.update()
        except IOError as error:
            print("{error}".format(error=error), file=sys.stderr)
            exit(1)

        initFile = initFile or self.protocole.extract_init_file(self.dirPath)

        if initFile: self.protocole.load_init_path(initFile)

        if cutoff:
            self.set_cutoff(cutoff)


    def add_step(self, titrationFilePath, volume=None):
        try:
            with open(titrationFilePath, 'r') as titrationStream:
                Titration.add_step(self, titrationFilePath, titrationStream, volume=volume)

            # generate colors for each titration step
            self.colors = plt.cm.get_cmap('hsv', self.dataSteps)

            # close stale stacked hist
            if self.stackedHist and not self.stackedHist.closed:
                self.stackedHist.close()

        except IOError as fileError:
            print("{error}".format(error=fileError), file=sys.stderr)
            return


    def set_cutoff(self, cutoff):
        "Sets cut off for all titration steps"
        try:
            # check cut off validity and store it
            cutoff = float(cutoff)
            self.cutoff = cutoff
            # update cutoff in open hists
            for hist in self.hist.values():
                hist.set_cutoff(cutoff)
            if self.stackedHist:
                self.stackedHist.set_cutoff(cutoff)
            return self.cutoff
        except TypeError as err:
            print("Invalid cut-off value : {error}".format(
                error=err), file=sys.stderr)
            return self.cutoff

## -------------------------
##    Utils
## -------------------------

    def extract_dir(self, directory = None):
        extract_dir = directory or self.dirPath
        if not ( extract_dir and os.path.isdir(extract_dir)): return []

        extract_dir = os.path.abspath(extract_dir)

        # update protocole if init file is present
        initFile = self.protocole.extract_init_file(extract_dir)
        if initFile:
            with open(initFile, 'r') as initStream:
                self.protocole.load_init_file(initStream)

        files = set(glob.glob(os.path.join(extract_dir, '*.list')))
        if len(files) < 1:
            raise ValueError("Directory {dir} does not contain any `.list` titration file.".format(
                dir=extract_dir))
        return files

    def extract_source(self, source=None):
        """
        Handles source data depending on type (file list, directory, saved file).
        """
        source = source or self.dirPath
        # extract list of files
        if type(source) is list:
            if len(source) <= 1:
                if os.path.isdir(source[0]):
                    files = self.extract_dir(source.pop())
            for file in source:
                if not os.path.isfile(file):
                    raise IOError("{path} is not a file.".format(path=file))
                    return
            files = set(map(os.path.abspath, source))
        elif os.path.isdir(source):
            files=self.extract_dir(source)
        else:
            files = set(source)
        return files

    def update(self, source=None):
        files = self.extract_source(source)

        # exclude already known files
        files = files.difference(set(self.files))

        # sort files before adding them
        try:
            files = sorted(files, key=self.validate_filepath)
        except (ValueError, IOError) as error:
            raise
            return

        # load files
        for file in files:
            self.add_step(file)

        return files

    def save(self, path):
        "Save method for titration object"
        try:
            # matplotlib objects can't be saved
            stackedHist = self.stackedHist
            hist = self.hist
            self.stackedHist= None
            self.hist = dict()
            with open(path, 'wb') as saveHandle:
                pickle.dump(self, saveHandle)
            # restore matplotlib objects
            self.stackedHist = stackedHist
            self.hist = hist
        except IOError as fileError:
            print("Could not save titration : {error}\n".format(error=fileError), file=sys.stderr)

    def load(self, path):
        "Loads previously saved titration in place of current instance"
        try:
            with open(path, 'rb') as loadHandle:
                self = pickle.load(loadHandle)
                if type(self) == Titration:
                    return self
                else:
                    raise ValueError("{file} does not contain a Titration object".format(file=path))
        except (ValueError, IOError) as loadError:
            print("Could not load titration : {error}\n".format(error=loadError), file=sys.stderr)

## -------------------------------------------
##      Properties
## -------------------------------------------
    @property
    def concentrationRatio(self):
    	return self.protocole['ratio'].tolist()

    @property
    def summary(self):
        "Returns a short summary of current titration status as string."
        summary = '\n'.join(["--------------------------------------------",
                            "> {name}".format(name=self.name),
                            "--------------------------------------------",
                            "Source dir :\t{dir}".format(dir=self.dirPath),
                            "Steps :\t\t{steps} (reference step 0 to {last})".format(steps=self.dataSteps, last=max(self.dataSteps -1, 0)),
                            "Cut-off :\t{cutoff}".format(cutoff=self.cutoff),
                            "Total residues :\t\t{res}".format(res=len(self.residues)),
                            " - Complete residues :\t\t{complete}".format(complete=len(self.complete)),
                            " - Incomplete residues :\t{incomplete}".format(incomplete=len(self.incomplete)),
                            " - Filtered residues :\t\t{filtered}".format(filtered=len(self.filtered)),
                            "--------------------------------------------\n"  ])
        return summary


## ------------------------
##    Plotting
## ------------------------

    def plot_hist (self, step = None, show=True):
        """
        Define all the options needed (step, cutoof) for the representation.
        Call the getHistogram function to show corresponding histogram plots.
        """
        if not step: # plot stacked histograms of all steps
            # close stacked hist if needed
            if self.stackedHist and not self.stackedHist.closed:
                self.stackedHist.close()
            # replace stacked hist with new hist
            hist = MultiHist(self.complete,self.intensities[1:])
            self.stackedHist = hist
        else: # plot specific titration step
            # allow accession using python-ish negative index
            step = step if step >= 0 else self.dataSteps + step
            # close existing figure if needed
            if self.hist.get(step) and not self.hist[step].closed:
                self.hist[step].close()
            # plot new hist
            hist = Hist(self.complete, self.intensities[step], step=step)
            self.hist[step] = hist
        # add cutoff change event handling
        hist.add_cutoff_listener(self.set_cutoff, mouseUpdateOnly=True)
        if show:
            hist.show()
        hist.set_cutoff(self.cutoff)
        return hist


    def plot_shiftmap(self, residues, split = False):
        """
        Plot measured chemical shifts for each residue as a scatter plot of (chemshiftH, chemshiftN).
        Each color is assigned to a titration step.
        `residue` argument should be an iterable of AminoAcid objects.
        If using `split` option, each residue is plotted in its own subplot.
        """
        residues = list(residues)
        if split and len(residues) > 1:
            shiftmap = SplitShiftMap(residues)
        else: # Trace global chem shifts map
            shiftmap = ShiftMap(residues)
        shiftmap.show()
        return shiftmap


    def plot_titration(self, residue):
        "Plots a titration curve for `residue`, using intensity at each step"
        curve = TitrationCurve(self.concentrationRatio[:self.dataSteps], residue,
                                titrant=self.protocole.titrant['name'],
                                analyte=self.protocole.analyte['name'])
        curve.show()
        return curve


