"""
Prompts predefinidos para guiar usuarios no expertos
"""


class UserPrompts:
    """
    Colección de prompts y mensajes amigables para usuarios sin conocimientos técnicos.
    """
    
    # Mensajes de bienvenida
    WELCOME_MESSAGES = [
        "¡Hola! Soy tu asistente de ciberseguridad. ¿En qué puedo ayudarte hoy?",
        "Bienvenido. Estoy aquí para ayudarte a analizar y proteger tu red.",
        "¡Saludos! ¿Qué aspecto de seguridad te gustaría revisar?",
    ]
    
    # Explicaciones para usuarios novatos
    EXPLANATIONS = {
        "escaneo": (
            "Un escaneo de red es como 'tocar las puertas' de un dispositivo para ver "
            "cuáles están abiertas. Esto nos ayuda a identificar servicios activos y "
            "posibles vulnerabilidades."
        ),
        "captura": (
            "Capturar tráfico es como 'escuchar' las conversaciones que suceden en tu red. "
            "Nos permite ver qué dispositivos están comunicándose y detectar actividad sospechosa."
        ),
        "whois": (
            "WHOIS es como la 'cédula de identidad' de un sitio web. Nos dice quién lo "
            "registró, cuándo y cuándo expira. Útil para verificar si un sitio es legítimo."
        ),
        "logs": (
            "Los logs son el 'diario del sistema'. Registran todo lo que sucede: errores, "
            "accesos, cambios. Revisarlos nos ayuda a detectar problemas o intrusos."
        ),
    }
    
    # Preguntas frecuentes
    FAQ = {
        "¿Qué puedes hacer?": (
            "Puedo ayudarte con:\n"
            "  • Escanear dispositivos en tu red para ver qué servicios están activos\n"
            "  • Capturar y analizar el tráfico de red\n"
            "  • Consultar información sobre dominios (WHOIS)\n"
            "  • Revisar logs del sistema en busca de problemas\n"
            "  • Explicarte los resultados en términos simples"
        ),
        "¿Es seguro?": (
            "Sí. Todas las herramientas que uso son estándar en ciberseguridad y no dañan "
            "tu sistema. Además, te pediré confirmación antes de ejecutar acciones sensibles."
        ),
        "¿Necesito conocimientos técnicos?": (
            "No. Mi trabajo es traducir toda la información técnica a un lenguaje que "
            "cualquiera pueda entender. Solo dime qué necesitas revisar."
        ),
        "¿Qué hago si encuentras algo malo?": (
            "Te explicaré claramente qué se encontró, qué significa y te daré recomendaciones "
            "específicas sobre qué hacer. No te preocupes, te guiaré paso a paso."
        ),
    }
    
    # Advertencias amigables
    WARNINGS = {
        "escaneo_red": (
            "📌 Nota: Escanear redes que no te pertenecen puede ser ilegal. "
            "Asegúrate de tener permiso antes de continuar."
        ),
        "requiere_sudo": (
            "🔒 Esta acción requiere permisos de administrador (sudo). "
            "Si no tienes estos permisos, la operación no se podrá completar."
        ),
        "puede_ser_lento": (
            "⏱️  Esta operación puede tardar varios minutos. Ten paciencia."
        ),
        "trafico_red": (
            "📡 Capturar tráfico puede generar archivos grandes. "
            "Asegúrate de tener suficiente espacio en disco."
        ),
    }
    
    # Sugerencias de uso
    SUGGESTIONS = [
        "Intenta: 'Escanea mi red local'",
        "Intenta: 'Captura 100 paquetes en wlan0'",
        "Intenta: 'Busca información de google.com'",
        "Intenta: 'Analiza los logs de autenticación'",
        "Intenta: 'Muestra las herramientas disponibles'",
    ]
    
    # Mensajes de error amigables
    ERROR_MESSAGES = {
        "comando_no_entendido": (
            "No estoy seguro de qué quieres hacer. ¿Podrías reformular tu solicitud? "
            "Escribe 'help' para ver ejemplos."
        ),
        "permisos_insuficientes": (
            "No tengo los permisos necesarios para hacer eso. "
            "¿Podrías ejecutar este programa con sudo?"
        ),
        "herramienta_no_instalada": (
            "Parece que falta instalar una herramienta necesaria en tu sistema. "
            "Te mostraré cómo instalarla."
        ),
        "red_no_disponible": (
            "No puedo acceder a la red. Verifica tu conexión a Internet."
        ),
    }
    
    # Instrucciones paso a paso
    TUTORIALS = {
        "primer_uso": [
            "1. Primero, te recomiendo ejecutar 'tools' para ver qué puedo hacer",
            "2. Luego, prueba con un escaneo simple de tu red local",
            "3. Si encuentro algo, te explicaré qué significa en términos sencillos",
            "4. Todas tus acciones quedan registradas para consulta posterior",
        ],
        "escanear_red": [
            "1. Necesito saber qué dispositivo escanear (una IP como 192.168.1.1)",
            "2. Elegiré el tipo de escaneo más apropiado",
            "3. Te pediré confirmación antes de empezar",
            "4. El escaneo puede tardar unos minutos",
            "5. Te mostraré los resultados de forma clara y comprensible",
        ],
    }
    
    @staticmethod
    def get_explanation(topic: str) -> str:
        """Obtiene una explicación amigable de un tema"""
        return UserPrompts.EXPLANATIONS.get(topic, 
            "Concepto de ciberseguridad que ayuda a proteger sistemas y datos.")
    
    @staticmethod
    def get_warning(warning_type: str) -> str:
        """Obtiene una advertencia específica"""
        return UserPrompts.WARNINGS.get(warning_type, "⚠️  Procede con precaución.")
    
    @staticmethod
    def get_tutorial(tutorial_name: str) -> list:
        """Obtiene un tutorial paso a paso"""
        return UserPrompts.TUTORIALS.get(tutorial_name, ["Consulta 'help' para más información"])
