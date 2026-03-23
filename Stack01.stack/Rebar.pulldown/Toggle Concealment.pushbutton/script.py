# -*- coding: utf-8 -*-
__title__ = "Toggle Rebar Visibility"
__author__ = "Fred da Silveira"
__version__ = 'Version = 1.0'
__doc__ = """Version = 1.0
Date    = 13.11.2025
_____________________________________________________________________
Description:
Intelligently toggles rebar visibility (obscured/unobscured) in the current view.
Detects current state and applies smart logic:
- Mixed state → Make all unobscured
- All obscured → Make all unobscured
- All unobscured → Make all obscured
_____________________________________________________________________
Last update:
13.11.2025
- Initial release
- Smart state detection
- Intelligent toggle logic
_____________________________________________________________________
How-to:
-> Open a view containing rebar elements
-> Run the script
-> Script automatically detects current state and toggles accordingly
-> Success message confirms the action taken
_____________________________________________________________________
Author: Fred da Silveira"""

import clr
from Autodesk.Revit import DB
from pyrevit import forms, script

# Access the Revit document and active view
doc = __revit__.ActiveUIDocument.Document
active_view = doc.ActiveView

def get_rebars_in_current_view():
    """Retrieve all rebar elements visible in the current view."""
    collector = DB.FilteredElementCollector(doc, active_view.Id)\
                  .OfCategory(DB.BuiltInCategory.OST_Rebar)\
                  .WhereElementIsNotElementType()
    return collector.ToElements()

def check_rebar_states(rebars):
    """Check the current visibility state of all rebars.
    Returns: (obscured_count, unobscured_count)
    """
    obscured_count = 0
    unobscured_count = 0
    
    for rebar in rebars:
        if rebar.IsUnobscuredInView(active_view):
            unobscured_count += 1
        else:
            obscured_count += 1
    
    return obscured_count, unobscured_count

def set_rebar_visibility(rebars, make_unobscured):
    """Set rebar visibility states.
    
    Args:
        rebars: Collection of rebar elements
        make_unobscured: True to make unobscured, False to make obscured
    """
    for rebar in rebars:
        rebar.SetUnobscuredInView(active_view, make_unobscured)

# Collect all rebars in the current view
rebars_in_view = get_rebars_in_current_view()

if not rebars_in_view:
    forms.alert("No rebars found in the current view.", title="Error")
    script.exit()

# Check current state
obscured_count, unobscured_count = check_rebar_states(rebars_in_view)

# Determine action based on current state
if obscured_count > 0 and unobscured_count > 0:
    # Mixed state: make all unobscured
    make_unobscured = True
    action_description = "Set All Rebar Unobscured (Mixed State)"
elif unobscured_count == len(rebars_in_view):
    # All unobscured: make obscured
    make_unobscured = False
    action_description = "Set All Rebar Obscured"
else:
    # All obscured: make unobscured
    make_unobscured = True
    action_description = "Set All Rebar Unobscured"

# Start a transaction to modify rebar properties
t = DB.Transaction(doc, action_description)
t.Start()

try:
    set_rebar_visibility(rebars_in_view, make_unobscured)
    t.Commit()
except Exception as e:
    t.RollBack()
    forms.alert(
        "Error: {}".format(str(e)),
        title="Transaction Failed"
    )