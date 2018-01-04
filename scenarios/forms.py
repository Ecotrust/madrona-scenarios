from features.forms import FeatureForm, SpatialFeatureForm
from django import forms
from django.forms import ModelMultipleChoiceField, CheckboxSelectMultiple
from django.forms.widgets import *
from os.path import splitext
from analysistools.widgets import SliderWidget, DualSliderWidget
from scenarios.models import *
from scenarios.widgets import AdminFileWidget, SliderWidgetWithTooltip, DualSliderWidgetWithTooltip, CheckboxSelectMultipleWithTooltip, CheckboxSelectMultipleWithObjTooltip

# WEA_CHOICES = ( ('constrain', 'Constrain the result to the following WEAs'), ('exclude', 'Exclude the following WEAs') )

# http://www.neverfriday.com/sweetfriday/2008/09/-a-long-time-ago.html
class FileValidationError(forms.ValidationError):
    def __init__(self):
        super(FileValidationError, self).__init__('Document types accepted: ' + ', '.join(ValidFileField.valid_file_extensions))

class ValidFileField(forms.FileField):
    """A validating document upload field"""
    valid_file_extensions = ['odt', 'pdf', 'doc', 'xls', 'txt', 'csv', 'kml', 'kmz', 'jpeg', 'jpg', 'png', 'gif', 'zip']

    def __init__(self, *args, **kwargs):
        super(ValidFileField, self).__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        f = super(ValidFileField, self).clean(data, initial)
        if f:
            ext = splitext(f.name)[1][1:].lower()
            if ext in ValidFileField.valid_file_extensions:
                # check data['content-type'] ?
                return f
            raise FileValidationError()

class ScenarioForm(FeatureForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 30, 'rows': 3}), required=False)

    #RDH Generic updates 12/15/2017: I have no idea if we need this, but it isn't hurting anything (yet).
    support_file = ValidFileField(widget=AdminFileWidget,required=False,label="Support File")

    area = forms.BooleanField(
        label="Area",
        required=False,
        help_text="Area of Planning Unit in sq. meters",
        widget=CheckboxInput(
            attrs={
                'class': 'parameters hidden_checkbox'
            }
        )
    )
    area_min = forms.FloatField(
        required=False,
        initial=310000000,
        widget=forms.TextInput(
            attrs={
                'class': 'slidervalue',
                'pre_text': 'Area'
            }
        )
    )
    area_max = forms.FloatField(
        required=False,
        initial=5900000000,
        widget=forms.TextInput(
            attrs={
                'class': 'slidervalue',
                'pre_text': 'to',
                'post_text': 'm<sup>2</sup>'
            }
        )
    )
    area_input = forms.FloatField(
        widget=DualSliderWidget(
            'area_min',
            'area_max',
            min=3000000000,
            max=6000000000,
            step=10000000
        )
    )

    def get_step_0_fields(self):
        names = [
            ('area', 'area_min', 'area_max', 'area_input'),
        ]
        return self._get_fields(names)

    def get_step_1_fields(self):
        names = []
        return self._get_fields(names)

    def get_steps(self):
        return self.get_step_0_fields(),

    def _get_fields(self, names):
        fields = []
        for name_list in names:
            group = []
            for name in name_list:
                if name:
                    group.append(self[name])
                else:
                    group.append(None)
            while len(group) < 5:
                group.append(None)
            fields.append(group)
        return fields

    ###
    # is_valid() and clean() are included here to take care of some trickiness with how checkbox lists are implemented. Override these in the manner you see commented out below if you use this widget.
    ###
    def is_valid(self, *args, **kwargs):
        # validation fails because what the model expects, what the form expects, and how we manage these values do not match.
        # if len(self.errors.keys()) == 1 and self.errors.keys()[0] == 'hsall_m2_checkboxes' and len(self.errors['hsall_m2_checkboxes']) == 1 and 'is not one of the available choices.' in self.errors['hsall_m2_checkboxes'][0]:
        #     del self._errors['hsall_m2_checkboxes']
        return super(FeatureForm, self).is_valid()

    def clean(self):
        super(FeatureForm, self).clean()
        # try:
        #     if 'hsall_m2_checkboxes' not in self.cleaned_data.keys() and self.cleaned_data['hsall_m2'] == True:
        #         checkdata = self.data.getlist('hsall_m2_checkboxes')
        #         checklist = False
        #         for box in checkdata:
        #             if not box == 'False':
        #                 checklist = True
        #                 self.cleaned_data['hsall_m2_checkboxes'] = unicode([unicode(x) for x in box.split(',')])
        #
        #         if not checklist:
        #             self.data.__delitem__('hsall_m2_checkboxes')
        # except Exception as e:
        #     print(e)
        #     pass
        return self.cleaned_data

    def save(self, commit=True):
        inst = super(FeatureForm, self).save(commit=False)
        if self.data.get('clear_support_file'):
            inst.support_file = None
        if commit:
            inst.save()
        return inst

    class Meta(FeatureForm.Meta):
        model = Scenario
        exclude = list(FeatureForm.Meta.exclude)
        for f in model.output_fields():
            exclude.append(f.attname)
        widgets = {}


class PlanningUnitSelectionForm(FeatureForm):
    planningunit_ids = forms.CharField()
    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 30, 'rows': 3}), required=False)

    class Meta(FeatureForm.Meta):
        model = PlanningUnitSelection
        exclude = list(FeatureForm.Meta.exclude)
        for f in model.output_fields():
            exclude.append(f.attname)
