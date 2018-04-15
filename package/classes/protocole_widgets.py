from ipywidgets import *
from ipyfileupload.widgets import DirectoryUploadWidget
from traitlets import observe
import base64, io
import pandas as pd

from classes.widgets_base import *
from classes.Titration import Titration
from classes.bqplotwidgets import ChemshiftPanel


class NameWidget(TextControlWidget):
    "Sets study name"

    widget_kw = {
        'description' : 'Experiment name:',
        'style': {'description_width': '130px'},
    }

    def __init__(self, *args, **kwargs):
        TextControlWidget.__init__(self, 'name', *args, **kwargs)

    def set_value(self, value):
        self.titration.set_name(value)

    def update(self):
        self.value = self.titration.name


class ConcentrationWidget(FloatControlWidget):
    """Sets concentration for one of the molecule

    molecule : str 'analyte', 'titrant'
    """

    widget_kw = {
        'min': 0,
        'max': 100000,
        "layout" : Layout(width='100px'),
        #'style' : {'description_width':'100px'}
    }

    def __init__(self, molecule, *args, **kwargs):
        FloatControlWidget.__init__(self, molecule, *args, **kwargs)

    def set_value(self, value):
        "Set concentration for target molecule."
        getattr(self.titration.protocole, self.endpoint)['concentration'] = value

    def update(self):
        "Get concentration value for target molecule"
        self.value = getattr(self.titration.protocole, self.endpoint)['concentration']
        return self.value


class MoleculeNameWidget(TextControlWidget):
    """Sets name for one of the molecule

    molecule : str 'analyte', 'titrant'
    """

    widget_kw = {
        "layout" : Layout(width='100px'),
        #'style' : {'description_width':'100px'}
    }

    def __init__(self, molecule, *args, **kwargs):
        TextControlWidget.__init__(self, molecule, *args, **kwargs)

    def set_value(self, value):
        "Set name for target molecule."
        getattr(self.titration.protocole, self.endpoint)['name'] = value

    def update(self):
        "Get name of target molecule"
        self.value = getattr(self.titration.protocole, self.endpoint)['name']
        return self.value


class SingleMolContainer(TitrationWidget,VBox):

    desc_kwargs = {
        'style': {'description_width': '35%'},
        'layout': Layout(width="160px")
    }

    def __init__(self, target, desc=False, *args, **kwargs):
        assert target in ('analyte', 'titrant'), "Invalid argument {arg}: must be 'analyte' or 'titrant'"

        VBox.__init__(self, *args, **kwargs)
        self.add_class('align-right')

        self.label = Label(value=target.title(), layout=Layout(width="100px"))
        self.label.add_class('form-head-label')

        if desc:
            self.name_field = MoleculeNameWidget(target, description = "Name:", **self.desc_kwargs)
            self.conc_field = ConcentrationWidget(target, description = "[µM]:", **self.desc_kwargs)
        else:
            self.name_field = MoleculeNameWidget(target)
            self.conc_field = ConcentrationWidget(target)


        self.children = (self.label, self.name_field, self.conc_field)

    def children_observe(self, func, name = 'value'):
        self.name_field.observe(func, name)
        self.conc_field.observe(func, name)

    def update(self):
        self.name_field.update()
        self.conc_field.update()


class MoleculesContainer(TitrationWidget, HBox):

    def __init__(self, *args,**kwargs):
        HBox.__init__(self, *args, **kwargs)

        self.analyte = SingleMolContainer('analyte', desc=True)
        self.titrant = SingleMolContainer('titrant')
        self.children = (self.analyte, self.titrant)

    def children_observe(self, func, name='value'):
        self.analyte.children_observe(func, name)
        self.titrant.children_observe(func, name)

    def update(self):
        self.analyte.update()
        self.titrant.update()


