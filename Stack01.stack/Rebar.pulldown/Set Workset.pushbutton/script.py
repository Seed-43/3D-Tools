# -*- coding: utf-8 -*-
__title__ = "Set Rebar to Workset"
__author__ = "Fred da Silveira"
__version__ = 'Version = 1.0'
__doc__ = """Version = 1.0
Date    = 13.11.2025
_____________________________________________________________________
Description:
Assigns all rebar elements in the model to a selected workset.
Smart workset detection:
- If one rebar workset exists → Uses it automatically
- If multiple rebar worksets exist → Shows selection list + Other option
- If no rebar worksets exist → Shows all worksets + Create New option
_____________________________________________________________________
Last update:
13.11.2025
- Initial release with header documentation
- Smart rebar workset detection
- Create new workset option
_____________________________________________________________________
How-to:
-> Run the script in a workshared Revit model
-> Select target workset (auto-detected if only one rebar workset exists)
-> All rebar elements are assigned to the selected workset
-> Success message shows count of elements updated
_____________________________________________________________________
Author: Fred da Silveira"""

from pyrevit import revit, DB, forms
from Autodesk.Revit.DB import FilteredWorksetCollector, WorksetKind

doc = revit.doc
uidoc = revit.uidoc

# Get worksets
worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets()

# Filter rebar worksets (case insensitive)
rebar_worksets = [ws for ws in worksets if 'rebar' in ws.Name.lower()]

def get_target_workset():
    num_rebar = len(rebar_worksets)
    if num_rebar == 1:
        return rebar_worksets[0]
    elif num_rebar > 1:
        # LIST 2: Rebar worksets + Other
        options = [ws.Name for ws in rebar_worksets] + ['Other']
        selected_name = forms.SelectFromList.show(options, button_name='Select Rebar Workset')
        if not selected_name:
            forms.alert('Operation cancelled.')
            return None
        if selected_name == 'Other':
            return select_or_create_workset()
        else:
            return next(ws for ws in rebar_worksets if ws.Name == selected_name)
    else:
        # No rebar worksets, directly LIST 1
        return select_or_create_workset()

def select_or_create_workset():
    # LIST 1: All user worksets + Create New
    options = [ws.Name for ws in worksets] + ['Create New']
    selected_name = forms.SelectFromList.show(options, button_name='Select or Create Workset')
    if not selected_name:
        forms.alert('Operation cancelled.')
        return None
    if selected_name == 'Create New':
        new_name = forms.ask_for_string(prompt='Enter name for new Rebar workset:', default='Rebar')
        if not new_name:
            forms.alert('Invalid name. Operation cancelled.')
            return None
        try:
            transaction = DB.Transaction(doc, 'Create Rebar Workset')
            transaction.Start()
            new_ws = DB.Workset.Create(doc, new_name)
            transaction.Commit()
            return new_ws
        except Exception as e:
            if transaction.HasStarted():
                transaction.RollBack()
            forms.alert('Failed to create workset: {}'.format(str(e)))
            return None
    else:
        return next(ws for ws in worksets if ws.Name == selected_name)

# Get target workset
target_ws = get_target_workset()
if not target_ws:
    # Script ends if no workset selected
    import sys
    sys.exit()

# Collect all rebar elements
collector = DB.FilteredElementCollector(doc).OfClass(DB.Structure.Rebar).WhereElementIsNotElementType()
rebar_elements = list(collector)

if not rebar_elements:
    forms.alert('No rebar elements found in the model.')
    import sys
    sys.exit()

# Set workset
count = 0
transaction = DB.Transaction(doc, 'Set Rebar to Workset')
transaction.Start()
try:
    for elem in rebar_elements:
        param = elem.get_Parameter(DB.BuiltInParameter.ELEM_PARTITION_PARAM)
        if param and not param.IsReadOnly:
            param.Set(target_ws.Id.IntegerValue)
            count += 1
    transaction.Commit()
    forms.alert('Successfully set {} rebar elements to "{}" workset.'.format(count, target_ws.Name))
except Exception as e:
    if transaction.HasStarted():
        transaction.RollBack()
    forms.alert('Error: {}'.format(str(e)))