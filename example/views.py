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
from .models import UsuarioPersonalizado, HorarioFijo, Asistencia

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
from .serializers import (
    LoginSerializer, TokenSerializer, UsuarioSerializer, UsuarioCreateSerializer,
    HorarioFijoSerializer, HorarioFijoCreateSerializer, HorarioFijoMultipleSerializer, HorarioFijoEditMultipleSerializer,
    AsistenciaSerializer, AsistenciaCreateSerializer
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