class StartVolumeForm(TitrationWidget, VBox):

    vol_layout_kw = {
        'style': {'description_width': '100px'},
        'layout': Layout(width="200px")
    }

    def __init__(self, *args, **kwargs):
        VBox.__init__(self, *args, **kwargs)
        self.add_class('align-right')

        self.label = Label('Initial volumes', layout=Layout(width="100px"))
        self.label.add_class('form-head-label')
        self.analyteStartVol = FloatControlWidget(
            'analyteStartVol',
            description='Analyte (µL):',
            **self.vol_layout_kw)
        self.startVol = FloatControlWidget(
            'startVol',
            description='Total (µL):',
            **self.vol_layout_kw)

        self.analyteStartVol.observe(self.on_change, 'value')
        self.startVol.observe(self.on_change, 'value')

        self.children = [
            HBox([self.label],layout=Layout(width="200px", justify_content="flex-end")),
            self.analyteStartVol,
            self.startVol
        ]

    def on_change(self, change=None):
        if change['owner'] is self.analyteStartVol:
            self.startVol.min = change['new']

    def children_observe(self, func):
        self.analyteStartVol.observe(func)
        self.startVol.observe(func)

    def update(self, change=None):
        self.analyteStartVol.update()
        self.startVol.update()


class StartParamContainer(TitrationWidget, PanelContainer):

    def __init__(self, *args, **kwargs):
        PanelContainer.__init__(self, layout=Layout(min_width='350px', width='68%'), *args, **kwargs)
        self.add_class('start-param-container')
        self.observers = set()

        # name_kw = dict(self.layout_kw)
        # name_kw['layout'] = Layout(width="335px")


        # HEADING
        panelHeader = Label('Protocole parameters')
        panelHeader.add_class('panel-header-title')
        self.set_heading([panelHeader])

        # BODY
        # Name
        # self.titrationName = NameWidget(layout=Layout(margin='auto'))
        # self.titrationName.add_class('bold-label')
        # self.titrationName.observe(self.on_change, 'value')

        # Titrant and analyte
        self.molecules = MoleculesContainer()
        self.molecules.add_class('well')
        self.molecules.add_class('molecules-param')
        self.molecules.layout = Layout(align_items='center', justify_content='center')
        self.molecules.children_observe(self.on_change)

        # Initial volumes
        self.volumeForm = StartVolumeForm()
        self.volumeForm.add_class('well')
        self.volumeForm.add_class('volumes-param')
        self.volumeForm.layout = Layout(align_items='center')
        self.volumeForm.children_observe(self.on_change)

        form = HBox(
            [self.molecules, self.volumeForm],
            layout=Layout(justify_content='space-around'))

        self.set_content([
            #self.titrationName,
            form ])

    def add_observer(self, func):
        self.observers.add(func)

    def on_change(self, change):
        for obs in self.observers:
            obs(change)

    def update(self, change=None):
        # self.titrationName.update()
        self.volumeForm.update()
        self.molecules.update()


class VolumeWidget(TitrationWidget, BoundedFloatText, WidgetKwargs):

    widget_kw = {
        'min': 0,
        'max': 100000,
        "layout" : Layout(width='100%', height='28px'),
        'style' : {'description_width':'50%'}
    }

    def __init__(self, step_id, *args, **kwargs):
        self.step_id = int(step_id)
        type(self).update_kwargs(kwargs)
        kwargs['description'] = "Step {number:d}".format(number=self.step_id)
        BoundedFloatText.__init__(self, *args,**kwargs)
        self.add_class('volume-input-widget')



