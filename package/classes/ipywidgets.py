from ipywidgets import *
from ipyfileupload.widgets import DirectoryUploadWidget
from traitlets import observe
import base64, io
import pandas as pd

from classes.widgets_base import *
from classes.Titration import Titration
from classes.bqplotwidgets import ChemshiftPanel
from classes.protocole_widgets import *




class TitrationDirUploader(TitrationWidget, DirectoryUploadWidget):

    def __init__(self, *args, **kwargs):
        DirectoryUploadWidget.__init__(self, *args, **kwargs)
        self.label = "Upload titration directory"
        self.output = Output()
        self.observers = set()
        self.add_class('upload-directory-btn')

    def dispatch(self):
        for obs in self.observers:
            obs()

    def add_observer(self, func):
        "Observer must have a update() method"
        self.observers.add(func)

    @observe('files')
    def _files_changed(self, *args):
        if self.files:
            current_protocole = self.titration.protocole.as_init_dict
            self.titration.__init__()
            self.titration.protocole.load_init_dict(current_protocole, validate=False)
            self.extract_chemshifts()
            self.extract_protocole()
            self.dispatch()

    @observe('base64_files')
    def _base64_files_changed(self, *args):
        self.files = {}
        for name, file in self.base64_files.items():
            self.files[name] = base64.b64decode(file.split(',',1)[1])
        self._files_changed(self, *args)
        self.base_64_files = {}

    def extract_chemshifts(self):
        filenames = set([file for file in self.files.keys() if file.endswith('.list')]) - set(self.titration.files)
        filenames = sorted(filenames, key=self.titration.validate_filepath)
        with self.output:
            for fname in filenames:
                self.titration.add_step(fname, io.StringIO(self.files[fname].decode('utf-8')))

    def extract_protocole(self):
        filenames = set([file for file in self.files.keys() if file.endswith('.yml')])
        with self.output:
            for fname in filenames:
                self.titration.protocole.load_init_file(io.StringIO(self.files[fname].decode('utf-8')))


class TitrationFilesView(TitrationWidget, PanelContainer ):

    HeaderBox = HBox

    def __init__(self, *args, **kwargs):

        PanelContainer.__init__(self, *args,**kwargs)

        self.add_class('data-files-view')

        self.label = Label("Data files")
        self.label.add_class('panel-header-title')
        self.files_count = Label('0', layout=Layout(width="26px", height="26px"))
        self.files_count.add_class("badge")
        self.layout.width="30%"
        self.content.layout.max_height="200px"
        self.content.layout.height="200px"
        self.content.layout.overflow_x="scroll"
        self.content.layout.overflow_y="scroll"
        self.content.layout.display="inline-block"
        self.content.add_class('list-group')

        self.set_heading([self.label, self.files_count])
        self.uploader = TitrationDirUploader()
        self.uploader.add_class('file-uploader')
        self.uploader.add_observer(self.update)
        self.add_footer([self.uploader])
        self.update()

    def update(self):
        self.files = self.titration.files
        content = []
        if self.files:
            for file in self.files:
                flabel = Label(file)
                flabel.add_class('list-group-item')
                content.append(flabel)
            # content = HTML(pd.DataFrame(data=self.files).to_html(index=False, header=False))
        else:
            content = [Label('No files yet.')]
        self.set_content(content)
        self.files_count.value = str(len(self.files))

class Shift2Me(TitrationWidget, VBox):


    def __init__(self, *args, **kwargs):
        TitrationWidget.titration = Titration()
        VBox.__init__(self, *args, **kwargs)
        self.layout=Layout(align_content='space-between')

        self.uploadview = TitrationFilesView()
        self.chemshifts = ChemshiftPanel(self.uploadview.uploader)
        self.startParams = StartParamContainer()
        self.protocole = ProtocoleContainer()

        self.connect()

        self.children = [
            HBox(
                [self.uploadview,self.startParams],layout=Layout(justify_content='space-around')
            ),
            self.protocole,
            self.chemshifts
            ]

    def connect(self):
        self.uploadview.uploader.add_observer(self.startParams.update)
        self.uploadview.uploader.add_observer(self.protocole.update)
        self.startParams.add_observer(self.protocole.protocole.update)
        self.startParams.add_observer(self.chemshifts.update_curves)
        self.startParams.molecules.titrant.name_field.observe(self.protocole.volumes.update, 'value')
        self.protocole.volumes.add_observer(self.chemshifts.update_curves)
        #self.protocole.volumes.validate_button.on_click(self.chemshifts.update_curves)

