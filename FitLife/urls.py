"""
URL configuration for FitLife project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from primerApp import views as views1

urlpatterns = [
    path('', views1.index),
    path('registro/', views1.registrar),
    path('inicio_de_Sesion/', views1.inicioSesion),
    path('administrar/<str:rut>/', views1.ventanaAdministrador, name='ventana_administrador'),
    path('cerrar_sesion/', views1.cerrarSesion,name='cerrar_sesion'),
    path('actualizar_clase_grupal/<int:id>/', views1.actualizarCG, name='actualizarCG'),
    path('eliminar_clase_grupal/<int:id>/', views1.eliminarCG, name='eliminarCG'),
    path('actualizar_Pro/<int:id>/', views1.actualizarPro, name='actualizarPro'),
    path('eliminar_Pro/<int:id>/', views1.eliminarPro, name='eliminarPro'),
    path('actualizar_equipo/<str:rut>/', views1.actualizarEquipo, name='actualizarEquipo'),
    path('eliminar_equipo/<str:rut>/', views1.eliminarEquipo, name='eliminarEquipo'),
    path('clase_grupal/<int:id>/', views1.interfazCG, name='interfaz_CG'),
    path('administrar2/<str:rut>/', views1.ventanaAdministrador2, name='ventanaAdministrador2')
]