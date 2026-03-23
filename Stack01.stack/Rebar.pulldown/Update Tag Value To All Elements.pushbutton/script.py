from pyrevit import revit, DB, forms

def get_param_value(param):
    try:
        if param.StorageType == DB.StorageType.String:
            return param.AsString()
        else:
            return None
    except:
        return None

tag_elem = revit.pick_element(message="Select a Tag element")
if not tag_elem:
    forms.alert("No tag element selected. Exiting.")
    exit()

try:
    host_ids = list(tag_elem.GetTaggedLocalElementIds())
except Exception:
    forms.alert("Selected element is not a tag or unsupported tag type.")
    exit()

if not host_ids:
    forms.alert("Tag does not reference any host elements.")
    exit()

host_elem = revit.doc.GetElement(host_ids[0])
if not host_elem:
    forms.alert("Could not find host element for the selected tag.")
    exit()

# Collect all text parameters on host element
text_params = []
for p in host_elem.Parameters:
    if p.StorageType == DB.StorageType.String and not p.IsReadOnly:
        text_params.append(p)

if not text_params:
    forms.alert("No editable text parameters found on host element.")
    exit()

param_names = [p.Definition.Name for p in text_params]
selected_param_name = forms.SelectFromList.show(param_names, title="Select Text Parameter to Edit")
if not selected_param_name:
    forms.alert("No parameter selected. Exiting.")
    exit()

selected_param = None
for p in text_params:
    if p.Definition.Name == selected_param_name:
        selected_param = p
        break

old_value = get_param_value(selected_param)

new_value = forms.ask_for_string(default=old_value if old_value else "", prompt="Old value: '{}'. Enter new value to set:".format(old_value))
if new_value is None:
    forms.alert("No new value entered. Exiting.")
    exit()

collector = DB.FilteredElementCollector(revit.doc).WhereElementIsNotElementType()
elements_to_update = []
for elem in collector:
    param = elem.LookupParameter(selected_param_name)
    if param and param.StorageType == DB.StorageType.String:
        val = param.AsString()
        if val == old_value:
            elements_to_update.append(elem)

t = DB.Transaction(revit.doc, "Update Text Parameter Values")
t.Start()
for elem in elements_to_update:
    param = elem.LookupParameter(selected_param_name)
    if param and not param.IsReadOnly:
        try:
            param.Set(new_value)
        except:
            pass
t.Commit()

forms.alert("Updated {} elements with parameter '{}' from '{}' to '{}'.".format(len(elements_to_update), selected_param_name, old_value, new_value))
