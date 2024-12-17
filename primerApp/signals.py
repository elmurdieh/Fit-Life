from django.db.models.signals import post_save
from django.dispatch import receiver
from primerApp.models import integra, claseGrupal

@receiver(post_save, sender=integra)
def verificar_max_participantes(sender, instance, **kwargs):
    clase = instance.clase_grupal
    participantes_actuales = integra.objects.filter(clase_grupal=clase).count()
    print(f"DEBUG: Clase {clase.nombre} tiene {participantes_actuales} participantes, máximo permitido: {clase.max_participantes}")

    if participantes_actuales >= clase.max_participantes:
        print(f"DEBUG: Clase {clase.nombre} ha alcanzado el máximo de participantes.")
        clase.estatus_llenado = True
        clase.save()
    else:
        print(f"DEBUG: Clase {clase.nombre} no ha alcanzado el máximo de participantes.")

