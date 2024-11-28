from django import forms
from primerApp.models import administrador, solicitudCG, claseGrupal, equipo, producto, cliente, integra

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

class clienteForm(forms.ModelForm):
    class Meta:
        model = cliente
        fields = '__all__'

class integraForm(forms.ModelForm):
    class Meta:
        model = integra
        fields = '__all__'