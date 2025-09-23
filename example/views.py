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
from .models import UsuarioPersonalizado, HorarioFijo, Asistencia, AjusteHoras, ConfiguracionSistema

def calcular_horas_asistencia(asistencia):
    """
    Calcula y actualiza las horas de una asistencia basado en:
    - presente=True AND (estado_autorizacion='autorizado' OR estado_autorizacion='recuperado') = 4 horas
    - Cualquier otro caso = 0 horas
    """
    if asistencia.presente and asistencia.estado_autorizacion in ['autorizado', 'recuperado']:
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
    AsistenciaSerializer, AsistenciaCreateSerializer, AjusteHorasSerializer, AjusteHorasCreateSerializer,
    ConfiguracionSistemaSerializer, ConfiguracionSistemaCreateSerializer
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
    estado = request.query_params.get('estado')  # pendiente|autorizado|rechazado|recuperado
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

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_asistencias_recuperables(request):
    """
    Listar asistencias que están pendientes y pueden ser recuperadas (fechas pasadas).
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
    monitor_id = request.query_params.get('monitor_id')
    jornada = request.query_params.get('jornada')  # M|T
    sede = request.query_params.get('sede')  # SA|BA

    # Fechas por defecto: últimos 30 días
    from datetime import date, timedelta
    if not fecha_inicio_str:
        fecha_inicio = date.today() - timedelta(days=30)
    else:
        fecha_inicio = _parse_fecha(fecha_inicio_str)
    
    if not fecha_fin_str:
        fecha_fin = date.today() - timedelta(days=1)  # Solo fechas pasadas
    else:
        fecha_fin = _parse_fecha(fecha_fin_str)

    # Validar filtros
    if jornada and jornada not in ['M', 'T']:
        return Response({'detail': 'jornada debe ser M o T'}, status=status.HTTP_400_BAD_REQUEST)
    if sede and sede not in ['SA', 'BA']:
        return Response({'detail': 'sede debe ser SA o BA'}, status=status.HTTP_400_BAD_REQUEST)

    # Query: asistencias pendientes en fechas pasadas
    asistencias_qs = Asistencia.objects.filter(
        estado_autorizacion='pendiente',
        fecha__gte=fecha_inicio,
        fecha__lt=date.today()  # Solo fechas pasadas
    ).select_related('usuario', 'horario')

    # Aplicar filtros adicionales
    if monitor_id:
        try:
            monitor_id = int(monitor_id)
            asistencias_qs = asistencias_qs.filter(usuario__id=monitor_id)
        except ValueError:
            return Response({'detail': 'monitor_id debe ser un número entero'}, status=status.HTTP_400_BAD_REQUEST)
    
    if jornada:
        asistencias_qs = asistencias_qs.filter(horario__jornada=jornada)
    if sede:
        asistencias_qs = asistencias_qs.filter(horario__sede=sede)

    # Ordenar por fecha descendente (más recientes primero)
    asistencias_qs = asistencias_qs.order_by('-fecha', 'usuario__nombre', 'horario__jornada')

    serializer = AsistenciaSerializer(asistencias_qs, many=True)
    
    # Estadísticas
    total_recuperables = asistencias_qs.count()
    monitores_afectados = asistencias_qs.values('usuario').distinct().count()
    
    # Agrupar por fecha para mejor visualización
    asistencias_por_fecha = {}
    for asistencia in asistencias_qs:
        fecha_str = asistencia.fecha.strftime('%Y-%m-%d')
        if fecha_str not in asistencias_por_fecha:
            asistencias_por_fecha[fecha_str] = []
        asistencias_por_fecha[fecha_str].append(AsistenciaSerializer(asistencia).data)

    response_data = {
        'periodo': {
            'fecha_inicio': str(fecha_inicio),
            'fecha_fin': str(fecha_fin)
        },
        'estadisticas': {
            'total_recuperables': total_recuperables,
            'monitores_afectados': monitores_afectados,
            'fechas_afectadas': len(asistencias_por_fecha)
        },
        'filtros_aplicados': {
            'monitor_id': monitor_id,
            'jornada': jornada,
            'sede': sede
        },
        'asistencias_por_fecha': asistencias_por_fecha,
        'asistencias': serializer.data
    }

    return Response(response_data)

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

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_recuperar_asistencia(request, pk):
    """
    Recuperar una asistencia que estaba pendiente y ya pasó la fecha.
    Solo funciona si:
    1. La asistencia está en estado 'pendiente'
    2. La fecha de la asistencia ya pasó
    3. La solicitud viene de un DIRECTIVO
    """
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
        return Response({'detail': 'Asistencia no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    # Validar que la asistencia esté en estado pendiente
    if asistencia.estado_autorizacion != 'pendiente':
        return Response(
            {'detail': f'La asistencia debe estar en estado "pendiente" para poder recuperarla. Estado actual: {asistencia.estado_autorizacion}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validar que la fecha ya haya pasado
    from datetime import date
    if asistencia.fecha >= date.today():
        return Response(
            {'detail': 'Solo se pueden recuperar asistencias de fechas pasadas'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    # Cambiar estado a recuperado
    asistencia.estado_autorizacion = 'recuperado'
    calcular_horas_asistencia(asistencia)
    asistencia.save()
    
    return Response({
        'mensaje': 'Asistencia recuperada exitosamente',
        'asistencia': AsistenciaSerializer(asistencia).data
    })

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
    
    REGLAS DE MARCADO:
    - Los monitores pueden marcar CUALQUIER JORNADA durante TODO EL DÍA si está autorizada
    - Pueden marcar asistencia de MAÑANA en la TARDE y viceversa
    - Solo importa que sea el mismo día y que esté autorizada por un directivo
    - No hay restricciones de horario - pueden marcar a cualquier hora del día
    - No se puede marcar fechas futuras
    """
    usuario = request.user
    print(f"=== MONITOR MARCAR - Usuario autenticado: {usuario.username} (ID: {usuario.id}) ===")
    
    if usuario.tipo_usuario != 'MONITOR':
        return Response({'detail': 'Solo monitores pueden marcar asistencia'}, status=status.HTTP_403_FORBIDDEN)

    fecha_obj = _parse_fecha(request.data.get('fecha'))
    jornada = request.data.get('jornada')
    
    # Validar jornada
    if jornada not in ['M', 'T']:
        return Response({'detail': 'Jornada inválida. Debe ser M (Mañana) o T (Tarde)'}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que no sea fecha futura
    from datetime import date
    if fecha_obj > date.today():
        return Response({'detail': 'No puedes marcar asistencia para fechas futuras'}, status=status.HTTP_400_BAD_REQUEST)

    # Buscar el horario fijo del usuario para ese día y jornada
    dia_semana = _dia_semana_de_fecha(fecha_obj)
    try:
        horario = HorarioFijo.objects.get(usuario=usuario, dia_semana=dia_semana, jornada=jornada)
    except HorarioFijo.DoesNotExist:
        return Response({'detail': 'No tienes horario asignado para esa jornada en este día'}, status=status.HTTP_400_BAD_REQUEST)

    # Crear o obtener la asistencia
    asistencia, created = Asistencia.objects.get_or_create(
        usuario=usuario,
        fecha=fecha_obj,
        horario=horario,
        defaults={'presente': False, 'estado_autorizacion': 'pendiente', 'horas': 0.00}
    )

    # Solo permite marcar si el bloque fue autorizado o recuperado por un DIRECTIVO
    if asistencia.estado_autorizacion not in ['autorizado', 'recuperado']:
        return Response(
            {
                'detail': 'Esta jornada aún no ha sido autorizada por un directivo.',
                'code': 'not_authorized',
                'jornada': jornada,
                'fecha': fecha_obj.strftime('%Y-%m-%d')
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # Verificar si ya está marcada como presente
    if asistencia.presente:
        return Response(
            {
                'detail': 'Ya has marcado asistencia para esta jornada',
                'jornada': jornada,
                'fecha': fecha_obj.strftime('%Y-%m-%d'),
                'asistencia': AsistenciaSerializer(asistencia).data
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Marcar como presente y calcular horas
    asistencia.presente = True
    calcular_horas_asistencia(asistencia)
    asistencia.save()

    return Response({
        'mensaje': f'Asistencia marcada exitosamente para {jornada}',
        'asistencia': AsistenciaSerializer(asistencia).data
    })


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


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_buscar_monitores(request):
    """
    Buscar monitores por nombre o username.
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

    # Parámetro de búsqueda
    busqueda = request.query_params.get('q', '').strip()
    
    if not busqueda:
        return Response({'detail': 'Parámetro de búsqueda "q" es requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(busqueda) < 2:
        return Response({'detail': 'La búsqueda debe tener al menos 2 caracteres'}, status=status.HTTP_400_BAD_REQUEST)

    # Buscar monitores por nombre o username (case-insensitive)
    from django.db.models import Q
    monitores = UsuarioPersonalizado.objects.filter(
        tipo_usuario='MONITOR'
    ).filter(
        Q(nombre__icontains=busqueda) | Q(username__icontains=busqueda)
    ).order_by('nombre')[:20]  # Limitar a 20 resultados

    # Serializar resultados
    resultados = []
    for monitor in monitores:
        resultados.append({
            'id': monitor.id,
            'username': monitor.username,
            'nombre': monitor.nombre
        })

    response_data = {
        'busqueda': busqueda,
        'total_encontrados': len(resultados),
        'monitores': resultados
    }

    return Response(response_data)


# ===== Endpoints para FINANZAS =====

def obtener_configuracion(clave, valor_por_defecto=None):
    """
    Obtiene el valor de una configuración del sistema.
    Si no existe, retorna el valor por defecto.
    """
    try:
        config = ConfiguracionSistema.objects.get(clave=clave)
        return config.get_valor_tipado()
    except ConfiguracionSistema.DoesNotExist:
        return valor_por_defecto

def obtener_costo_por_hora():
    """
    Obtiene el costo por hora desde las configuraciones.
    Por defecto: 9965 COP
    """
    return obtener_configuracion('costo_por_hora', 9965.0)

def obtener_semanas_semestre():
    """
    Obtiene el total de semanas del semestre desde las configuraciones.
    Por defecto: 14 semanas
    """
    return obtener_configuracion('semanas_semestre', 14)

def calcular_horas_semanales_monitor(monitor_id):
    """
    Calcula las horas semanales que debe trabajar un monitor basado en sus horarios fijos.
    Cada jornada (M/T) = 4 horas.
    """
    horarios = HorarioFijo.objects.filter(usuario_id=monitor_id)
    total_horas_semana = horarios.count() * 4  # 4 horas por jornada
    return total_horas_semana

def calcular_costo_total_monitor(monitor_id, fecha_inicio, fecha_fin):
    """
    Calcula el costo total que debe recibir un monitor en un período.
    Incluye horas de asistencias + ajustes de horas.
    """
    calculo_horas = calcular_horas_totales_monitor(monitor_id, fecha_inicio, fecha_fin)
    costo_por_hora = obtener_costo_por_hora()
    costo_total = calculo_horas['horas_totales'] * costo_por_hora
    return round(costo_total, 2)

def calcular_costo_proyectado_monitor(monitor_id, semanas_trabajadas, total_semanas=None):
    """
    Calcula el costo proyectado de un monitor basado en sus horarios fijos.
    """
    if total_semanas is None:
        total_semanas = obtener_semanas_semestre()
    
    horas_semanales = calcular_horas_semanales_monitor(monitor_id)
    horas_totales_proyectadas = horas_semanales * total_semanas
    horas_trabajadas_proyectadas = horas_semanales * semanas_trabajadas
    costo_por_hora = obtener_costo_por_hora()
    
    return {
        'horas_semanales': horas_semanales,
        'horas_totales_proyectadas': horas_totales_proyectadas,
        'horas_trabajadas_proyectadas': horas_trabajadas_proyectadas,
        'costo_total_proyectado': round(horas_totales_proyectadas * costo_por_hora, 2),
        'costo_trabajado_proyectado': round(horas_trabajadas_proyectadas * costo_por_hora, 2),
        'semanas_trabajadas': semanas_trabajadas,
        'semanas_faltantes': total_semanas - semanas_trabajadas
    }

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_finanzas_monitor_individual(request, monitor_id):
    """
    Reporte financiero individual de un monitor específico.
    Incluye costo actual, proyectado, horas semanales, etc.
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
    semanas_trabajadas = request.query_params.get('semanas_trabajadas', 8)  # Por defecto 8 semanas

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

    # Validar semanas_trabajadas
    try:
        semanas_trabajadas = int(semanas_trabajadas)
        max_semanas = obtener_semanas_semestre()
        if semanas_trabajadas < 0 or semanas_trabajadas > max_semanas:
            return Response({'detail': f'semanas_trabajadas debe estar entre 0 y {max_semanas}'}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({'detail': 'semanas_trabajadas debe ser un número entero'}, status=status.HTTP_400_BAD_REQUEST)

    # Calcular horas y costos
    calculo_horas = calcular_horas_totales_monitor(monitor_id, fecha_inicio, fecha_fin)
    costo_actual = calcular_costo_total_monitor(monitor_id, fecha_inicio, fecha_fin)
    proyeccion = calcular_costo_proyectado_monitor(monitor_id, semanas_trabajadas)

    # Información de horarios
    horarios = HorarioFijo.objects.filter(usuario=monitor)
    horarios_por_dia = {}
    for horario in horarios:
        dia = horario.get_dia_semana_display()
        if dia not in horarios_por_dia:
            horarios_por_dia[dia] = []
        horarios_por_dia[dia].append({
            'jornada': horario.get_jornada_display(),
            'sede': horario.get_sede_display()
        })

    # Respuesta
    response_data = {
        'monitor': {
            'id': monitor.id,
            'username': monitor.username,
            'nombre': monitor.nombre
        },
        'periodo_actual': {
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
            'dias_trabajados': (fecha_fin - fecha_inicio).days + 1
        },
        'horarios_semanales': {
            'horas_por_semana': proyeccion['horas_semanales'],
            'jornadas_por_semana': proyeccion['horas_semanales'] // 4,
            'detalle_por_dia': horarios_por_dia
        },
        'finanzas_actuales': {
            'horas_trabajadas': calculo_horas['horas_totales'],
            'horas_asistencias': calculo_horas['horas_asistencias'],
            'horas_ajustes': calculo_horas['horas_ajustes'],
            'costo_total': costo_actual,
            'costo_por_hora': obtener_costo_por_hora()
        },
        'proyeccion_semestre': {
            'semanas_trabajadas': proyeccion['semanas_trabajadas'],
            'semanas_faltantes': proyeccion['semanas_faltantes'],
            'horas_totales_proyectadas': proyeccion['horas_totales_proyectadas'],
            'horas_trabajadas_proyectadas': proyeccion['horas_trabajadas_proyectadas'],
            'costo_total_proyectado': proyeccion['costo_total_proyectado'],
            'costo_trabajado_proyectado': proyeccion['costo_trabajado_proyectado'],
            'porcentaje_completado': round((proyeccion['semanas_trabajadas'] / obtener_semanas_semestre()) * 100, 2)
        },
        'estadisticas': {
            'total_asistencias': calculo_horas['total_asistencias'],
            'total_ajustes': calculo_horas['total_ajustes'],
            'promedio_horas_por_dia': round(calculo_horas['horas_totales'] / max(1, (fecha_fin - fecha_inicio).days + 1), 2)
        }
    }

    return Response(response_data)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_finanzas_todos_monitores(request):
    """
    Reporte financiero consolidado de todos los monitores.
    Incluye costos totales, proyecciones, comparativas, etc.
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
    semanas_trabajadas = request.query_params.get('semanas_trabajadas', 8)  # Por defecto 8 semanas

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

    # Validar semanas_trabajadas
    try:
        semanas_trabajadas = int(semanas_trabajadas)
        max_semanas = obtener_semanas_semestre()
        if semanas_trabajadas < 0 or semanas_trabajadas > max_semanas:
            return Response({'detail': f'semanas_trabajadas debe estar entre 0 y {max_semanas}'}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({'detail': 'semanas_trabajadas debe ser un número entero'}, status=status.HTTP_400_BAD_REQUEST)

    # Obtener todos los monitores
    monitores = UsuarioPersonalizado.objects.filter(tipo_usuario='MONITOR')
    
    # Calcular datos para cada monitor
    monitores_data = []
    total_costo_actual = 0.0
    total_costo_proyectado = 0.0
    total_horas_actuales = 0.0
    total_horas_proyectadas = 0.0
    
    for monitor in monitores:
        # Calcular horas y costos
        calculo_horas = calcular_horas_totales_monitor(monitor.id, fecha_inicio, fecha_fin)
        costo_actual = calcular_costo_total_monitor(monitor.id, fecha_inicio, fecha_fin)
        proyeccion = calcular_costo_proyectado_monitor(monitor.id, semanas_trabajadas)
        
        # Solo incluir monitores que tienen horarios asignados
        if proyeccion['horas_semanales'] > 0:
            monitor_data = {
                'monitor': {
                    'id': monitor.id,
                    'username': monitor.username,
                    'nombre': monitor.nombre
                },
                'horarios_semanales': {
                    'horas_por_semana': proyeccion['horas_semanales'],
                    'jornadas_por_semana': proyeccion['horas_semanales'] // 4
                },
                'finanzas_actuales': {
                    'horas_trabajadas': calculo_horas['horas_totales'],
                    'costo_total': costo_actual
                },
                'proyeccion_semestre': {
                    'semanas_trabajadas': proyeccion['semanas_trabajadas'],
                    'semanas_faltantes': proyeccion['semanas_faltantes'],
                    'costo_total_proyectado': proyeccion['costo_total_proyectado'],
                    'costo_trabajado_proyectado': proyeccion['costo_trabajado_proyectado'],
                    'porcentaje_completado': round((proyeccion['semanas_trabajadas'] / obtener_semanas_semestre()) * 100, 2)
                },
                'estadisticas': {
                    'total_asistencias': calculo_horas['total_asistencias'],
                    'total_ajustes': calculo_horas['total_ajustes']
                }
            }
            
            monitores_data.append(monitor_data)
            
            # Acumular totales
            total_costo_actual += costo_actual
            total_costo_proyectado += proyeccion['costo_total_proyectado']
            total_horas_actuales += calculo_horas['horas_totales']
            total_horas_proyectadas += proyeccion['horas_totales_proyectadas']

    # Ordenar monitores por costo actual (descendente)
    monitores_data.sort(key=lambda x: x['finanzas_actuales']['costo_total'], reverse=True)

    # Calcular estadísticas generales
    total_monitores = len(monitores_data)
    costo_promedio_por_monitor = total_costo_actual / max(1, total_monitores)
    horas_promedio_por_monitor = total_horas_actuales / max(1, total_monitores)

    # Respuesta
    response_data = {
        'periodo_actual': {
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
            'dias_trabajados': (fecha_fin - fecha_inicio).days + 1
        },
        'semanas_trabajadas': semanas_trabajadas,
        'estadisticas_generales': {
            'total_monitores': total_monitores,
            'costo_total_actual': round(total_costo_actual, 2),
            'costo_total_proyectado': round(total_costo_proyectado, 2),
            'costo_promedio_por_monitor': round(costo_promedio_por_monitor, 2),
            'horas_totales_actuales': round(total_horas_actuales, 2),
            'horas_totales_proyectadas': round(total_horas_proyectadas, 2),
            'horas_promedio_por_monitor': round(horas_promedio_por_monitor, 2),
            'costo_por_hora': obtener_costo_por_hora()
        },
        'resumen_financiero': {
            'diferencia_proyeccion_vs_actual': round(total_costo_proyectado - total_costo_actual, 2),
            'porcentaje_ejecutado': round((total_costo_actual / max(1, total_costo_proyectado)) * 100, 2),
            'costo_semanal_promedio': round(total_costo_actual / max(1, (fecha_fin - fecha_inicio).days + 1) * 7, 2)
        },
        'monitores': monitores_data
    }

    return Response(response_data)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_finanzas_resumen_ejecutivo(request):
    """
    Resumen ejecutivo financiero del sistema.
    Dashboard con métricas clave, tendencias y alertas.
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
    semanas_trabajadas = request.query_params.get('semanas_trabajadas', 8)

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

    # Validar semanas_trabajadas
    try:
        semanas_trabajadas = int(semanas_trabajadas)
        max_semanas = obtener_semanas_semestre()
        if semanas_trabajadas < 0 or semanas_trabajadas > max_semanas:
            return Response({'detail': f'semanas_trabajadas debe estar entre 0 y {max_semanas}'}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({'detail': 'semanas_trabajadas debe ser un número entero'}, status=status.HTTP_400_BAD_REQUEST)

    # Obtener todos los monitores
    monitores = UsuarioPersonalizado.objects.filter(tipo_usuario='MONITOR')
    
    # Calcular métricas generales
    total_costo_actual = 0.0
    total_costo_proyectado = 0.0
    total_horas_actuales = 0.0
    total_horas_proyectadas = 0.0
    monitores_activos = 0
    monitores_con_horarios = 0
    
    # Top monitores por costo
    monitores_costo = []
    
    for monitor in monitores:
        calculo_horas = calcular_horas_totales_monitor(monitor.id, fecha_inicio, fecha_fin)
        costo_actual = calcular_costo_total_monitor(monitor.id, fecha_inicio, fecha_fin)
        proyeccion = calcular_costo_proyectado_monitor(monitor.id, semanas_trabajadas)
        
        # Contar monitores con horarios
        if proyeccion['horas_semanales'] > 0:
            monitores_con_horarios += 1
            
            # Contar monitores activos (con horas trabajadas)
            if calculo_horas['horas_totales'] > 0:
                monitores_activos += 1
            
            # Acumular totales
            total_costo_actual += costo_actual
            total_costo_proyectado += proyeccion['costo_total_proyectado']
            total_horas_actuales += calculo_horas['horas_totales']
            total_horas_proyectadas += proyeccion['horas_totales_proyectadas']
            
            # Para top monitores
            monitores_costo.append({
                'monitor': {
                    'id': monitor.id,
                    'nombre': monitor.nombre,
                    'username': monitor.username
                },
                'costo_actual': costo_actual,
                'horas_trabajadas': calculo_horas['horas_totales']
            })

    # Ordenar por costo y tomar top 5
    monitores_costo.sort(key=lambda x: x['costo_actual'], reverse=True)
    top_monitores = monitores_costo[:5]

    # Calcular alertas y tendencias
    porcentaje_ejecutado = (total_costo_actual / max(1, total_costo_proyectado)) * 100
    costo_semanal_promedio = total_costo_actual / max(1, (fecha_fin - fecha_inicio).days + 1) * 7
    
    alertas = []
    if porcentaje_ejecutado > 80:
        alertas.append({
            'tipo': 'warning',
            'mensaje': f'Se ha ejecutado el {porcentaje_ejecutado:.1f}% del presupuesto proyectado'
        })
    
    if monitores_activos < monitores_con_horarios * 0.5:
        alertas.append({
            'tipo': 'info',
            'mensaje': f'Solo {monitores_activos} de {monitores_con_horarios} monitores han trabajado en el período'
        })

    # Respuesta
    response_data = {
        'periodo': {
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
            'semanas_trabajadas': semanas_trabajadas
        },
        'metricas_principales': {
            'total_monitores': monitores_con_horarios,
            'monitores_activos': monitores_activos,
            'porcentaje_actividad': round((monitores_activos / max(1, monitores_con_horarios)) * 100, 2),
            'costo_total_actual': round(total_costo_actual, 2),
            'costo_total_proyectado': round(total_costo_proyectado, 2),
            'horas_totales_actuales': round(total_horas_actuales, 2),
            'horas_totales_proyectadas': round(total_horas_proyectadas, 2)
        },
        'indicadores_financieros': {
            'costo_por_hora': obtener_costo_por_hora(),
            'costo_promedio_por_monitor': round(total_costo_actual / max(1, monitores_con_horarios), 2),
            'costo_semanal_promedio': round(costo_semanal_promedio, 2),
            'porcentaje_ejecutado': round(porcentaje_ejecutado, 2),
            'diferencia_presupuesto': round(total_costo_proyectado - total_costo_actual, 2)
        },
        'top_monitores': {
            'por_costo': top_monitores,
            'total_considerados': len(monitores_costo)
        },
        'alertas': alertas,
        'resumen_semanal': {
            'costo_semanal_total': round(costo_semanal_promedio * monitores_con_horarios, 2),
            'horas_semanal_promedio': round(total_horas_actuales / max(1, (fecha_fin - fecha_inicio).days + 1) * 7, 2),
            'proyeccion_fin_semestre': round(total_costo_proyectado - total_costo_actual, 2)
        }
    }

    return Response(response_data)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_finanzas_comparativa_semanas(request):
    """
    Comparativa financiera por semanas del semestre.
    Muestra evolución de costos y horas por semana.
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

    # Obtener todos los monitores
    monitores = UsuarioPersonalizado.objects.filter(tipo_usuario='MONITOR')
    
    # Calcular datos por semana (simulado para las primeras 16 semanas)
    semanas_data = []
    total_semanas = obtener_semanas_semestre()
    
    for semana in range(1, total_semanas + 1):
        semana_costo_total = 0.0
        semana_horas_total = 0.0
        monitores_semana = 0
        
        for monitor in monitores:
            # Simular datos por semana (en un caso real, esto vendría de datos históricos)
            proyeccion = calcular_costo_proyectado_monitor(monitor.id, semana)
            
            if proyeccion['horas_semanales'] > 0:
                semana_costo_total += proyeccion['costo_trabajado_proyectado']
                semana_horas_total += proyeccion['horas_trabajadas_proyectadas']
                monitores_semana += 1
        
        semanas_data.append({
            'semana': semana,
            'costo_total': round(semana_costo_total, 2),
            'horas_total': round(semana_horas_total, 2),
            'monitores_activos': monitores_semana,
            'costo_promedio_por_monitor': round(semana_costo_total / max(1, monitores_semana), 2),
            'estado': 'completada' if semana <= 8 else 'pendiente'
        })
    
    # Calcular totales acumulados
    costo_acumulado = 0.0
    horas_acumuladas = 0.0
    
    for semana_data in semanas_data:
        costo_acumulado += semana_data['costo_total']
        horas_acumuladas += semana_data['horas_total']
        semana_data['costo_acumulado'] = round(costo_acumulado, 2)
        semana_data['horas_acumuladas'] = round(horas_acumuladas, 2)
    
    # Calcular porcentajes después de tener todos los totales acumulados
    costo_total_final = semanas_data[-1]['costo_acumulado'] if semanas_data else 0
    for semana_data in semanas_data:
        semana_data['porcentaje_completado'] = round((semana_data['costo_acumulado'] / max(1, costo_total_final)) * 100, 2)

    # Respuesta
    response_data = {
        'total_semanas': total_semanas,
        'semanas_trabajadas': 8,  # Por defecto
        'semanas_pendientes': total_semanas - 8,
        'resumen_general': {
            'costo_total_semestre': round(semanas_data[-1]['costo_acumulado'], 2),
            'horas_total_semestre': round(semanas_data[-1]['horas_acumuladas'], 2),
            'costo_promedio_por_semana': round(semanas_data[-1]['costo_acumulado'] / total_semanas, 2),
            'horas_promedio_por_semana': round(semanas_data[-1]['horas_acumuladas'] / total_semanas, 2)
        },
        'semanas': semanas_data,
        'tendencias': {
            'costo_por_semana': [s['costo_total'] for s in semanas_data],
            'horas_por_semana': [s['horas_total'] for s in semanas_data],
            'costo_acumulado': [s['costo_acumulado'] for s in semanas_data]
        }
    }

    return Response(response_data)


# ===== Endpoints para CONFIGURACIONES DEL SISTEMA =====

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_configuraciones(request):
    """
    Listar todas las configuraciones del sistema.
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

    configuraciones = ConfiguracionSistema.objects.all().select_related('creado_por')
    serializer = ConfiguracionSistemaSerializer(configuraciones, many=True)
    
    return Response({
        'total_configuraciones': configuraciones.count(),
        'configuraciones': serializer.data
    })

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_configuraciones_crear(request):
    """
    Crear nueva configuración del sistema.
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

    serializer = ConfiguracionSistemaCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Verificar si ya existe una configuración con esa clave
        clave = serializer.validated_data['clave']
        if ConfiguracionSistema.objects.filter(clave=clave).exists():
            return Response(
                {'detail': f'Ya existe una configuración con la clave "{clave}"'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        configuracion = serializer.save(creado_por=usuario_directivo)
        return Response(ConfiguracionSistemaSerializer(configuracion).data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_configuraciones_detalle(request, clave):
    """
    GET: Obtener configuración específica
    PUT: Actualizar configuración
    DELETE: Eliminar configuración
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

    try:
        configuracion = ConfiguracionSistema.objects.select_related('creado_por').get(clave=clave)
    except ConfiguracionSistema.DoesNotExist:
        return Response({'detail': 'Configuración no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ConfiguracionSistemaSerializer(configuracion)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ConfiguracionSistemaCreateSerializer(configuracion, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(ConfiguracionSistemaSerializer(configuracion).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        configuracion.delete()
        return Response({'detail': 'Configuración eliminada exitosamente'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_configuraciones_detalle_por_id(request, id):
    """
    GET: Obtener configuración específica por ID
    PUT: Actualizar configuración por ID
    DELETE: Eliminar configuración por ID
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

    try:
        configuracion = ConfiguracionSistema.objects.select_related('creado_por').get(id=id)
    except ConfiguracionSistema.DoesNotExist:
        return Response({'detail': 'Configuración no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ConfiguracionSistemaSerializer(configuracion)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ConfiguracionSistemaCreateSerializer(configuracion, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(ConfiguracionSistemaSerializer(configuracion).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        configuracion.delete()
        return Response({'detail': 'Configuración eliminada exitosamente'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_total_horas_horarios(request):
    """
    Calcular el total de horas basado en los horarios fijos de los monitores * total de semanas.
    Filtros opcionales: monitor_id, sede, jornada
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
    monitor_id = request.query_params.get('monitor_id')
    sede = request.query_params.get('sede')  # SA|BA
    jornada = request.query_params.get('jornada')  # M|T

    # Validar filtros
    if sede and sede not in ['SA', 'BA']:
        return Response({'detail': 'sede debe ser SA o BA'}, status=status.HTTP_400_BAD_REQUEST)
    if jornada and jornada not in ['M', 'T']:
        return Response({'detail': 'jornada debe ser M o T'}, status=status.HTTP_400_BAD_REQUEST)

    # Obtener configuración de semanas del semestre
    total_semanas = obtener_semanas_semestre()
    costo_por_hora = obtener_costo_por_hora()

    # Query base para horarios fijos
    horarios_qs = HorarioFijo.objects.filter(usuario__tipo_usuario='MONITOR')
    
    # Aplicar filtros
    if monitor_id:
        try:
            monitor_id = int(monitor_id)
            horarios_qs = horarios_qs.filter(usuario__id=monitor_id)
        except ValueError:
            return Response({'detail': 'monitor_id debe ser un número entero'}, status=status.HTTP_400_BAD_REQUEST)
    
    if sede:
        horarios_qs = horarios_qs.filter(sede=sede)
    if jornada:
        horarios_qs = horarios_qs.filter(jornada=jornada)

    # Calcular estadísticas por monitor
    monitores_data = {}
    total_horarios = 0
    total_horas_semanales = 0
    total_horas_semestre = 0
    total_costo_semestre = 0

    # Agrupar horarios por monitor
    for horario in horarios_qs.select_related('usuario'):
        monitor = horario.usuario
        monitor_id = monitor.id
        
        if monitor_id not in monitores_data:
            monitores_data[monitor_id] = {
                'monitor': {
                    'id': monitor.id,
                    'username': monitor.username,
                    'nombre': monitor.nombre
                },
                'horarios': [],
                'horas_semanales': 0,
                'horas_semestre': 0,
                'costo_semestre': 0,
                'total_jornadas_semana': 0
            }
        
        # Agregar horario al monitor
        horario_data = {
            'id': horario.id,
            'dia_semana': horario.dia_semana,
            'dia_semana_display': horario.get_dia_semana_display(),
            'jornada': horario.jornada,
            'jornada_display': horario.get_jornada_display(),
            'sede': horario.sede,
            'sede_display': horario.get_sede_display()
        }
        monitores_data[monitor_id]['horarios'].append(horario_data)
        monitores_data[monitor_id]['total_jornadas_semana'] += 1

    # Calcular horas y costos para cada monitor
    for monitor_id, data in monitores_data.items():
        # Cada jornada = 4 horas
        horas_semanales = data['total_jornadas_semana'] * 4
        horas_semestre = horas_semanales * total_semanas
        costo_semestre = horas_semestre * costo_por_hora
        
        data['horas_semanales'] = horas_semanales
        data['horas_semestre'] = horas_semestre
        data['costo_semestre'] = round(costo_semestre, 2)
        
        # Acumular totales
        total_horarios += data['total_jornadas_semana']
        total_horas_semanales += horas_semanales
        total_horas_semestre += horas_semestre
        total_costo_semestre += costo_semestre

    # Ordenar monitores por horas semanales (descendente)
    monitores_ordenados = sorted(
        monitores_data.values(),
        key=lambda x: x['horas_semanales'],
        reverse=True
    )

    # Calcular estadísticas generales
    total_monitores = len(monitores_data)
    promedio_horas_semana = total_horas_semanales / max(1, total_monitores)
    promedio_costo_semestre = total_costo_semestre / max(1, total_monitores)

    # Respuesta
    response_data = {
        'configuracion': {
            'total_semanas_semestre': total_semanas,
            'costo_por_hora': costo_por_hora,
            'horas_por_jornada': 4
        },
        'estadisticas_generales': {
            'total_monitores': total_monitores,
            'total_horarios': total_horarios,
            'total_horas_semanales': total_horas_semanales,
            'total_horas_semestre': total_horas_semestre,
            'total_costo_semestre': round(total_costo_semestre, 2),
            'promedio_horas_semana_por_monitor': round(promedio_horas_semana, 2),
            'promedio_costo_semestre_por_monitor': round(promedio_costo_semestre, 2)
        },
        'filtros_aplicados': {
            'monitor_id': monitor_id,
            'sede': sede,
            'jornada': jornada
        },
        'monitores': monitores_ordenados,
        'resumen_por_sede': _calcular_resumen_por_sede(monitores_data),
        'resumen_por_jornada': _calcular_resumen_por_jornada(monitores_data)
    }

    return Response(response_data)

def _calcular_resumen_por_sede(monitores_data):
    """Calcular resumen de horas por sede"""
    resumen = {'SA': {'monitores': 0, 'horas_semana': 0, 'horas_semestre': 0}, 
               'BA': {'monitores': 0, 'horas_semana': 0, 'horas_semestre': 0}}
    
    for data in monitores_data.values():
        for horario in data['horarios']:
            sede = horario['sede']
            if sede in resumen:
                resumen[sede]['monitores'] += 1
                resumen[sede]['horas_semana'] += 4  # 4 horas por jornada
                resumen[sede]['horas_semestre'] += 4 * 14  # 14 semanas por defecto
    
    return resumen

def _calcular_resumen_por_jornada(monitores_data):
    """Calcular resumen de horas por jornada"""
    resumen = {'M': {'monitores': 0, 'horas_semana': 0, 'horas_semestre': 0}, 
               'T': {'monitores': 0, 'horas_semana': 0, 'horas_semestre': 0}}
    
    for data in monitores_data.values():
        for horario in data['horarios']:
            jornada = horario['jornada']
            if jornada in resumen:
                resumen[jornada]['monitores'] += 1
                resumen[jornada]['horas_semana'] += 4  # 4 horas por jornada
                resumen[jornada]['horas_semestre'] += 4 * 14  # 14 semanas por defecto
    
    return resumen

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def directivo_configuraciones_inicializar(request):
    """
    Inicializar configuraciones por defecto del sistema.
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

    configuraciones_por_defecto = [
        {
            'clave': 'costo_por_hora',
            'valor': '9965',
            'descripcion': 'Costo por hora de trabajo de los monitores en pesos colombianos (COP)',
            'tipo_dato': 'decimal'
        },
        {
            'clave': 'semanas_semestre',
            'valor': '14',
            'descripcion': 'Total de semanas que dura un semestre académico',
            'tipo_dato': 'entero'
        }
    ]

    configuraciones_creadas = []
    configuraciones_existentes = []

    for config_data in configuraciones_por_defecto:
        clave = config_data['clave']
        
        if ConfiguracionSistema.objects.filter(clave=clave).exists():
            configuraciones_existentes.append(clave)
        else:
            configuracion = ConfiguracionSistema.objects.create(
                clave=clave,
                valor=config_data['valor'],
                descripcion=config_data['descripcion'],
                tipo_dato=config_data['tipo_dato'],
                creado_por=usuario_directivo
            )
            configuraciones_creadas.append(ConfiguracionSistemaSerializer(configuracion).data)

    return Response({
        'mensaje': f'Se crearon {len(configuraciones_creadas)} configuraciones nuevas',
        'configuraciones_creadas': configuraciones_creadas,
        'configuraciones_existentes': configuraciones_existentes,
        'total_procesadas': len(configuraciones_por_defecto)
    }, status=status.HTTP_201_CREATED)