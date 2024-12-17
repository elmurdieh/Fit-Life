from django.db import models
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from django.conf import settings
import string
import random

# Create your models here.

class administrador(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=15)
    contraseña = models.CharField(max_length=150)

class equipo(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=15, unique=True)
    rol = models.CharField(max_length=30)
    fechaIngreso = models.DateField()
    imgReferencia = models.ImageField(upload_to='static/img/equipo/',blank=True, null=True)
    bio = models.TextField()

class claseGrupal(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha_Inicio = models.DateField(default="2024-01-01")
    fecha_Fin = models.DateField(default="2024-01-01")
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    max_participantes = models.PositiveIntegerField()
    entrenador = models.ForeignKey(
        equipo, 
        on_delete=models.CASCADE, 
        related_name="clases_grupales", 
        to_field="rut"  # Usamos el campo 'rut' para la relación
    )  
    lugar = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    imgCG = models.ImageField(upload_to='static/img/clasesGrupales/',blank=True, null=True)
    archivar = models.BooleanField(default=False)
    estatus_llenado = models.BooleanField(default=False)

class solicitudCG(models.Model):
    CG = models.ForeignKey(claseGrupal, on_delete=models.CASCADE, related_name="solicitudes")
    nombreCompleto = models.CharField(max_length=512)  # Aumentar longitud por datos cifrados
    rut = models.CharField(max_length=512)
    edad = models.PositiveIntegerField()
    genero = models.CharField(max_length=1)  # "M", "F", "O"
    correoElectronico = models.CharField(max_length=512)
    telefono = models.CharField(max_length=512)
    condicionMedica = models.TextField(blank=True)
    contactoEmergenciaNombre = models.CharField(max_length=512)
    contactoEmergenciaTelefono = models.CharField(max_length=512)
    acepta_reglamento = models.BooleanField(default=False)
    acepta_uso_imagen = models.BooleanField(default=False)
    estado = models.BooleanField(default=False)  # False para "pendiente", True para "aceptada"
    fechaSolicitud = models.DateTimeField()
    codigo = models.CharField(max_length=255, unique=True, editable=False)

    def _encrypt(self, plaintext):
        cipher = AES.new(settings.AES_SECRET_KEY, AES.MODE_CBC, self._get_iv())
        ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
        return ciphertext.hex()

    def _decrypt(self, ciphertext):
        cipher = AES.new(settings.AES_SECRET_KEY, AES.MODE_CBC, self._get_iv())
        plaintext = unpad(cipher.decrypt(bytes.fromhex(ciphertext)), AES.block_size)
        return plaintext.decode('utf-8')

    def _get_iv(self):
        # Mantén un IV constante para este prototipo
        return b'1234567890123456'

    def save(self, *args, **kwargs):
        
        if not self.codigo:
            original_code = self._generate_codigo()
            self.codigo = self._encrypt(original_code)  # Cifrar el código antes de guardarlo

            self._original_code = original_code

        self.nombreCompleto = self._encrypt(self.nombreCompleto)
        self.rut = self._encrypt(self.rut)
        self.correoElectronico = self._encrypt(self.correoElectronico)
        self.telefono = self._encrypt(self.telefono)
        self.contactoEmergenciaNombre = self._encrypt(self.contactoEmergenciaNombre)
        self.contactoEmergenciaTelefono = self._encrypt(self.contactoEmergenciaTelefono)
        
        super().save(*args, **kwargs)

    def get_decrypted_data(self):
        return {
            'nombreCompleto': self._decrypt(self.nombreCompleto),
            'rut': self._decrypt(self.rut),
            'correoElectronico': self._decrypt(self.correoElectronico),
            'telefono': self._decrypt(self.telefono),
            'contactoEmergenciaNombre': self._decrypt(self.contactoEmergenciaNombre),
            'contactoEmergenciaTelefono': self._decrypt(self.contactoEmergenciaTelefono),
        }

    def _generate_codigo(self):
        characters = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choices(characters, k=8))
            if not solicitudCG.objects.filter(codigo=code).exists():
                return code


class solicitudEP(models.Model):
    pass

class cliente(models.Model):
    nombreCompleto = models.CharField(max_length=512)
    rut = models.CharField(max_length=512, unique=True)

class integra(models.Model):
    cliente = models.ForeignKey(cliente, on_delete=models.CASCADE, related_name="clases")
    clase_grupal = models.ForeignKey(claseGrupal, on_delete=models.CASCADE, related_name="participantes")
    solicitud = models.OneToOneField(solicitudCG, on_delete=models.SET_NULL, null=True, blank=True)
    estadoPago = models.BooleanField(default=False)
    fecha_union = models.DateTimeField()


class entrenamientoPersonalizado(models.Model):
    pass

class producto(models.Model):
    nombre = models.CharField(max_length=100,default='pikochu')
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(default=1)
    imgPro = models.ImageField(upload_to="static/img/productos/")
    disponible = models.BooleanField(default=1)

class seguimiento(models.Model):
    ip = models.GenericIPAddressField()
    accion = models.TextField()
    tiempo = models.DateTimeField(auto_now_add=True)

