from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from primerApp.models import administrador, equipo, claseGrupal, producto, solicitudCG
from primerApp.forms import formAdministrador,formEquipo,formClaseGrupal, formProducto, formCG
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
    # Obtener la clase y el entrenador
    clase = claseGrupal.objects.select_related('entrenador').get(id=id)
    entrenador = clase.entrenador
    form = formCG()

    if request.method == 'POST':
        form = formCG(request.POST)
        if form.is_valid():
            # Guardamos la solicitud en la base de datos, pero no la guardamos aún
            solicitud = form.save(commit=False)
            solicitud.fechaSolicitud = timezone.now()  # Asignar la fecha y hora actual
            solicitud.save()  # Ahora sí guardamos la solicitud en la base de datos

            # Obtener el correo desde los datos del formulario
            recipient_email = form.cleaned_data['correoElectronico']

            # Enviar el correo
            subject = f'Solicitud recibida para la clase grupal {clase.nombre}'
            message = f'Hola {form.cleaned_data["nombreCompleto"]},\n\nTu solicitud para la clase grupal {clase.nombre} ha sido recibida correctamente.\n\nFecha de ingreso: {solicitud.fechaSolicitud}, Este es tu codigo para cancelar tu Solicitud en caso de algun inconveniente {solicitud.codigo}'
            from_email = settings.EMAIL_HOST_USER  # Este es el correo configurado en settings.py

            # Enviar el correo
            send_mail(
                subject,
                message,
                from_email,
                [recipient_email],  # El correo proporcionado por el usuario
                fail_silently=False,
            )

            print('Solicitud enviada correctamente y correo enviado.')
            return redirect("/")  # Redirigir a una página después de enviar el formulario
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
        
        solicitudesCG = solicitudCG.objects.all()

        data = {
            'solicitudesCG' : solicitudesCG,
            'usuario' : usuario,
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