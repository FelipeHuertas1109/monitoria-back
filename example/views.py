from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import authenticate
from .models import UsuarioPersonalizado, HorarioFijo, Asistencia
from .serializers import (
    LoginSerializer, TokenSerializer, UsuarioSerializer, UsuarioCreateSerializer,
    HorarioFijoSerializer, HorarioFijoCreateSerializer, HorarioFijoMultipleSerializer, HorarioFijoEditMultipleSerializer,
    AsistenciaSerializer, AsistenciaCreateSerializer
)

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
    # Verificar autenticación manualmente
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response(
            {'detail': 'Token de autenticación requerido', 'code': 'token_required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    token = auth_header.split(' ')[1]
    
    # Buscar usuario (temporalmente usamos el primero)
    try:
        usuario = UsuarioPersonalizado.objects.first()
        if not usuario:
            return Response(
                {'detail': 'User not found', 'code': 'user_not_found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {'detail': f'Error al buscar usuario: {str(e)}', 'code': 'user_error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
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
    # Verificar autenticación manualmente
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response(
            {'detail': 'Token de autenticación requerido', 'code': 'token_required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    token = auth_header.split(' ')[1]
    
    # Buscar usuario (temporalmente usamos el primero)
    try:
        usuario = UsuarioPersonalizado.objects.first()
        if not usuario:
            return Response(
                {'detail': 'User not found', 'code': 'user_not_found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {'detail': f'Error al buscar usuario: {str(e)}', 'code': 'user_error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
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
    
    # Verificar autenticación manualmente
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response(
            {'detail': 'Token de autenticación requerido', 'code': 'token_required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    token = auth_header.split(' ')[1]
    
    # Debug: verificar usuarios en la base de datos
    try:
        # Contar usuarios totales
        total_usuarios = UsuarioPersonalizado.objects.count()
        print(f"Total de usuarios en la BD: {total_usuarios}")
        
        # Listar todos los usuarios
        usuarios = UsuarioPersonalizado.objects.all()
        for u in usuarios:
            print(f"Usuario: {u.username} (ID: {u.id}, Nombre: {u.nombre})")
        
        # Buscar el primer usuario disponible (temporal)
        usuario = UsuarioPersonalizado.objects.first()
        if not usuario:
            return Response(
                {
                    'detail': f'No hay usuarios en el sistema. Total encontrados: {total_usuarios}', 
                    'code': 'no_users',
                    'debug_info': {
                        'total_usuarios': total_usuarios,
                        'usuarios_list': [{'id': u.id, 'username': u.username, 'nombre': u.nombre} for u in usuarios]
                    }
                }, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        print(f"Usuario seleccionado: {usuario.username} (ID: {usuario.id})")
            
    except Exception as e:
        return Response(
            {'detail': f'Error al buscar usuario: {str(e)}', 'code': 'user_search_error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
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
    
    # Verificar autenticación manualmente
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response(
            {'detail': 'Token de autenticación requerido', 'code': 'token_required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    token = auth_header.split(' ')[1]
    
    # Debug: verificar usuarios en la base de datos
    try:
        # Contar usuarios totales
        total_usuarios = UsuarioPersonalizado.objects.count()
        print(f"Total de usuarios en la BD: {total_usuarios}")
        
        # Listar todos los usuarios
        usuarios = UsuarioPersonalizado.objects.all()
        for u in usuarios:
            print(f"Usuario: {u.username} (ID: {u.id}, Nombre: {u.nombre})")
        
        # Buscar el primer usuario disponible (temporal)
        usuario = UsuarioPersonalizado.objects.first()
        if not usuario:
            return Response(
                {
                    'detail': f'No hay usuarios en el sistema. Total encontrados: {total_usuarios}', 
                    'code': 'no_users',
                    'debug_info': {
                        'total_usuarios': total_usuarios,
                        'usuarios_list': [{'id': u.id, 'username': u.username, 'nombre': u.nombre} for u in usuarios]
                    }
                }, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        print(f"Usuario seleccionado: {usuario.username} (ID: {usuario.id})")
            
    except Exception as e:
        return Response(
            {'detail': f'Error al buscar usuario: {str(e)}', 'code': 'user_search_error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
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