from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from primerApp.models import administrador, equipo, claseGrupal, producto, solicitudCG, cliente, integra
from primerApp.forms import formAdministrador,formEquipo,formClaseGrupal, formProducto, formCG, integraForm
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


def index(request):
    clases = claseGrupal.objects.all()
    productos = producto.objects.all()
    data = {'clasesGrupales' : clases,
            'productos' : productos
            }
    return render(request, 'primerApp/index.html', data)


def interfazCG(request, id):
    clase = claseGrupal.objects.select_related('entrenador').get(id=id)
    entrenador = clase.entrenador
    form = formCG()

    if request.method == 'POST':
        form = formCG(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.fechaSolicitud = timezone.now()
            solicitud.save()

            recipient_email = form.cleaned_data['correoElectronico']
            subject = f'Solicitud recibida para la clase grupal {clase.nombre}'
            message = f'Hola {form.cleaned_data["nombreCompleto"]},\n\nTu solicitud para la clase grupal {clase.nombre} ha sido recibida correctamente.\n\nFecha de ingreso: {solicitud.fechaSolicitud}.\n\n Este es tu codigo para cancelar tu Solicitud en caso de algun inconveniente {solicitud.codigo}'
            from_email = settings.EMAIL_HOST_USER
            send_mail(
                subject,
                message,
                from_email,
                [recipient_email],
                fail_silently=False,
            )

            print('Solicitud enviada correctamente y correo enviado.')
            return redirect("/")
        else:
            print('Error al enviar la solicitud')
            print(form.errors)

    data = {
        'clase': clase,
        'entrenador': entrenador,
        'formClase': form,
    }
    return render(request, 'primerApp/interfazCG.html', data)

def registrar(request):
    form = formAdministrador()
    
    if request.method == 'POST':
        form = formAdministrador(request.POST)
        if form.is_valid():
            administrador = form.save(commit=False)
            administrador.contraseña = make_password(form.cleaned_data['contraseña'])
            print("Contraseña encriptada:", administrador.contraseña)
            administrador.save()
            return redirect('/')
    
    data = {'form': form}
    return render(request, 'primerApp/registro.html', data)

def inicioSesion(request):
    if request.method == 'POST':
        if 'rut' in request.POST and 'contraseña' in request.POST:
            rut = request.POST['rut']
            contraseña = request.POST['contraseña']
            try:
                usuario = administrador.objects.get(rut=rut)
                if check_password(contraseña, usuario.contraseña):
                    request.session['usuario_id'] = usuario.id
                    return redirect(f'/administrar/{usuario.rut}/')
                else:
                    messages.error(request, 'Contraseña incorrecta')
            except administrador.DoesNotExist:
                messages.error(request, 'El RUT ingresado no está registrado')
        else:
            messages.error(request, 'Complete ambos campos')
    
    return render(request, 'primerApp/inicioSesion.html')

def cerrarSesion(request):
    if 'usuario_id' in request.session:
        request.session.flush()
    return redirect('/')


def ventanaAdministrador(request, rut):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')

    try:
        usuario = administrador.objects.get(rut=rut)
        if request.session.get('usuario_id') != usuario.id:
            return redirect('/inicio_de_Sesion/')

        form_equipo = formEquipo()
        form_clase_grupal = formClaseGrupal()
        form_producto = formProducto()

        entrenadores = equipo.objects.filter(rol="entrenador")
        clasesGrupales = claseGrupal.objects.all()
        personal = equipo.objects.all()
        productos = producto.objects.all()

        if request.method == 'POST':
            if 'submit_equipo' in request.POST:
                form_equipo = formEquipo(request.POST, request.FILES)
                if form_equipo.is_valid():
                    form_equipo.save()
                    print("Perfil del equipo creado exitosamente.")
                    return redirect(f'/administrar/{usuario.rut}/')
                else:
                    print("Error al crear el perfil del equipo. Verifique los datos.")
                    print(form_equipo.errors)
            elif 'submit_clase_grupal' in request.POST:
                form_clase_grupal = formClaseGrupal(request.POST, request.FILES)
                print("Archivos recibidos:", request.FILES)
                if form_clase_grupal.is_valid():
                    form_clase_grupal.save()
                    print("Clase grupal creada exitosamente.")
                    return redirect(f'/administrar/{usuario.rut}/')
                else:
                    print("Error al crear la clase grupal. Verifique los datos.")
                    print(form_clase_grupal.errors)
            elif 'submit_producto' in request.POST:
                form_producto = formProducto(request.POST, request.FILES)
                print("Archivos recibidos:", request.FILES)
                if form_producto.is_valid():
                    form_producto.save()
                    print("Producto creado exitosamente.")
                    return redirect(f'/administrar/{usuario.rut}/')
                else:
                    print("Error al crear el producto. Verifique los datos.")
                    print("Errores del formulario de producto:", form_producto.errors)

        # Datos que se pasarán al template
        data = {
            'usuario': usuario,
            'form_equipo': form_equipo,
            'form_clase_grupal': form_clase_grupal,
            'form_producto': form_producto,
            'entrenadores': entrenadores,
            'clasesGrupales': clasesGrupales,
            'personal' : personal,
            'productos' : productos
        }
    except administrador.DoesNotExist:
        print("Usuario no encontrado.")
        return redirect('/inicio_de_Sesion/')

    return render(request, 'primerApp/administrador.html', data)

def ventanaAdministrador2(request,rut):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')
    

    try:
        usuario = administrador.objects.get(rut=rut)
        if request.session.get('usuario_id') != usuario.id:
            return redirect('/inicio_de_Sesion/')
        
        solicitudesCG = solicitudCG.objects.filter(estado=False).select_related('CG')
        clasesG = claseGrupal.objects.all()

        data = {
            'solicitudesCG' : solicitudesCG,
            'usuario' : usuario,
            'clasesGrupales' : clasesG,
        }

    except administrador.DoesNotExist:
        print("Usuario no encontrado.")
        return redirect('/inicio_de_Sesion/')

    return render(request, 'primerApp/administradorVentana2.html', data)

def actualizarCG(request, id):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')
        
    clase = claseGrupal.objects.get(id=id)
    usuario = administrador.objects.get(id=request.session['usuario_id'])
    
    if request.method == 'POST':
        form = formClaseGrupal(request.POST, request.FILES, instance=clase)
        print("POST data:", request.POST)  # Para ver qué datos están llegando
        print("Form errors:", form.errors)  # Para ver si hay errores en el formulario
        if form.is_valid():
            form.save()
            return redirect(f'/administrar/{usuario.rut}/')
        else:
            print("Form is not valid")
    
    return redirect(f'/administrar/{usuario.rut}/')

def eliminarCG(request, id):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')
        
    clase = claseGrupal.objects.get(id=id)
    usuario = administrador.objects.get(id=request.session['usuario_id'])
    clase.delete()
    return redirect(f'/administrar/{usuario.rut}/')

def actualizarPro(request, id):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')
        
    pro = producto.objects.get(id=id)
    usuario = administrador.objects.get(id=request.session['usuario_id'])
    
    if request.method == 'POST':
        formPro = formProducto(request.POST, request.FILES, instance=pro)
        if formPro.is_valid():
            formPro.save()
            return redirect(f'/administrar/{usuario.rut}/')
    else:
        formPro = formProducto(instance=pro)
    
    data = {'formPro': formPro}
    return render(request, 'primerApp/editar_producto.html', data)

def eliminarPro(request, id):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')
        
    pro = producto.objects.get(id=id)
    usuario = administrador.objects.get(id=request.session['usuario_id'])
    pro.delete()
    return redirect(f'/administrar/{usuario.rut}/')

def actualizarEquipo(request, rut):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')
        
    miembro = equipo.objects.get(rut=rut)
    usuario = administrador.objects.get(id=request.session['usuario_id'])
    
    if request.method == 'POST':
        form = formEquipo(request.POST, request.FILES, instance=miembro)
        if form.is_valid():
            form.save()
            return redirect(f'/administrar/{usuario.rut}/')
    
    return redirect(f'/administrar/{usuario.rut}/')

def eliminarEquipo(request, rut):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')
        
    miembro = equipo.objects.get(rut=rut)
    usuario = administrador.objects.get(id=request.session['usuario_id'])
    miembro.delete()
    return redirect(f'/administrar/{usuario.rut}/')

def aprobar_solicitud(request, id):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')

    usuario = administrador.objects.get(id=request.session['usuario_id'])

    if request.method == 'POST':
        # Obtener la solicitud a aprobar
        solicitud = get_object_or_404(solicitudCG, id=id)

        # Marcar la solicitud como aprobada
        solicitud.estado = True
        solicitud.save()

        # Crear cliente con los datos de la solicitud
        cliente_creado = cliente.objects.create(
            nombreCompleto=solicitud.nombreCompleto,
            rut=solicitud.rut
        )

        # Crear la instancia en 'integra' con los datos adecuados
        integra.objects.create(
            cliente=cliente_creado,
            clase_grupal=solicitud.CG,  # Usando la clase grupal asociada
            solicitud=solicitud,
            estadoPago=False,  # Por defecto en False
            fecha_union=solicitud.fechaSolicitud  # Fecha de solicitud como fecha de unión
        )

        # Construir el enlace con el ID de la solicitud
        enlace = f"http://127.0.0.1:8000/bancoWeb/{solicitud.id}"

        # Enviar correo de aprobación
        recipient_email = solicitud.correoElectronico
        subject = '¡Solicitud Aprobada!'
        message = (f'Hola {solicitud.nombreCompleto},\n\n'
                   f'Tu solicitud para la clase grupal "{solicitud.CG.nombre}" ha sido aprobada.\n\n'
                   f'Ahora podrás pagar, ya sea de forma presencial en el establecimiento o ir a nuestro banco en línea:\n\n'
                   f'{enlace}\n\n'
                   f'Te esperamos en la fecha y hora acordada. ¡Gracias por elegirnos!\n\n'
                   f'- Equipo FitLife')
        from_email = settings.EMAIL_HOST_USER

        try:
            send_mail(
                subject,
                message,
                from_email,
                [recipient_email],
                fail_silently=False,
            )
            print('Correo de aprobación enviado correctamente.')
        except Exception as e:
            print(f'Error al enviar el correo de aprobación: {e}')

    return redirect(f'/administrar2/{usuario.rut}/')




def rechazar_solicitud(request, id):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')
    usuario = administrador.objects.get(id=request.session['usuario_id'])

    if request.method == 'POST':
        solicitud = get_object_or_404(solicitudCG, id=id)
        
        # Enviar correo de rechazo antes de eliminar
        recipient_email = solicitud.correoElectronico
        subject = 'Solicitud Rechazada'
        message = (f'Hola {solicitud.nombreCompleto},\n\n'
                   f'Lamentamos informarte que tu solicitud para la clase grupal "{solicitud.CG.nombre}" '
                   f'ha sido rechazada.\n\n'
                   f'Si tienes alguna consulta, no dudes en contactarnos.\n\n'
                   f'- Equipo FitLife')
        from_email = settings.EMAIL_HOST_USER

        try:
            send_mail(
                subject,
                message,
                from_email,
                [recipient_email],
                fail_silently=False,
            )
            print('Correo de rechazo enviado correctamente.')
        except Exception as e:
            print(f'Error al enviar el correo de rechazo: {e}')

        # Eliminar la solicitud después de enviar el correo
        solicitud.delete()

    return redirect(f'/administrar2/{usuario.rut}/')


def cancelarReserva(request,codigo):
    eliminar = solicitudCG.objects.get(codigo = codigo)
    if request.method == 'POST':
        eliminar.delete()
    return redirect("/")

def pagarServicio(request, id):
    solicitud = solicitudCG.objects.select_related('CG').get(id=id)

    # Pasar la solicitud a la plantilla
    data = {
        'solicitud': solicitud
    }

    return render(request, 'primerApp/bancoWeb.html', data)


def procesar_pago(request, id):
    if request.method == 'POST':
        try:
            # Obtener la solicitud
            solicitud = get_object_or_404(solicitudCG, id=id)

            # Obtener el objeto 'integra' relacionado
            integra_obj = get_object_or_404(integra, solicitud=solicitud)

            # Actualizar el estado de pago
            integra_obj.estadoPago = True
            integra_obj.save()

            # Agregar mensaje de éxito
            messages.success(request, 'Pago Realizado Correctamente')

            # Confirmar el cambio en la consola
            print(f"Estado de pago actualizado para la integración ID {integra_obj.id}: {integra_obj.estadoPago}")

            # Redirigir al usuario a la misma página
            return redirect(f"/")
        except integra.DoesNotExist:
            print("Error: No se encontró una integración para esta solicitud.")
            messages.error(request, 'Error: No se encontró la integración para esta solicitud.')
            return redirect(f"/bancoWeb/{id}/")
        except Exception as e:
            print(f"Error al procesar el pago: {e}")
            messages.error(request, 'Error inesperado al procesar el pago.')
            return redirect(f"/bancoWeb/{id}/")

def cancelar_solicitud(request):
    codigo = request.GET.get('codigo')  # Obtener el código ingresado en el input
    if not codigo:
        return redirect('/')  # Redirigir si no hay código proporcionado

    # Buscar la solicitud por código
    try:
        solicitud = solicitudCG.objects.get(codigo=codigo)  # Buscar por el código
        return render(request, 'primerApp/cancelarSolicitud.html', {'solicitud': solicitud})
    except solicitudCG.DoesNotExist:
        return redirect('/')  # Si no se encuentra la solicitud, redirigir a la página principal

def eliminar_solicitud(request, id):
    try:
        solicitud = solicitudCG.objects.get(id=id)
        solicitud.delete()  # Eliminar la solicitud
        return redirect('/')  # Redirigir a la página principal después de la eliminación
    except solicitudCG.DoesNotExist:
        return redirect('/')  # Si no se encuentra la solicitud, redirigir a la página principal