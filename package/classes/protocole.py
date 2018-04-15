import glob
import sys
import os
from collections import OrderedDict

import pandas as pd
import yaml
import json

represent_dict_order = lambda self, data: self.represent_mapping('tag:yaml.org,2002:map', data.items())
""" setup YAML for ordered dict output : https://stackoverflow.com/a/8661021 """
yaml.add_representer(OrderedDict, represent_dict_order)

# Setup pandas float precision
pd.set_option('precision', 3)


## --------------------------------------------------------------------
##      Shift2Me classes
## --------------------------------------------------------------------

class TitrationProtocole(object):
    "A titration protocole tracker, wrapping around a pandas dataframe"

    INIT_FIELDS=('name', 'analyte', 'titrant', 'start_volume', 'add_volumes')
    COLUMN_ALIASES = ('step', 'vol_add', 'vol_titrant', 'vol_total', 'conc_titrant', 'conc_analyte', 'ratio')

    def __init__(self, initStream=None, **kwargs):

        # Experiment name
        self.name = None

        self.isInit = False # False while parameters are incorrect

        # Initial titrant concentration
        self.titrant = {
            "name" : 'titrant',
            "concentration" : 0
        }

        # Initial analyte concentration
        self.analyte = {
            "name" : 'analyte',
            'concentration' : 0
        }

        # Initial total volume
        self.startVol = 0
        # Initial analyte volume in total volume
        self.analyteStartVol = 0

        # Added titrant volumes : 0 for first step
        self.volumes = [0]

        # Initialize protocole dataframe
        self._df = pd.DataFrame(index=list(range(len(self.volumes))) or [0], columns=self.COLUMN_ALIASES, data=0)
        self.col_aliases = dict(zip(self.COLUMN_ALIASES, self._df.columns))

        # Load YAML file or arg dictionnary
        if initStream is not None: # init from file
            self.load_init_file(initStream)
        elif kwargs: # init from dict
            self.load_init_dict(kwargs)



## ----------------------------------------------------------
##      Protocole using pandas
## ----------------------------------------------------------

    def __getitem__(self, item):
        "Get item from data frame using column alias"
        if item in self.col_aliases:
            return self._df[self.col_aliases[item]]
        else:
            return self._df[item]

    def __setitem__(self, item, value):
        "Set item from data frame using column alias"
        if item in self.col_aliases:
            self._df[self.col_aliases[item]] = value
        else:
            self._df[item] = value

    @property
    def df(self):
        "Property for getting inner dataframe"
        return self._df

    def update(self, index=True):
        "Rebuild dataframe from current volumes list"
        self._df = pd.DataFrame(
            index=list(range(len(self.volumes))) or [0],
            columns=self.COLUMN_ALIASES,
            data=0)
        self.fill_df()
        self.set_headers()
        if index:
            self._df.set_index('Step', inplace=True)
        return self._df

    def fill_df(self):
        "Fill dataframe columns"
        self._df['step'] = list(range(len(self.volumes)))
        self._df['vol_add'] = self.volumes
        self._df['vol_titrant'] = self._df['vol_add'].cumsum()
        self._df['vol_total'] = self.startVol + self._df['vol_titrant']
        self._df['conc_titrant'] = self._df['vol_titrant'] * self.titrant['concentration'] / self._df['vol_total']
        self._df['conc_analyte'] = self.analyteStartVol * self.analyte['concentration'] / self._df['vol_total']
        self._df['ratio'] = self._df['conc_titrant'] / self._df['conc_analyte']

    def set_headers(self):
        """Set more expressive column headers for display
        and register headers aliases for easy access to data
        """
        # Create headers list
        headers = list(map(
            lambda s: s.format(
                titrant=self.titrant['name'],
                analyte=self.analyte['name']),
            [
                'Step',
                'Added {titrant} (µL)',
                'Total {titrant} (µL)',
                'Total volume (µL)',
                '[{titrant}] (µM)',
                '[{analyte}] (µM)',
                '[{titrant}]/[{analyte}]'
            ]))
        # update aliases
        self.col_aliases = dict(zip(self.COLUMN_ALIASES, headers))
        # update headers
        self._df.columns = list(headers)

