from django import forms
from primerApp.models import administrador, solicitudCG, claseGrupal, equipo, producto

class formAdministrador(forms.ModelForm):
    class Meta:
        model = administrador
        fields = '__all__'

class formClaseGrupal(forms.ModelForm):
    class Meta:
        model = claseGrupal
        fields = '__all__'

class formSolicitudCG(forms.ModelForm):
    class Meta:
        model = solicitudCG
        fields = '__all__'

class formEquipo(forms.ModelForm):
    class Meta:
        model = equipo
        fields = '__all__'
class formProducto(forms.ModelForm):
    class Meta:
        model = producto
        fields = '__all__'

class formCG(forms.ModelForm):
    class Meta:
        model = solicitudCG
        fields = '__all__'