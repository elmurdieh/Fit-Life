from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from primerApp.models import administrador, equipo, claseGrupal,seguimiento, producto, solicitudCG, cliente, integra
from primerApp.forms import formAdministrador,formEquipo,formClaseGrupal, formProducto, formCG, integraForm
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache


def registrar_seguimiento(ip, accion):
    seguimiento.objects.create(
        ip=ip,
        accion=accion,
        tiempo=now()
    )

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

            # Recalcular los participantes después de agregar un nuevo integrante
            participantes_actuales = integra.objects.filter(clase_grupal=clase).count()
            if participantes_actuales >= clase.max_participantes:
                clase.estatus_llenado = True
                clase.save()

            recipient_email = form.cleaned_data['correoElectronico']
            subject = f'Solicitud recibida para la clase grupal {clase.nombre}'
            message = f'Hola {form.cleaned_data["nombreCompleto"]},\n\nTu solicitud para la clase grupal {clase.nombre} ha sido recibida correctamente.\n\nFecha de ingreso: {solicitud.fechaSolicitud}.\n\nEste es tu código para cancelar tu Solicitud en caso de algún inconveniente: {solicitud.codigo}'
            from_email = settings.EMAIL_HOST_USER
            send_mail(subject, message, from_email, [recipient_email], fail_silently=False)

            # Redirigir a la misma página después de la inscripción
            return redirect(f"/clase_grupal/{clase.id}/")
        else:
            print("Error al enviar la solicitud")
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
    blocked = False  # Inicializamos la variable blocked como False

    if request.method == 'POST':
        if 'rut' in request.POST and 'contraseña' in request.POST:
            rut = request.POST['rut']
            contraseña = request.POST['contraseña']

            # Limitar intentos por IP
            client_ip = get_client_ip(request)  # Obtener la IP del cliente
            key = f"login_attempts:{client_ip}"
            attempts = cache.get(key, 0)

            if attempts >= 3:
                blocked = True  # Bloqueamos la interfaz si supera el límite
                registrar_seguimiento(client_ip, "Bloqueo por múltiples intentos fallidos de inicio de sesión")
                messages.error(request, 'Demasiados intentos fallidos. Intente de nuevo más tarde.')
            else:
                try:
                    usuario = administrador.objects.get(rut=rut)
                    if check_password(contraseña, usuario.contraseña):
                        # Restablecer intentos al iniciar sesión con éxito
                        cache.delete(key)
                        request.session['usuario_id'] = usuario.id
                        registrar_seguimiento(client_ip, f"Inicio de sesión exitoso para el usuario {rut}")
                        return redirect(f'/administrar/{usuario.rut}/')
                    else:
                        # Incrementar intentos fallidos
                        cache.set(key, attempts + 1, timeout=300)  # Bloquear por 5 minutos después de 3 intentos
                        registrar_seguimiento(client_ip, f"Intento fallido de inicio de sesión para el usuario {rut}")
                        messages.error(request, 'Contraseña incorrecta')
                except administrador.DoesNotExist:
                    # Incrementar intentos fallidos
                    cache.set(key, attempts + 1, timeout=300)
                    registrar_seguimiento(client_ip, f"Intento fallido: usuario {rut} no registrado")
                    messages.error(request, 'El RUT ingresado no está registrado')
        else:
            messages.error(request, 'Complete ambos campos')

    return render(request, 'primerApp/inicioSesion.html', {'blocked': blocked})




