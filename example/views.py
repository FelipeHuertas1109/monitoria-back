from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import BaseAuthentication
import jwt
from django.conf import settings
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import datetime, date
from .models import UsuarioPersonalizado, HorarioFijo, Asistencia, AjusteHoras

def calcular_horas_asistencia(asistencia):
    """
    Calcula y actualiza las horas de una asistencia basado en:
    - presente=True AND estado_autorizacion='autorizado' = 4 horas
    - Cualquier otro caso = 0 horas
    """
    if asistencia.presente and asistencia.estado_autorizacion == 'autorizado':
        asistencia.horas = 4.00
    else:
        asistencia.horas = 0.00
    return asistencia


def calcular_horas_totales_monitor(monitor_id, fecha_inicio, fecha_fin, sede=None, jornada=None):
    """
    Calcula las horas totales de un monitor incluyendo asistencias y ajustes de horas.
    Retorna diccionario con horas_asistencias, horas_ajustes, horas_totales
    """
    # Horas de asistencias
    asistencias_qs = Asistencia.objects.filter(
        usuario_id=monitor_id,
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).select_related('horario')
    
    # Aplicar filtros adicionales si se proporcionan
    if sede:
        asistencias_qs = asistencias_qs.filter(horario__sede=sede)
    if jornada:
        asistencias_qs = asistencias_qs.filter(horario__jornada=jornada)
    
    horas_asistencias = sum(float(asistencia.horas) for asistencia in asistencias_qs)
    
    # Horas de ajustes
    ajustes_qs = AjusteHoras.objects.filter(
        usuario_id=monitor_id,
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    )
    
    horas_ajustes = sum(float(ajuste.cantidad_horas) for ajuste in ajustes_qs)
    
    return {
        'horas_asistencias': horas_asistencias,
        'horas_ajustes': horas_ajustes,
        'horas_totales': horas_asistencias + horas_ajustes,
        'total_asistencias': asistencias_qs.count(),
        'total_ajustes': ajustes_qs.count()
    }
from .serializers import (
    LoginSerializer, TokenSerializer, UsuarioSerializer, UsuarioCreateSerializer,
    HorarioFijoSerializer, HorarioFijoCreateSerializer, HorarioFijoMultipleSerializer, HorarioFijoEditMultipleSerializer,
    AsistenciaSerializer, AsistenciaCreateSerializer, AjusteHorasSerializer, AjusteHorasCreateSerializer
)

# Autenticación personalizada para JWT con nuestro modelo
class UsuarioPersonalizadoJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        print(f"🔍 AUTH DEBUG - Header: {auth_header}")
        
        if not auth_header or not auth_header.startswith('Bearer '):
            print("❌ AUTH DEBUG - No Bearer token found")
            return None
        
        token = auth_header.split(' ')[1]
        print(f"🔍 AUTH DEBUG - Token: {token[:50]}...")
        
        try:
            # Decodificar token JWT
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            print(f"🔍 AUTH DEBUG - Payload: {payload}")
            
            user_id = payload.get('user_id')
            print(f"🔍 AUTH DEBUG - User ID: {user_id}")
            
            if not user_id:
                print("❌ AUTH DEBUG - No user_id in payload")
                return None
            
            # Buscar usuario personalizado
            usuario = UsuarioPersonalizado.objects.get(pk=user_id)
            print(f"✅ AUTH DEBUG - Usuario encontrado: {usuario.username} (ID: {usuario.id})")
            
            return (usuario, token)
            
        except jwt.InvalidTokenError as e:
            print(f"❌ AUTH DEBUG - JWT Error: {e}")
            return None
        except UsuarioPersonalizado.DoesNotExist as e:
            print(f"❌ AUTH DEBUG - Usuario no existe: {e}")
            return None
        except Exception as e:
            print(f"❌ AUTH DEBUG - Error general: {e}")
            return None

