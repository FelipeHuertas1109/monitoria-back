from rest_framework import serializers
from .models import UsuarioPersonalizado, HorarioFijo, Asistencia, AjusteHoras, ConfiguracionSistema

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


class AjusteHorasSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    creado_por = UsuarioSerializer(read_only=True)
    asistencia = AsistenciaSerializer(read_only=True)
    
    class Meta:
        model = AjusteHoras
        fields = [
            'id', 'usuario', 'fecha', 'cantidad_horas', 'motivo', 
            'asistencia', 'creado_por', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AjusteHorasCreateSerializer(serializers.ModelSerializer):
    monitor_id = serializers.IntegerField(write_only=True, help_text="ID del monitor al que se le ajustan las horas")
    asistencia_id = serializers.IntegerField(write_only=True, required=False, allow_null=True, help_text="ID de la asistencia relacionada (opcional)")
    
    class Meta:
        model = AjusteHoras
        fields = ['monitor_id', 'fecha', 'cantidad_horas', 'motivo', 'asistencia_id']
    
    def validate_monitor_id(self, value):
        """Validar que el monitor existe"""
        try:
            monitor = UsuarioPersonalizado.objects.get(id=value, tipo_usuario='MONITOR')
            return value
        except UsuarioPersonalizado.DoesNotExist:
            raise serializers.ValidationError("Monitor no encontrado o no es de tipo MONITOR.")
    
    def validate_asistencia_id(self, value):
        """Validar que la asistencia existe si se proporciona"""
        if value is not None:
            try:
                Asistencia.objects.get(id=value)
                return value
            except Asistencia.DoesNotExist:
                raise serializers.ValidationError("Asistencia no encontrada.")
        return value
    
    def validate_cantidad_horas(self, value):
        """Validar rango de horas permitidas"""
        if value < -24.00 or value > 24.00:
            raise serializers.ValidationError("La cantidad de horas debe estar entre -24.00 y 24.00.")
        if value == 0:
            raise serializers.ValidationError("La cantidad de horas no puede ser 0.")
        return value
    
    def validate(self, data):
        """Validaciones adicionales"""
        # Si se proporciona asistencia_id, validar que pertenezca al monitor
        if data.get('asistencia_id'):
            try:
                asistencia = Asistencia.objects.get(id=data['asistencia_id'])
                if asistencia.usuario.id != data['monitor_id']:
                    raise serializers.ValidationError("La asistencia no pertenece al monitor especificado.")
            except Asistencia.DoesNotExist:
                pass  # Ya validado en validate_asistencia_id
        
        return data


# Serializers para Configuraciones del Sistema

class ConfiguracionSistemaSerializer(serializers.ModelSerializer):
    """
    Serializer para configuraciones del sistema.
    """
    creado_por = UsuarioSerializer(read_only=True)
    valor_tipado = serializers.SerializerMethodField()
    
    class Meta:
        model = ConfiguracionSistema
        fields = [
            'id', 'clave', 'valor', 'descripcion', 'tipo_dato',
            'creado_por', 'created_at', 'updated_at', 'valor_tipado'
        ]
        read_only_fields = ['id', 'creado_por', 'created_at', 'updated_at']
    
    def get_valor_tipado(self, obj):
        return obj.get_valor_tipado()

class ConfiguracionSistemaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar configuraciones del sistema.
    """
    class Meta:
        model = ConfiguracionSistema
        fields = ['clave', 'valor', 'descripcion', 'tipo_dato']
    
    def validate_clave(self, value):
        """
        Validar que la clave sea única y tenga formato válido.
        """
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError("La clave solo puede contener letras, números y guiones bajos.")
        return value.lower()
    
    def validate_valor(self, value):
        """
        Validar el valor según el tipo de dato.
        """
        tipo_dato = self.initial_data.get('tipo_dato')
        
        if tipo_dato == 'decimal':
            try:
                float(value)
            except ValueError:
                raise serializers.ValidationError("El valor debe ser un número decimal válido.")
        
        elif tipo_dato == 'entero':
            try:
                int(value)
            except ValueError:
                raise serializers.ValidationError("El valor debe ser un número entero válido.")
        
        elif tipo_dato == 'booleano':
            if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no', 'si', 'no']:
                raise serializers.ValidationError("El valor debe ser true/false, 1/0, yes/no o si/no.")
        
        return value
