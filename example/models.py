from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings

class UsuarioPersonalizado(models.Model):
    """
    Modelo de usuario completamente personalizado, independiente de Django
    """
    TIPOS_USUARIO = [
        ('MONITOR', 'Monitor'),
        ('DIRECTIVO', 'Directivo'),
    ]
    
    username = models.CharField(max_length=150, unique=True)
    nombre = models.CharField(max_length=255)
    password = models.CharField(max_length=128)
    tipo_usuario = models.CharField(max_length=10, choices=TIPOS_USUARIO, default='MONITOR')
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['nombre']
    
    def save(self, *args, **kwargs):
        # Hashear la contraseña solo si no está ya hasheada
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def set_password(self, raw_password):
        """Establecer la contraseña hasheada"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Verificar si la contraseña es correcta"""
        return check_password(raw_password, self.password)
    
    def is_authenticated(self):
        """Verificar si el usuario está autenticado"""
        return True
    
    def __str__(self):
        return f"{self.nombre} ({self.username}) - {self.get_tipo_usuario_display()}"
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"


# 📦 Modelos (versión final)


# Los modelos HorarioFijo y Asistencia se conectan directamente al UsuarioPersonalizado

class HorarioFijo(models.Model):
    """
    Plantilla que el usuario define UNA sola vez.
    Puede tener varias jornadas el mismo día, incluso en sedes distintas.
    """
    DIAS = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    JORNADAS = [
        ("M", "Mañana"),
        ("T", "Tarde"),
    ]

    SEDES = [
        ("SA", "San Antonio"),
        ("BA", "Barcelona"),
    ]

    usuario = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE, related_name="horario_fijo")
    dia_semana = models.IntegerField(choices=DIAS)
    jornada = models.CharField(max_length=1, choices=JORNADAS)
    sede = models.CharField(max_length=2, choices=SEDES)

    class Meta:
        unique_together = ("usuario", "dia_semana", "jornada")

    def __str__(self):
        return f"{self.usuario} - {self.get_dia_semana_display()} {self.get_jornada_display()} ({self.get_sede_display()})"


class Asistencia(models.Model):
    """
    Asistencia semanal basada en el HorarioFijo.
    """
    ESTADOS_AUTORIZACION = [
        ("pendiente", "Pendiente"),
        ("autorizado", "Autorizado"),
        ("rechazado", "Rechazado"),
    ]
    usuario = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE, related_name="asistencias")
    fecha = models.DateField()  # Día específico
    horario = models.ForeignKey(HorarioFijo, on_delete=models.CASCADE, related_name="asistencias")
    presente = models.BooleanField(default=False)
    estado_autorizacion = models.CharField(max_length=10, choices=ESTADOS_AUTORIZACION, default="pendiente")
    horas = models.DecimalField(max_digits=4, decimal_places=2, default=0.00, help_text="Horas trabajadas en esta jornada")

    class Meta:
        unique_together = ("usuario", "fecha", "horario")

    def __str__(self):
        estado = "Presente" if self.presente else "Pendiente"
        return f"{self.usuario} - {self.fecha} - {self.horario} [{estado} | {self.estado_autorizacion}]"


class AjusteHoras(models.Model):
    """
    Modelo para ajustes manuales de horas realizados por directivos.
    Permite agregar o restar horas a monitores con trazabilidad completa.
    """
    usuario = models.ForeignKey(
        UsuarioPersonalizado, 
        on_delete=models.CASCADE, 
        related_name="ajustes_horas",
        limit_choices_to={'tipo_usuario': 'MONITOR'},
        help_text="Monitor al que se le ajustan las horas"
    )
    fecha = models.DateField(help_text="Fecha del ajuste de horas")
    cantidad_horas = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        help_text="Cantidad de horas a ajustar (positivo para agregar, negativo para restar)"
    )
    motivo = models.TextField(help_text="Razón del ajuste de horas")
    asistencia = models.ForeignKey(
        Asistencia, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="ajustes_horas",
        help_text="Asistencia relacionada (opcional)"
    )
    creado_por = models.ForeignKey(
        UsuarioPersonalizado,
        on_delete=models.CASCADE,
        related_name="ajustes_creados",
        limit_choices_to={'tipo_usuario': 'DIRECTIVO'},
        help_text="Directivo que realizó el ajuste"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Fecha y hora de creación del ajuste")
    updated_at = models.DateTimeField(auto_now=True, help_text="Fecha y hora de última modificación")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Ajuste de Horas"
        verbose_name_plural = "Ajustes de Horas"

    def __str__(self):
        signo = "+" if self.cantidad_horas >= 0 else ""
        return f"{self.usuario.nombre} - {self.fecha} - {signo}{self.cantidad_horas}h - {self.motivo[:50]}"


class ConfiguracionSistema(models.Model):
    """
    Modelo para configuraciones del sistema que pueden ser editadas por directivos.
    Incluye parámetros financieros y de tiempo.
    """
    clave = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Clave única para identificar la configuración"
    )
    valor = models.CharField(
        max_length=255,
        help_text="Valor de la configuración"
    )
    descripcion = models.TextField(
        help_text="Descripción de qué representa esta configuración"
    )
    tipo_dato = models.CharField(
        max_length=20,
        choices=[
            ('decimal', 'Decimal'),
            ('entero', 'Entero'),
            ('texto', 'Texto'),
            ('booleano', 'Booleano')
        ],
        default='texto',
        help_text="Tipo de dato de la configuración"
    )
    creado_por = models.ForeignKey(
        UsuarioPersonalizado,
        on_delete=models.CASCADE,
        related_name="configuraciones_creadas",
        limit_choices_to={'tipo_usuario': 'DIRECTIVO'},
        help_text="Directivo que creó esta configuración"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
        ordering = ['clave']

    def get_valor_tipado(self):
        """
        Retorna el valor convertido al tipo de dato correspondiente.
        """
        if self.tipo_dato == 'decimal':
            try:
                return float(self.valor)
            except ValueError:
                return 0.0
        elif self.tipo_dato == 'entero':
            try:
                return int(self.valor)
            except ValueError:
                return 0
        elif self.tipo_dato == 'booleano':
            return self.valor.lower() in ['true', '1', 'yes', 'si']
        else:
            return self.valor

    def __str__(self):
        return f"{self.clave}: {self.valor} ({self.tipo_dato})"