@api_view(['POST'])
@permission_classes([AllowAny])
def login_usuario(request):
    """
    Endpoint para autenticación de usuarios
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        nombre_usuario = serializer.validated_data['nombre_de_usuario']
        password = serializer.validated_data['password']
        
        # Buscar usuario por nombre de usuario
        try:
            usuario = UsuarioPersonalizado.objects.get(username=nombre_usuario)
        except UsuarioPersonalizado.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar contraseña
        if not usuario.check_password(password):
            return Response(
                {'error': 'Contraseña incorrecta'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generar token JWT que no expira
        refresh = RefreshToken.for_user(usuario)
        access_token = refresh.access_token
        
        # Configurar el token para que no expire
        access_token.set_exp(lifetime=None)
        
        # Crear respuesta con token y datos del usuario usando el serializer
        usuario_serializer = UsuarioSerializer(usuario)
        response_data = {
            'token': str(access_token),
            'usuario': usuario_serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def registro_usuario(request):
    """
    Endpoint para registrar nuevos usuarios.
    El tipo_usuario se asigna automáticamente como MONITOR.
    """
    serializer = UsuarioCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        # Crear el usuario
        usuario = serializer.save()
        
        # Generar token JWT automáticamente para el usuario recién creado
        refresh = RefreshToken.for_user(usuario)
        access_token = refresh.access_token
        access_token.set_exp(lifetime=None)
        
        # Serializar datos del usuario para la respuesta
        usuario_serializer = UsuarioSerializer(usuario)
        
        response_data = {
            'mensaje': 'Usuario registrado exitosamente',
            'token': str(access_token),
            'usuario': usuario_serializer.data
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_usuario_actual(request):
    """
    Endpoint para obtener información del usuario autenticado
    """
    serializer = UsuarioSerializer(request.user)
    return Response(serializer.data)

# Vistas para HorarioFijo
@api_view(['GET', 'POST'])
@authentication_classes([])  # Deshabilitar autenticación automática
@permission_classes([AllowAny])  # Permitir acceso para manejar autenticación manual
def horarios_fijos(request):
    """
    GET: Obtener horarios fijos del usuario
    POST: Crear nuevo horario fijo
    """
    # Obtener usuario desde el token JWT
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido', 'code': 'token_required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    try:
        payload = AccessToken(token)
        user_id = payload.get('user_id')
    except Exception:
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
        except Exception as e:
            return Response({'detail': f'Token inválido: {str(e)}', 'code': 'invalid_token'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        usuario = UsuarioPersonalizado.objects.get(pk=user_id)
    except UsuarioPersonalizado.DoesNotExist:
        return Response({'detail': 'User not found', 'code': 'user_not_found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        horarios = HorarioFijo.objects.filter(usuario=usuario)
        serializer = HorarioFijoSerializer(horarios, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = HorarioFijoCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(usuario=usuario)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([])  # Deshabilitar autenticación automática
@permission_classes([AllowAny])  # Permitir acceso para manejar autenticación manual
def horario_fijo_detalle(request, pk):
    """
    GET: Obtener horario fijo específico
    PUT: Actualizar horario fijo
    DELETE: Eliminar horario fijo
    """
    # Obtener usuario desde el token JWT
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido', 'code': 'token_required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    try:
        payload = AccessToken(token)
        user_id = payload.get('user_id')
    except Exception:
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
        except Exception as e:
            return Response({'detail': f'Token inválido: {str(e)}', 'code': 'invalid_token'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        usuario = UsuarioPersonalizado.objects.get(pk=user_id)
    except UsuarioPersonalizado.DoesNotExist:
        return Response({'detail': 'User not found', 'code': 'user_not_found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        horario = HorarioFijo.objects.get(pk=pk, usuario=usuario)
    except HorarioFijo.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = HorarioFijoSerializer(horario)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = HorarioFijoCreateSerializer(horario, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        horario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@authentication_classes([])  # Deshabilitar autenticación automática
@permission_classes([AllowAny])  # Cambiamos a AllowAny para manejar la autenticación manualmente
def horarios_fijos_multiple(request):
    """
    Crear múltiples horarios fijos en una sola petición
    """
    print("=== INICIO DE VISTA horarios_fijos_multiple ===")
    print(f"Método HTTP: {request.method}")
    print(f"URL: {request.path}")
    print(f"Headers completos: {dict(request.headers)}")
    print(f"Headers de autorización: {request.headers.get('Authorization', 'No presente')}")
    print(f"Content-Type: {request.headers.get('Content-Type', 'No especificado')}")
    print(f"Body de la petición: {request.body}")
    print(f"Data de la petición: {request.data}")
    
    # Verificar autenticación manualmente y obtener usuario desde el token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido', 'code': 'token_required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    try:
        payload = AccessToken(token)
        user_id = payload.get('user_id')
    except Exception:
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
        except Exception as e:
            return Response({'detail': f'Token inválido: {str(e)}', 'code': 'invalid_token'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        usuario = UsuarioPersonalizado.objects.get(pk=user_id)
    except UsuarioPersonalizado.DoesNotExist:
        return Response({'detail': 'User not found', 'code': 'user_not_found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = HorarioFijoMultipleSerializer(data=request.data)
    
    if serializer.is_valid():
        horarios_data = serializer.validated_data['horarios']
        horarios_creados = []
        errores = []
        
        for i, horario_data in enumerate(horarios_data):
            try:
                # Verificar si ya existe un horario con la misma combinación
                horario_existente = HorarioFijo.objects.filter(
                    usuario=usuario,
                    dia_semana=horario_data['dia_semana'],
                    jornada=horario_data['jornada']
                ).first()
                
                if horario_existente:
                    errores.append(f"Horario {i+1}: Ya existe un horario para {horario_existente.get_dia_semana_display()} {horario_existente.get_jornada_display()}")
                    continue
                
                # Crear el horario fijo
                horario = HorarioFijo.objects.create(
                    usuario=usuario,
                    dia_semana=horario_data['dia_semana'],
                    jornada=horario_data['jornada'],
                    sede=horario_data['sede']
                )
                
                # Serializar el horario creado
                horario_serializado = HorarioFijoSerializer(horario).data
                horarios_creados.append(horario_serializado)
                
            except Exception as e:
                errores.append(f"Horario {i+1}: Error al crear - {str(e)}")
        
        # Preparar respuesta
        response_data = {
            'mensaje': f"Se crearon {len(horarios_creados)} horarios exitosamente para {usuario.username}",
            'horarios_creados': horarios_creados,
            'total_solicitados': len(horarios_data),
            'total_creados': len(horarios_creados),
            'usuario': {
                'id': usuario.id,
                'username': usuario.username,
                'nombre': usuario.nombre
            }
        }
        
        if errores:
            response_data['errores'] = errores
            response_data['mensaje'] += f", {len(errores)} con errores"
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        
        print(f"✅ Respuesta exitosa: {response_data}")
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    print(f"❌ Errores de validación: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'POST'])  # Permitir tanto PUT como POST
@authentication_classes([])  # Deshabilitar autenticación automática
@permission_classes([AllowAny])  # Cambiamos a AllowAny para manejar la autenticación manualmente
def horarios_fijos_edit_multiple(request):
    """
    Editar múltiples horarios fijos en una sola petición
    Esta funcionalidad reemplaza TODOS los horarios existentes del usuario con los nuevos
    """
    print("=== INICIO DE VISTA horarios_fijos_edit_multiple ===")
    print(f"Método HTTP: {request.method}")
    print(f"URL: {request.path}")
    print(f"Headers completos: {dict(request.headers)}")
    print(f"Headers de autorización: {request.headers.get('Authorization', 'No presente')}")
    print(f"Content-Type: {request.headers.get('Content-Type', 'No especificado')}")
    print(f"Body de la petición: {request.body}")
    print(f"Data de la petición: {request.data}")
    
    # Verificar autenticación manualmente y obtener usuario desde el token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido', 'code': 'token_required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    try:
        payload = AccessToken(token)
        user_id = payload.get('user_id')
    except Exception:
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
        except Exception as e:
            return Response({'detail': f'Token inválido: {str(e)}', 'code': 'invalid_token'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        usuario = UsuarioPersonalizado.objects.get(pk=user_id)
    except UsuarioPersonalizado.DoesNotExist:
        return Response({'detail': 'User not found', 'code': 'user_not_found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = HorarioFijoEditMultipleSerializer(data=request.data)
    
    if serializer.is_valid():
        horarios_data = serializer.validated_data['horarios']
        
        # Eliminar todos los horarios existentes del usuario
        horarios_eliminados = HorarioFijo.objects.filter(usuario=usuario).count()
        HorarioFijo.objects.filter(usuario=usuario).delete()
        print(f"Eliminados {horarios_eliminados} horarios existentes")
        
        # Crear los nuevos horarios
        horarios_creados = []
        errores = []
        
        for i, horario_data in enumerate(horarios_data):
            try:
                # Crear el horario fijo
                horario = HorarioFijo.objects.create(
                    usuario=usuario,
                    dia_semana=horario_data['dia_semana'],
                    jornada=horario_data['jornada'],
                    sede=horario_data['sede']
                )
                
                # Serializar el horario creado
                horario_serializado = HorarioFijoSerializer(horario).data
                horarios_creados.append(horario_serializado)
                
            except Exception as e:
                errores.append(f"Horario {i+1}: Error al crear - {str(e)}")
        
        # Preparar respuesta
        response_data = {
            'mensaje': f"Se editaron los horarios exitosamente para {usuario.username}",
            'horarios_eliminados': horarios_eliminados,
            'horarios_creados': horarios_creados,
            'total_solicitados': len(horarios_data),
            'total_creados': len(horarios_creados),
            'usuario': {
                'id': usuario.id,
                'username': usuario.username,
                'nombre': usuario.nombre
            }
        }
        
        if errores:
            response_data['errores'] = errores
            response_data['mensaje'] += f", {len(errores)} con errores"
            print(f"⚠️ Respuesta con errores: {response_data}")
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        
        print(f"✅ Respuesta exitosa: {response_data}")
        return Response(response_data, status=status.HTTP_200_OK)
    
    print(f"❌ Errores de validación: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Vistas para Asistencia
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def asistencias(request):
    """
    GET: Obtener asistencias del usuario
    POST: Crear nueva asistencia
    """
    if request.method == 'GET':
        asistencias = Asistencia.objects.filter(usuario=request.user)
        serializer = AsistenciaSerializer(asistencias, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = AsistenciaCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(usuario=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def asistencia_detalle(request, pk):
    """
    GET: Obtener asistencia específica
    PUT: Actualizar asistencia
    DELETE: Eliminar asistencia
    """
    try:
        asistencia = Asistencia.objects.get(pk=pk, usuario=request.user)
    except Asistencia.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = AsistenciaSerializer(asistencia)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = AsistenciaCreateSerializer(asistencia, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        asistencia.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# ===== Endpoints para DIRECTIVOS =====

def _parse_fecha(fecha_str: str | None) -> date:
    if not fecha_str:
        return date.today()
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except Exception:
        return date.today()

def _dia_semana_de_fecha(fecha_obj: date) -> int:
    # Python: Monday=0 ... Sunday=6; coincide con nuestro enum
    return fecha_obj.weekday()

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_horarios_monitores(request):
    """
    Listar todos los horarios fijos de todos los monitores.
    Filtros opcionales: usuario_id, dia_semana, jornada, sede
    Acceso: solo DIRECTIVO
    """
    # Autenticación manual
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido'}, status=status.HTTP_401_UNAUTHORIZED)

    # Usuario DIRECTIVO temporal
    usuario_directivo = UsuarioPersonalizado.objects.filter(tipo_usuario='DIRECTIVO').first()
    if not usuario_directivo:
        return Response({'detail': 'No hay usuarios DIRECTIVO'}, status=status.HTTP_403_FORBIDDEN)

    # Parámetros de filtrado
    usuario_id = request.query_params.get('usuario_id')  # ID específico de monitor
    dia_semana = request.query_params.get('dia_semana')  # 0-6
    jornada = request.query_params.get('jornada')  # M|T
    sede = request.query_params.get('sede')  # SA|BA

    # Query base: solo horarios de monitores
    horarios_qs = HorarioFijo.objects.filter(usuario__tipo_usuario='MONITOR')
    
    # Aplicar filtros
    if usuario_id:
        try:
            usuario_id = int(usuario_id)
            horarios_qs = horarios_qs.filter(usuario__id=usuario_id)
        except ValueError:
            return Response({'detail': 'usuario_id debe ser un número entero'}, status=status.HTTP_400_BAD_REQUEST)
    
    if dia_semana is not None:
        try:
            dia_semana = int(dia_semana)
            if dia_semana < 0 or dia_semana > 6:
                return Response({'detail': 'dia_semana debe ser entre 0-6'}, status=status.HTTP_400_BAD_REQUEST)
            horarios_qs = horarios_qs.filter(dia_semana=dia_semana)
        except ValueError:
            return Response({'detail': 'dia_semana debe ser un número entero'}, status=status.HTTP_400_BAD_REQUEST)
    
    if jornada:
        if jornada not in ['M', 'T']:
            return Response({'detail': 'jornada debe ser M o T'}, status=status.HTTP_400_BAD_REQUEST)
        horarios_qs = horarios_qs.filter(jornada=jornada)
    
    if sede:
        if sede not in ['SA', 'BA']:
            return Response({'detail': 'sede debe ser SA o BA'}, status=status.HTTP_400_BAD_REQUEST)
        horarios_qs = horarios_qs.filter(sede=sede)

    # Ordenar por usuario, día y jornada para mejor presentación
    horarios_qs = horarios_qs.order_by('usuario__nombre', 'dia_semana', 'jornada')
    
    # Serializar y responder
    serializer = HorarioFijoSerializer(horarios_qs.select_related('usuario'), many=True)
    
    # Agregar información de conteo
    response_data = {
        'total_horarios': horarios_qs.count(),
        'total_monitores': horarios_qs.values('usuario').distinct().count(),
        'horarios': serializer.data
    }
    
    return Response(response_data)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_asistencias(request):
    """
    Listar asistencias del día (por defecto hoy) para todos los monitores
    con HorarioFijo del día de la semana. Genera en demanda las asistencias faltantes.
    Filtros: fecha, estado, jornada, sede
    Acceso: solo DIRECTIVO (temporal: usamos el primer DIRECTIVO hasta integrar JWT)
    """
    # Autenticación manual
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido'}, status=status.HTTP_401_UNAUTHORIZED)

    # Usuario DIRECTIVO temporal
    usuario_directivo = UsuarioPersonalizado.objects.filter(tipo_usuario='DIRECTIVO').first()
    if not usuario_directivo:
        return Response({'detail': 'No hay usuarios DIRECTIVO'}, status=status.HTTP_403_FORBIDDEN)

    # Parámetros
    fecha_str = request.query_params.get('fecha')
    estado = request.query_params.get('estado')  # pendiente|autorizado|rechazado
    jornada = request.query_params.get('jornada')  # M|T
    sede = request.query_params.get('sede')  # SA|BA

    fecha_obj = _parse_fecha(fecha_str)
    dia_semana = _dia_semana_de_fecha(fecha_obj)

    # Horarios del día
    horarios_qs = HorarioFijo.objects.filter(dia_semana=dia_semana)
    if jornada:
        horarios_qs = horarios_qs.filter(jornada=jornada)
    if sede:
        horarios_qs = horarios_qs.filter(sede=sede)

    # Generar asistencias si faltan
    for h in horarios_qs:
        Asistencia.objects.get_or_create(
            usuario=h.usuario,
            fecha=fecha_obj,
            horario=h,
            defaults={
                'presente': False,
                'estado_autorizacion': 'pendiente',
                'horas': 0.00
            }
        )

    asistencias_qs = Asistencia.objects.filter(fecha=fecha_obj, horario__in=horarios_qs)
    if estado:
        asistencias_qs = asistencias_qs.filter(estado_autorizacion=estado)

    serializer = AsistenciaSerializer(asistencias_qs.select_related('usuario', 'horario'), many=True)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_autorizar_asistencia(request, pk):
    # Auth manual y rol DIRECTIVO
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido'}, status=status.HTTP_401_UNAUTHORIZED)
    usuario_directivo = UsuarioPersonalizado.objects.filter(tipo_usuario='DIRECTIVO').first()
    if not usuario_directivo:
        return Response({'detail': 'No hay usuarios DIRECTIVO'}, status=status.HTTP_403_FORBIDDEN)

    try:
        asistencia = Asistencia.objects.get(pk=pk)
    except Asistencia.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    asistencia.estado_autorizacion = 'autorizado'
    calcular_horas_asistencia(asistencia)
    asistencia.save()
    return Response(AsistenciaSerializer(asistencia).data)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_rechazar_asistencia(request, pk):
    # Auth manual y rol DIRECTIVO
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido'}, status=status.HTTP_401_UNAUTHORIZED)
    usuario_directivo = UsuarioPersonalizado.objects.filter(tipo_usuario='DIRECTIVO').first()
    if not usuario_directivo:
        return Response({'detail': 'No hay usuarios DIRECTIVO'}, status=status.HTTP_403_FORBIDDEN)

    try:
        asistencia = Asistencia.objects.get(pk=pk)
    except Asistencia.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    asistencia.estado_autorizacion = 'rechazado'
    calcular_horas_asistencia(asistencia)
    asistencia.save()
    return Response(AsistenciaSerializer(asistencia).data)

# ===== Endpoints para REPORTES =====

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_reporte_horas_monitor(request, monitor_id):
    """
    Reporte de horas trabajadas por un monitor específico.
    Filtros: fecha_inicio, fecha_fin, sede, jornada
    Acceso: solo DIRECTIVO
    """
    # Autenticación manual
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido'}, status=status.HTTP_401_UNAUTHORIZED)

    # Usuario DIRECTIVO temporal
    usuario_directivo = UsuarioPersonalizado.objects.filter(tipo_usuario='DIRECTIVO').first()
    if not usuario_directivo:
        return Response({'detail': 'No hay usuarios DIRECTIVO'}, status=status.HTTP_403_FORBIDDEN)

    # Verificar que el monitor existe
    try:
        monitor = UsuarioPersonalizado.objects.get(id=monitor_id, tipo_usuario='MONITOR')
    except UsuarioPersonalizado.DoesNotExist:
        return Response({'detail': 'Monitor no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # Parámetros de filtrado
    fecha_inicio_str = request.query_params.get('fecha_inicio')
    fecha_fin_str = request.query_params.get('fecha_fin')
    sede = request.query_params.get('sede')  # SA|BA
    jornada = request.query_params.get('jornada')  # M|T

    # Fechas por defecto: último mes
    if not fecha_inicio_str:
        from datetime import date, timedelta
        fecha_inicio = date.today() - timedelta(days=30)
    else:
        fecha_inicio = _parse_fecha(fecha_inicio_str)
    
    if not fecha_fin_str:
        fecha_fin = date.today()
    else:
        fecha_fin = _parse_fecha(fecha_fin_str)

    # Validar filtros
    if sede and sede not in ['SA', 'BA']:
        return Response({'detail': 'sede debe ser SA o BA'}, status=status.HTTP_400_BAD_REQUEST)
    if jornada and jornada not in ['M', 'T']:
        return Response({'detail': 'jornada debe ser M o T'}, status=status.HTTP_400_BAD_REQUEST)

    # Calcular horas totales incluyendo ajustes
    calculo_horas = calcular_horas_totales_monitor(monitor_id, fecha_inicio, fecha_fin, sede, jornada)

    # Query asistencias para el detalle
    asistencias_qs = Asistencia.objects.filter(
        usuario=monitor,
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).select_related('horario')

    # Aplicar filtros adicionales para asistencias
    if sede:
        asistencias_qs = asistencias_qs.filter(horario__sede=sede)
    if jornada:
        asistencias_qs = asistencias_qs.filter(horario__jornada=jornada)

    # Estadísticas de asistencias
    asistencias_presentes = asistencias_qs.filter(presente=True).count()
    asistencias_autorizadas = asistencias_qs.filter(estado_autorizacion='autorizado').count()
    
    # Agrupar asistencias por fecha para el detalle
    asistencias_por_fecha = {}
    for asistencia in asistencias_qs.order_by('fecha', 'horario__jornada'):
        fecha_str = asistencia.fecha.strftime('%Y-%m-%d')
        if fecha_str not in asistencias_por_fecha:
            asistencias_por_fecha[fecha_str] = []
        asistencias_por_fecha[fecha_str].append(AsistenciaSerializer(asistencia).data)

    # Query ajustes para el detalle
    ajustes_qs = AjusteHoras.objects.filter(
        usuario=monitor,
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).select_related('creado_por', 'asistencia')

    # Agrupar ajustes por fecha
    ajustes_por_fecha = {}
    for ajuste in ajustes_qs.order_by('fecha', 'created_at'):
        fecha_str = ajuste.fecha.strftime('%Y-%m-%d')
        if fecha_str not in ajustes_por_fecha:
            ajustes_por_fecha[fecha_str] = []
        ajustes_por_fecha[fecha_str].append(AjusteHorasSerializer(ajuste).data)

    # Respuesta
    response_data = {
        'monitor': {
            'id': monitor.id,
            'username': monitor.username,
            'nombre': monitor.nombre
        },
        'periodo': {
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin.strftime('%Y-%m-%d')
        },
        'estadisticas': {
            'horas_asistencias': round(calculo_horas['horas_asistencias'], 2),
            'horas_ajustes': round(calculo_horas['horas_ajustes'], 2),
            'total_horas': round(calculo_horas['horas_totales'], 2),
            'total_asistencias': calculo_horas['total_asistencias'],
            'total_ajustes': calculo_horas['total_ajustes'],
            'asistencias_presentes': asistencias_presentes,
            'asistencias_autorizadas': asistencias_autorizadas,
            'promedio_horas_por_dia': round(calculo_horas['horas_totales'] / max(1, (fecha_fin - fecha_inicio).days + 1), 2)
        },
        'filtros_aplicados': {
            'sede': sede,
            'jornada': jornada
        },
        'detalle_por_fecha': asistencias_por_fecha,
        'ajustes_por_fecha': ajustes_por_fecha
    }

    return Response(response_data)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_reporte_horas_todos(request):
    """
    Reporte de horas trabajadas por todos los monitores.
    Filtros: fecha_inicio, fecha_fin, sede, jornada
    Acceso: solo DIRECTIVO
    """
    # Autenticación manual
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido'}, status=status.HTTP_401_UNAUTHORIZED)

    # Usuario DIRECTIVO temporal
    usuario_directivo = UsuarioPersonalizado.objects.filter(tipo_usuario='DIRECTIVO').first()
    if not usuario_directivo:
        return Response({'detail': 'No hay usuarios DIRECTIVO'}, status=status.HTTP_403_FORBIDDEN)

    # Parámetros de filtrado
    fecha_inicio_str = request.query_params.get('fecha_inicio')
    fecha_fin_str = request.query_params.get('fecha_fin')
    sede = request.query_params.get('sede')  # SA|BA
    jornada = request.query_params.get('jornada')  # M|T

    # Fechas por defecto: último mes
    if not fecha_inicio_str:
        from datetime import date, timedelta
        fecha_inicio = date.today() - timedelta(days=30)
    else:
        fecha_inicio = _parse_fecha(fecha_inicio_str)
    
    if not fecha_fin_str:
        fecha_fin = date.today()
    else:
        fecha_fin = _parse_fecha(fecha_fin_str)

    # Validar filtros
    if sede and sede not in ['SA', 'BA']:
        return Response({'detail': 'sede debe ser SA o BA'}, status=status.HTTP_400_BAD_REQUEST)
    if jornada and jornada not in ['M', 'T']:
        return Response({'detail': 'jornada debe ser M o T'}, status=status.HTTP_400_BAD_REQUEST)

    # Obtener todos los monitores
    monitores = UsuarioPersonalizado.objects.filter(tipo_usuario='MONITOR')
    
    # Calcular datos para cada monitor
    monitores_data = {}
    total_horas_general = 0.0
    total_asistencias_general = 0
    total_ajustes_general = 0
    
    for monitor in monitores:
        # Calcular horas totales incluyendo ajustes
        calculo_horas = calcular_horas_totales_monitor(monitor.id, fecha_inicio, fecha_fin, sede, jornada)
        
        # Solo incluir monitores que tienen datos en el período
        if calculo_horas['total_asistencias'] > 0 or calculo_horas['total_ajustes'] > 0:
            # Query asistencias para el detalle
            asistencias_qs = Asistencia.objects.filter(
                usuario=monitor,
                fecha__gte=fecha_inicio,
                fecha__lte=fecha_fin
            ).select_related('horario')

            # Aplicar filtros a asistencias
            if sede:
                asistencias_qs = asistencias_qs.filter(horario__sede=sede)
            if jornada:
                asistencias_qs = asistencias_qs.filter(horario__jornada=jornada)

            asistencias_presentes = asistencias_qs.filter(presente=True).count()
            asistencias_autorizadas = asistencias_qs.filter(estado_autorizacion='autorizado').count()

            # Query ajustes para el detalle
            ajustes_qs = AjusteHoras.objects.filter(
                usuario=monitor,
                fecha__gte=fecha_inicio,
                fecha__lte=fecha_fin
            ).select_related('creado_por', 'asistencia')

            monitores_data[monitor.id] = {
                'monitor': {
                    'id': monitor.id,
                    'username': monitor.username,
                    'nombre': monitor.nombre
                },
                'horas_asistencias': round(calculo_horas['horas_asistencias'], 2),
                'horas_ajustes': round(calculo_horas['horas_ajustes'], 2),
                'total_horas': round(calculo_horas['horas_totales'], 2),
                'total_asistencias': calculo_horas['total_asistencias'],
                'total_ajustes': calculo_horas['total_ajustes'],
                'asistencias_presentes': asistencias_presentes,
                'asistencias_autorizadas': asistencias_autorizadas,
                'asistencias': [AsistenciaSerializer(a).data for a in asistencias_qs],
                'ajustes': [AjusteHorasSerializer(aj).data for aj in ajustes_qs]
            }
            
            # Acumular estadísticas generales
            total_horas_general += calculo_horas['horas_totales']
            total_asistencias_general += calculo_horas['total_asistencias']
            total_ajustes_general += calculo_horas['total_ajustes']

    total_monitores = len(monitores_data)

    # Ordenar monitores por horas trabajadas (descendente)
    monitores_ordenados = sorted(
        monitores_data.values(),
        key=lambda x: x['total_horas'],
        reverse=True
    )

    # Respuesta
    response_data = {
        'periodo': {
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin.strftime('%Y-%m-%d')
        },
        'estadisticas_generales': {
            'total_horas': round(total_horas_general, 2),
            'total_asistencias': total_asistencias_general,
            'total_ajustes': total_ajustes_general,
            'total_monitores': total_monitores,
            'promedio_horas_por_monitor': round(total_horas_general / max(1, total_monitores), 2)
        },
        'filtros_aplicados': {
            'sede': sede,
            'jornada': jornada
        },
        'monitores': monitores_ordenados
    }

    return Response(response_data)

# ===== Endpoints para MONITORES =====

@api_view(['GET'])
@authentication_classes([UsuarioPersonalizadoJWTAuthentication])
@permission_classes([IsAuthenticated])
def monitor_mis_asistencias(request):
    """
    Lista (y genera si faltan) las asistencias del usuario MONITOR para la fecha (por defecto hoy)
    """
    usuario = request.user
    print(f"=== MONITOR MIS ASISTENCIAS - Usuario autenticado: {usuario.username} (ID: {usuario.id}) ===")
    
    if usuario.tipo_usuario != 'MONITOR':
        return Response({'detail': 'Solo monitores pueden acceder a este endpoint'}, status=status.HTTP_403_FORBIDDEN)

    fecha_obj = _parse_fecha(request.query_params.get('fecha'))
    dia_semana = _dia_semana_de_fecha(fecha_obj)

    horarios_qs = HorarioFijo.objects.filter(usuario=usuario, dia_semana=dia_semana)

    # Generar asistencias si faltan
    for h in horarios_qs:
        Asistencia.objects.get_or_create(
            usuario=usuario,
            fecha=fecha_obj,
            horario=h,
            defaults={'presente': False, 'estado_autorizacion': 'pendiente', 'horas': 0.00}
        )

    asistencias_qs = Asistencia.objects.filter(usuario=usuario, fecha=fecha_obj)
    serializer = AsistenciaSerializer(asistencias_qs.select_related('usuario', 'horario'), many=True)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([UsuarioPersonalizadoJWTAuthentication])
@permission_classes([IsAuthenticated])
def monitor_marcar(request):
    """
    Body: { "fecha": "YYYY-MM-DD", "jornada": "M|T" }
    Marca presente=True en la asistencia del bloque correspondiente si el usuario tiene HorarioFijo.
    """
    usuario = request.user
    print(f"=== MONITOR MARCAR - Usuario autenticado: {usuario.username} (ID: {usuario.id}) ===")
    
    if usuario.tipo_usuario != 'MONITOR':
        return Response({'detail': 'Solo monitores pueden marcar asistencia'}, status=status.HTTP_403_FORBIDDEN)

    fecha_obj = _parse_fecha(request.data.get('fecha'))
    jornada = request.data.get('jornada')
    if jornada not in ['M', 'T']:
        return Response({'detail': 'Jornada inválida'}, status=status.HTTP_400_BAD_REQUEST)

    dia_semana = _dia_semana_de_fecha(fecha_obj)
    try:
        horario = HorarioFijo.objects.get(usuario=usuario, dia_semana=dia_semana, jornada=jornada)
    except HorarioFijo.DoesNotExist:
        return Response({'detail': 'No tienes horario asignado para esa jornada hoy'}, status=status.HTTP_400_BAD_REQUEST)

    asistencia, _ = Asistencia.objects.get_or_create(
        usuario=usuario,
        fecha=fecha_obj,
        horario=horario,
        defaults={'presente': False, 'estado_autorizacion': 'pendiente', 'horas': 0.00}
    )

    # Solo permite marcar si el bloque fue autorizado por un DIRECTIVO
    if asistencia.estado_autorizacion != 'autorizado':
        return Response(
            {
                'detail': 'Este bloque aún no ha sido autorizado por un directivo.',
                'code': 'not_authorized'
            },
            status=status.HTTP_403_FORBIDDEN
        )

    asistencia.presente = True
    calcular_horas_asistencia(asistencia)
    asistencia.save()

    return Response(AsistenciaSerializer(asistencia).data)


# ===== Endpoints para AJUSTES DE HORAS =====

@api_view(['GET', 'POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_ajustes_horas(request):
    """
    GET: Listar ajustes de horas con filtros opcionales
    POST: Crear nuevo ajuste de horas
    Acceso: solo DIRECTIVO
    """
    # Autenticación manual
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido'}, status=status.HTTP_401_UNAUTHORIZED)

    # Usuario DIRECTIVO temporal
    usuario_directivo = UsuarioPersonalizado.objects.filter(tipo_usuario='DIRECTIVO').first()
    if not usuario_directivo:
        return Response({'detail': 'No hay usuarios DIRECTIVO'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Parámetros de filtrado
        monitor_id = request.query_params.get('monitor_id')
        fecha_inicio_str = request.query_params.get('fecha_inicio')
        fecha_fin_str = request.query_params.get('fecha_fin')
        
        # Query base
        ajustes_qs = AjusteHoras.objects.all().select_related('usuario', 'creado_por', 'asistencia')
        
        # Aplicar filtros
        if monitor_id:
            try:
                monitor_id = int(monitor_id)
                ajustes_qs = ajustes_qs.filter(usuario__id=monitor_id)
            except ValueError:
                return Response({'detail': 'monitor_id debe ser un número entero'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Fechas por defecto: último mes
        if not fecha_inicio_str:
            from datetime import date, timedelta
            fecha_inicio = date.today() - timedelta(days=30)
        else:
            fecha_inicio = _parse_fecha(fecha_inicio_str)
        
        if not fecha_fin_str:
            fecha_fin = date.today()
        else:
            fecha_fin = _parse_fecha(fecha_fin_str)
        
        # Filtrar por rango de fechas
        ajustes_qs = ajustes_qs.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
        
        # Serializar y responder
        serializer = AjusteHorasSerializer(ajustes_qs, many=True)
        
        # Calcular estadísticas
        total_ajustes = ajustes_qs.count()
        total_horas_ajustadas = sum(float(ajuste.cantidad_horas) for ajuste in ajustes_qs)
        monitores_afectados = ajustes_qs.values('usuario').distinct().count()
        
        response_data = {
            'periodo': {
                'fecha_inicio': str(fecha_inicio),
                'fecha_fin': str(fecha_fin)
            },
            'estadisticas': {
                'total_ajustes': total_ajustes,
                'total_horas_ajustadas': total_horas_ajustadas,
                'monitores_afectados': monitores_afectados
            },
            'filtros_aplicados': {
                'monitor_id': monitor_id
            },
            'ajustes': serializer.data
        }
        
        return Response(response_data)
    
    elif request.method == 'POST':
        serializer = AjusteHorasCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Obtener instancias
            monitor = UsuarioPersonalizado.objects.get(id=serializer.validated_data['monitor_id'])
            asistencia = None
            if serializer.validated_data.get('asistencia_id'):
                asistencia = Asistencia.objects.get(id=serializer.validated_data['asistencia_id'])
            
            # Crear ajuste
            ajuste = AjusteHoras.objects.create(
                usuario=monitor,
                fecha=serializer.validated_data['fecha'],
                cantidad_horas=serializer.validated_data['cantidad_horas'],
                motivo=serializer.validated_data['motivo'],
                asistencia=asistencia,
                creado_por=usuario_directivo
            )
            
            return Response(AjusteHorasSerializer(ajuste).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_ajuste_horas_detalle(request, pk):
    """
    GET: Obtener detalles de un ajuste específico
    DELETE: Eliminar ajuste de horas
    Acceso: solo DIRECTIVO
    """
    # Autenticación manual
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'detail': 'Token de autenticación requerido'}, status=status.HTTP_401_UNAUTHORIZED)

    # Usuario DIRECTIVO temporal
    usuario_directivo = UsuarioPersonalizado.objects.filter(tipo_usuario='DIRECTIVO').first()
    if not usuario_directivo:
        return Response({'detail': 'No hay usuarios DIRECTIVO'}, status=status.HTTP_403_FORBIDDEN)

    # Verificar que el ajuste existe
    try:
        ajuste = AjusteHoras.objects.select_related('usuario', 'creado_por', 'asistencia').get(id=pk)
    except AjusteHoras.DoesNotExist:
        return Response({'detail': 'Ajuste de horas no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AjusteHorasSerializer(ajuste)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        ajuste.delete()
        return Response({'detail': 'Ajuste de horas eliminado exitosamente'}, status=status.HTTP_204_NO_CONTENT)