def get_client_ip(request):
    """Obtener la dirección IP del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

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

def ventanaAdministrador2(request, rut):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')
    
    try:
        usuario = administrador.objects.get(rut=rut)
        if request.session.get('usuario_id') != usuario.id:
            return redirect('/inicio_de_Sesion/')
        
        # Obtener y descifrar solicitudes
        solicitudesCG = solicitudCG.objects.filter(estado=False).select_related('CG')
        solicitudes_procesadas = []
        for solicitud in solicitudesCG:
            solicitudes_procesadas.append({
                'id': solicitud.id,
                'nombreCompleto': solicitud._decrypt(solicitud.nombreCompleto),
                'rut': solicitud._decrypt(solicitud.rut),
                'correoElectronico': solicitud._decrypt(solicitud.correoElectronico),
                'telefono': solicitud._decrypt(solicitud.telefono),
                'contactoEmergenciaNombre': solicitud._decrypt(solicitud.contactoEmergenciaNombre),
                'contactoEmergenciaTelefono': solicitud._decrypt(solicitud.contactoEmergenciaTelefono),
                'CG': solicitud.CG,
                'fechaSolicitud': solicitud.fechaSolicitud
            })

        data = {
            'solicitudesCG': solicitudes_procesadas,
            'usuario': usuario,
            'clasesGrupales': claseGrupal.objects.all(),
        }

    except administrador.DoesNotExist:
        print("Usuario no encontrado.")
        return redirect('/inicio_de_Sesion/')

    return render(request, 'primerApp/administradorVentana2.html', data)


def verClaseGrupal(request, id, rut):
    if not request.session.get('usuario_id'):
        return redirect('/inicio_de_Sesion/')

    try:
        usuario = administrador.objects.get(rut=rut)
        if request.session.get('usuario_id') != usuario.id:
            return redirect('/inicio_de_Sesion/')

        claseG = claseGrupal.objects.select_related('entrenador').get(id=id)
        integrantes = integra.objects.filter(clase_grupal=claseG).select_related('solicitud')

        integrantes_procesados = []
        for integrante in integrantes:
            solicitud = integrante.solicitud
            datos_solicitud = solicitud.get_decrypted_data()
            integrantes_procesados.append({
                'id': integrante.id,
                'nombreCompleto': datos_solicitud.get('nombreCompleto', 'N/A'),
                'rut': datos_solicitud.get('rut', 'N/A'),
                'estadoPago': integrante.estadoPago,
                'contactoEmergenciaTelefono': datos_solicitud.get('contactoEmergenciaTelefono', 'N/A'),
                'fecha_union': integrante.fecha_union,
            })

        data = {
            'integrantes': integrantes_procesados,
            'usuario': usuario,
            'clasesGrupales': claseG,
        }

    except administrador.DoesNotExist:
        print("Usuario no encontrado.")
        return redirect('/inicio_de_Sesion/')
    except claseGrupal.DoesNotExist:
        print("Clase no encontrada.")
        return redirect('/administrar2/')

    return render(request, 'primerApp/verEstadoCG.html', data)


    

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

        # Desencriptar los datos necesarios
        decrypted_data = solicitud.get_decrypted_data()

        # Marcar la solicitud como aprobada
        solicitud.estado = True
        solicitud.save()

        # Crear cliente con los datos desencriptados
        cliente_creado = cliente.objects.create(
            nombreCompleto=decrypted_data['nombreCompleto'],
            rut=decrypted_data['rut']
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

        # Enviar correo de aprobación con datos desencriptados
        recipient_email = decrypted_data['correoElectronico']
        subject = '¡Solicitud Aprobada!'
        message = (
            f'Hola {decrypted_data["nombreCompleto"]},\n\n'
            f'Tu solicitud para la clase grupal "{solicitud.CG.nombre}" ha sido aprobada.\n\n'
            f'Ahora podrás pagar, ya sea de forma presencial en el establecimiento o ir a nuestro banco en línea:\n\n'
            f'{enlace}\n\n'
            f'Te esperamos en la fecha y hora acordada. ¡Gracias por elegirnos!\n\n'
            f'- Equipo FitLife'
        )
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


def cancelarReserva(request, codigo):
    try:
        solicitud = solicitudCG.objects.get(codigo=codigo)
        if solicitud.verificar_codigo(codigo):
            solicitud.delete()
            return redirect("/")
    except solicitudCG.DoesNotExist:
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

            # Confirmar el cambio en la consola
            print(f"Estado de pago actualizado para la integración ID {integra_obj.id}: {integra_obj.estadoPago}")

            # Enviar correo de confirmación de pago
            cliente_email = solicitud.correoElectronico
            clase_nombre = solicitud.CG.nombre
            subject = 'Confirmación de pago exitoso'
            message = (f'Hola {solicitud.nombreCompleto},\n\n'
                       f'Te confirmamos que el pago para la clase grupal "{clase_nombre}" ha sido realizado con éxito.\n\n'
                       f'Te esperamos en la fecha acordada. ¡Gracias por confiar en nosotros!\n\n'
                       f'- Equipo FitLife')
            from_email = settings.EMAIL_HOST_USER

            try:
                send_mail(
                    subject,
                    message,
                    from_email,
                    [cliente_email],
                    fail_silently=False,
                )
                print('Correo de confirmación de pago enviado correctamente.')
            except Exception as e:
                print(f'Error al enviar el correo de confirmación de pago: {e}')

            # Agregar mensaje de éxito para la interfaz
            messages.success(request, 'Pago Realizado Correctamente. Revisa tu correo para más detalles.')

            # Redirigir al usuario a la página principal
            return redirect("/")
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

        # Obtener datos del cliente para el correo
        cliente_email = solicitud.correoElectronico
        clase_nombre = solicitud.CG.nombre

        # Eliminar la solicitud
        solicitud.delete()

        # Enviar correo de confirmación
        subject = 'Cancelación de servicio confirmada'
        message = (f'Hola {solicitud.nombreCompleto},\n\n'
                   f'Te confirmamos que tu solicitud para la clase grupal "{clase_nombre}" ha sido cancelada exitosamente.\n\n'
                   f'Si tienes alguna pregunta o necesitas asistencia, no dudes en contactarnos.\n\n'
                   f'- Equipo FitLife')
        from_email = settings.EMAIL_HOST_USER

        try:
            send_mail(
                subject,
                message,
                from_email,
                [cliente_email],
                fail_silently=False,
            )
            print('Correo de cancelación enviado correctamente.')
        except Exception as e:
            print(f'Error al enviar el correo de cancelación: {e}')

        return redirect('/') 
    except solicitudCG.DoesNotExist:
        return redirect('/')

def error_404(request, exception):
    return render(request, 'primerApp/404.html', status=404)

def error_500(request):
    return render(request, 'primerApp/500.html', status=500)