## -----------------------------------------------------
##         Input/output
## -----------------------------------------------------

    @staticmethod
    def extract_init_file(dirPath):
        "Find .yml files in dirPath"
        # find files by extension
        initFileList = glob.glob(os.path.join(dirPath, '*.yml')) or glob.glob(os.path.join(dirPath, '*.json'))
        # more than one file, take most recent
        if len(initFileList) > 1:
            initFile = min(initFileList, key=os.path.getctime)
            print("{number} init files found in {source}. Using most recent one : {file}".format(
                                number=len(initFileList), source=dirPath, file=initFile ),
                                file=sys.stderr)
        elif initFileList: # single file
            initFile = initFileList.pop()
        else: # no file
            initFile = None
        return initFile

    def validate(self):
        valid = True

        if not self.titrant['name']:
            self.titrant['name'] = 'titrant'
        if not self.analyte['name']:
            self.analyte['name'] = 'analyte'

        if self.titrant['concentration'] <= 0:
            self.titrant['concentration'] = 0
            valid = False

        if self.analyte['concentration'] <= 0:
            self.analyte['concentration'] = 0
            valid = False

        if self.startVol <= 0:
            self.startVol = 0
            valid=False
        if self.analyteStartVol <= 0:
            self.analyteStartVol = 0
            valid=False
        if self.analyteStartVol >= self.startVol:
            valid=False

        if self.volumes[0] != 0:
            valid=False

        return valid


    @staticmethod
    def validate_init_dict(initDict):
        try:
            for role in ['titrant', 'analyte']:
                concentration = float(initDict[role]['concentration'])
                if concentration <=0:
                    raise ValueError("Invalid concentration ({conc}) for {role}".format(
                        conc=concentration, role=role))

            for volumeKey in ('analyte', 'total'):
                volume = float(initDict['start_volume'][volumeKey])
                if volume <= 0:
                    raise ValueError("Invalid volume ({vol}) for {volKey}".format(
                        vol=volume, volKey=volumeKey))

            if initDict['start_volume']['analyte'] > initDict['start_volume']['total']:
                raise ValueError("Initial analyte volume ({analyte}) cannot be greater than total volume {total}".format(**initDict['start_volume']))
            return initDict
        except TypeError as typeError:
            typeError.args = ("Could not convert value to number : {error}".format(error=typeError), )
            raise
        except KeyError as keyError:
            keyError.args = ("Missing required data for protocole initialization. Hint: {error}".format(error=keyError), )
            raise

    def load_init_path(self, initPath):
        loaders = {
            '.yml' : yaml,
            '.json' : json
        }
        root, ext = os.path.splitext(initPath)
        loader = loaders.get(ext)
        if loader is None:
            raise IOError("Invalid init file extension for {init} : accepted are .yml or .json".format(init=initPath))

        print("[Protocole]\tLoading protocole parameters from {initPath}".format(
            initPath=initPath),
            file=sys.stderr)

        try:
            with open(initPath, 'r') as initStream:
                self.load_init_file(initStream, loader)
        except IOError as error:
            raise
            return



    def load_init_file(self, initStream, loader=yaml):
        try:
            initDict = loader.load(initStream)
            if initDict:
                self.load_init_dict(initDict)
            return self.isInit
        except IOError as fileError:
            raise
        except (ValueError,yaml.YAMLError) as valError:
            valError.args = ("Error : {error}".format(error=valError), )
            raise

    def load_init_dict(self, initDict, validate=True):
        if validate:
            initDict = self.validate_init_dict(initDict)
        if initDict is None:
            return

        #set name
        self.set_name(initDict.get('name'))

        # titrant, analyte initial names and concentration
        self.titrant = initDict['titrant']
        self.analyte = initDict['analyte']
        for initConcentration in (self.titrant, self.analyte):
            initConcentration['concentration'] = float(initConcentration['concentration'])

        # initial volumes
        self.analyteStartVol = float(initDict['start_volume']['analyte'])
        self.startVol = float(initDict['start_volume']['total'])
        # added titrant volumes
        self.set_volumes(initDict.get('add_volumes', self.volumes))

        # validate parameters
        self.isInit = self.validate()
        return self.isInit

    def dump_init_file(self, initFile=None):
        try:
            fh = open(initFile, 'w') if initFile else sys.stdout
            yaml.dump(self.as_init_dict, fh, default_flow_style=False, indent=4)
            if fh is not sys.stdout:
                fh.close()
            return initFile
        except IOError as fileError:
            print("{error}".format(error=fileError), file=sys.stderr)
            return



## -------------------------------------------------
##         Manipulation methods
## -------------------------------------------------
    def set_name(self, name=None):
        "Sets Titration instance name"
        self.name = str(name) if name is not None else self.name or "Unnamed Titration"
        return self.name



    def set_volumes(self, volumes):
        "Set tiration volumes, updating steps to match number of volumes"
        if volumes[0] != 0:
            volumes.insert(0,0)
        self.volumes = list(map(float, volumes))
        self.update()

    def update_volumes(self, stepVolumes):
        "Updates protocole volumes from a dict \{step_nb: volume\}"
        try:
            for step, vol in stepVolumes.items():
                self.volumes[step] = vol
        except IndexError:
            print("{step} does not exist".format(step=step), file=sys.stderr)

    def add_volume(self, volume):
        "Add a volume for next protocole step"
        self.volumes.append(volume)
        self.update()

    def add_volumes(self, volumes):
        "Add a list of volumes for next protocole steps"
        self.volumes += volumes
        self.update()

## -----------------------------------------------------
##         Properties
## -----------------------------------------------------

    @property
    def as_init_dict(self):
        "Represent protocole as an ordered dict, for sharing to other experiments or dumping as YAML file"
        initDict=OrderedDict({"_description" : "This file defines a titration's initial parameters."})
        unordered = {
            'name' : self.name,
            'titrant' : self.titrant,
            'analyte' : self.analyte,
            'start_volume': {
                "analyte" : self.analyteStartVol,
                "total" : self.startVol
            },
            'add_volumes': self.volumes
        }
        # ordered
        initDict.update([ (field, unordered[field]) for field in self.INIT_FIELDS])
        return initDict