class VolumePanel(TitrationWidget, PanelContainer):

    def __init__(self, *args, **kwargs):
        PanelContainer.__init__(self, *args, **kwargs)
        self.add_class('volumes-container')

        self.observers = set()

        # HEADING
        self.label = Label("Added {titrant} (µL)".format(
            titrant=self.titration.protocole.titrant['name']))
        self.label.add_class('panel-header-title')

        self.add_btn = Button(
            description = 'Add',
            button_style='primary',
            layout=Layout(width='30%'),
            icon="plus-circle")
        self.add_btn.on_click(self.add_volume)

        self.steps_input = BoundedIntText(
            min=0,
            max=25,
            layout=Layout(width='25%'),
            tooltip="Set number of steps"
        )
        self.steps_input.observe(self.set_steps, 'value')

        self.remove_btn = Button(
            description='Remove',
            button_style='warning',
            layout=Layout(width='30%'),
            disabled=True,
            icon="minus-circle")
        self.remove_btn.on_click(self.remove_volume)


        self.buttons = HBox(
            [self.remove_btn, self.steps_input, self.add_btn],
            layout=Layout(
                padding="5px",
                justify_content="space-around"))

        self.set_heading([self.label, self.buttons])


        # BODY
        self.volumesBox = VBox(
            [],
            layout=Layout(
                display='flex',
                flex_flow="column",
                padding='5px 5px 5px 5px'))
        self.set_content([self.volumesBox])

        # FOOTER

        # Create form
        self.volWidgets = []
        for volume in self.titration.protocole.volumes:
            self.add_volume()

    @property
    def steps(self):
        return self.steps_input.value

    def set_steps(self,change):
        while change['new'] < len(self.volWidgets)-1:
            self.remove_volume(button=change['owner'])
        while change['new'] > len(self.volWidgets)-1:
            self.add_volume(button=change['owner'])

    def update(self, change=None):
        if change:
            self.label.value = "Added {titrant} (µL)".format(
                titrant=self.titration.protocole.titrant['name'])

        for idx, volume in enumerate(self.titration.protocole.volumes):
            try:
                self.volWidgets[idx].value = volume
            except IndexError:
                self.add_volume(updating=True)
        self.update_children()

    def update_children(self):
        self.volumesBox.children = self.volWidgets

    def send_volumes(self, button=None):
        "Updates endpoint volume list"
        self.titration.protocole.set_volumes(self.volumes)
        self.update_children()
        self.on_change()

    def add_volume(self, button=None, updating=False):
        "Appends a new volume form field"

        if self.volWidgets:
            min_value=1
            self.remove_btn.disabled = False
            disabled = False
        else: # disable the first one (reference)
            disabled = True
            min_value=0


        # use existing value in titration endpoint
        if self.steps < len(self.titration.protocole['vol_add']):
            value = self.titration.protocole['vol_add'][self.steps]
        else: # use value from previous field as default
            value = self.volWidgets[-1].value

        # create widget
        widget = VolumeWidget(
            len(self.volWidgets),
            value=value,
            min=min_value,
            disabled=disabled)
        # update endpoint on field change
        widget.observe(self.send_volumes, 'value')
        self.volWidgets.append(widget) # add to volume list

        self.update_children() # display volume in box
        if not updating:
            self.send_volumes() # update endpoint
        if button is not self.steps_input and len(self.volWidgets)>1:
            self.steps_input.value += 1

    def remove_volume(self, button=None):
        "Removes last volume field"
        if len(self.volWidgets) > 1:
            vol =  self.volWidgets.pop()
            del vol
            self.update_children()
            self.send_volumes()
            if button is not self.steps_input:
                self.steps_input.value -= 1
        if self.steps < 1:
            self.remove_btn.disabled = True


    def add_observer(self, func):
        self.observers.add(func)

    def on_change(self, change=None):
        for obs in self.observers:
            obs(change)

    @property
    def volumes(self):
        return [widget.value for widget in self.volWidgets]


class ProtocolePanel(TitrationWidget, PanelContainer):

    def __init__(self, *args, **kwargs):

        self.title = Label('Protocole')
        self.title.add_class('panel-header-title')

        PanelContainer.__init__(self, heading=[self.title],  *args, **kwargs)

        self.update()

    def update(self, change=None):
        self.table = HTML(self.titration.protocole.update(index=False).to_html(index=False))
        self.table._dom_classes += ('rendered_html', 'protocole-table')
        self.set_content([self.table])



class ProtocoleContainer(HBox):

    def __init__(self, *args, **kwargs):
        HBox.__init__(self, *args, **kwargs, layout=Layout(justify_content='space-around'))

        self.volumes = VolumePanel(layout=Layout(width='30%', height="auto"))
        self.volumes.add_observer(self.on_submit)

        self.protocole = ProtocolePanel(layout=Layout(width='68%', height="auto"))

        self.children = (self.volumes, self.protocole)

    def on_submit(self, button):
        self.protocole.update()

    def update(self, change=None):
        self.volumes.update()
        self.protocole.update()
