from rest_framework import serializers
from .models import UsuarioPersonalizado, HorarioFijo, Asistencia

class UsuarioSerializer(serializers.ModelSerializer):
    tipo_usuario_display = serializers.CharField(source='get_tipo_usuario_display', read_only=True)
    
    class Meta:
        model = UsuarioPersonalizado
        fields = ['id', 'username', 'nombre', 'tipo_usuario', 'tipo_usuario_display']
        read_only_fields = ['id']

class UsuarioCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevos usuarios.
    El tipo_usuario se asigna automáticamente como MONITOR.
    """
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = UsuarioPersonalizado
        fields = ['username', 'nombre', 'password', 'confirm_password']
    
    def validate_username(self, value):
        """Validar que el username sea único"""
        if UsuarioPersonalizado.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return value
    
    def validate(self, data):
        """Validar que las contraseñas coincidan"""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return data
    
    def create(self, validated_data):
        """Crear usuario con tipo MONITOR por defecto"""
        # Remover confirm_password ya que no es parte del modelo
        validated_data.pop('confirm_password')
        
        # Crear usuario con tipo MONITOR por defecto
        usuario = UsuarioPersonalizado(
            username=validated_data['username'],
            nombre=validated_data['nombre'],
            tipo_usuario='MONITOR'  # Asignar automáticamente como MONITOR
        )
        usuario.set_password(validated_data['password'])
        usuario.save()
        
        return usuario

class LoginSerializer(serializers.Serializer):
    nombre_de_usuario = serializers.CharField()
    password = serializers.CharField()

class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    usuario = UsuarioSerializer()

class HorarioFijoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)
    jornada_display = serializers.CharField(source='get_jornada_display', read_only=True)
    sede_display = serializers.CharField(source='get_sede_display', read_only=True)
    
    class Meta:
        model = HorarioFijo
        fields = ['id', 'usuario', 'dia_semana', 'dia_semana_display', 'jornada', 'jornada_display', 'sede', 'sede_display']
        read_only_fields = ['id']

class HorarioFijoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorarioFijo
        fields = ['dia_semana', 'jornada', 'sede']

class HorarioFijoMultipleSerializer(serializers.Serializer):
    """
    Serializer para crear múltiples horarios fijos en una sola petición
    """
    horarios = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=50  # Máximo 50 horarios por petición
    )
    
    def validate_horarios(self, value):
        """
        Validar que cada horario tenga los campos requeridos y valores válidos
        """
        dias_validos = [0, 1, 2, 3, 4, 5, 6]
        jornadas_validas = ['M', 'T']
        sedes_validas = ['SA', 'BA']
        
        for i, horario in enumerate(value):
            # Verificar campos requeridos
            if 'dia_semana' not in horario:
                raise serializers.ValidationError(f"Horario {i+1}: campo 'dia_semana' es requerido")
            if 'jornada' not in horario:
                raise serializers.ValidationError(f"Horario {i+1}: campo 'jornada' es requerido")
            if 'sede' not in horario:
                raise serializers.ValidationError(f"Horario {i+1}: campo 'sede' es requerido")
            
            # Validar valores
            try:
                dia = int(horario['dia_semana'])
                if dia not in dias_validos:
                    raise serializers.ValidationError(f"Horario {i+1}: 'dia_semana' debe ser un valor entre 0-6")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Horario {i+1}: 'dia_semana' debe ser un número")
            
            if horario['jornada'] not in jornadas_validas:
                raise serializers.ValidationError(f"Horario {i+1}: 'jornada' debe ser 'M' o 'T'")
            
            if horario['sede'] not in sedes_validas:
                raise serializers.ValidationError(f"Horario {i+1}: 'sede' debe ser 'SA' o 'BA'")
        
        return value

class HorarioFijoEditMultipleSerializer(serializers.Serializer):
    """
    Serializer para editar múltiples horarios fijos en una sola petición
    """
    horarios = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=50  # Máximo 50 horarios por petición
    )
    
    def validate_horarios(self, value):
        """
        Validar que cada horario tenga los campos requeridos y valores válidos
        """
        dias_validos = [0, 1, 2, 3, 4, 5, 6]
        jornadas_validas = ['M', 'T']
        sedes_validas = ['SA', 'BA']
        
        for i, horario in enumerate(value):
            # Verificar campos requeridos
            if 'dia_semana' not in horario:
                raise serializers.ValidationError(f"Horario {i+1}: campo 'dia_semana' es requerido")
            if 'jornada' not in horario:
                raise serializers.ValidationError(f"Horario {i+1}: campo 'jornada' es requerido")
            if 'sede' not in horario:
                raise serializers.ValidationError(f"Horario {i+1}: campo 'sede' es requerido")
            
            # Validar valores
            try:
                dia = int(horario['dia_semana'])
                if dia not in dias_validos:
                    raise serializers.ValidationError(f"Horario {i+1}: 'dia_semana' debe ser un valor entre 0-6")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Horario {i+1}: 'dia_semana' debe ser un número")
            
            if horario['jornada'] not in jornadas_validas:
                raise serializers.ValidationError(f"Horario {i+1}: 'jornada' debe ser 'M' o 'T'")
            
            if horario['sede'] not in sedes_validas:
                raise serializers.ValidationError(f"Horario {i+1}: 'sede' debe ser 'SA' o 'BA'")
        
        return value

class AsistenciaSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    horario = HorarioFijoSerializer(read_only=True)
    estado_autorizacion_display = serializers.CharField(source='get_estado_autorizacion_display', read_only=True)
    
    class Meta:
        model = Asistencia
        fields = ['id', 'usuario', 'fecha', 'horario', 'presente', 'estado_autorizacion', 'estado_autorizacion_display', 'horas']
        read_only_fields = ['id']

class AsistenciaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asistencia
        fields = ['fecha', 'horario', 'presente']
