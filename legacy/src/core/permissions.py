"""
Utilidad para verificar y manejar permisos del sistema
"""

import os
import subprocess
from typing import Tuple, Optional


class PermissionChecker:
    """
    Verifica permisos del sistema y proporciona información clara sobre qué acciones requieren sudo.
    """
    
    @staticmethod
    def is_root() -> bool:
        """Verifica si el programa se ejecuta como root/sudo"""
        return os.geteuid() == 0
    
    @staticmethod
    def can_capture_packets() -> Tuple[bool, str]:
        """
        Verifica si se pueden capturar paquetes de red.
        
        Returns:
            (puede_capturar, mensaje_explicativo)
        """
        if PermissionChecker.is_root():
            return True, "✅ Permisos suficientes para captura de paquetes"
        
        # Verificar si el usuario está en grupo necesario
        try:
            result = subprocess.run(['groups'], capture_output=True, text=True)
            groups = result.stdout.lower()
            
            if 'wireshark' in groups or 'pcap' in groups:
                return True, "✅ Usuario en grupo adecuado para captura"
        except:
            pass
        
        return False, "⚠️  Se requiere sudo para captura de paquetes"
    
    @staticmethod
    def can_read_file(filepath: str) -> Tuple[bool, str]:
        """
        Verifica si se puede leer un archivo.
        
        Returns:
            (puede_leer, mensaje_explicativo)
        """
        if not os.path.exists(filepath):
            return False, f"❌ Archivo no existe: {filepath}"
        
        if os.access(filepath, os.R_OK):
            return True, "✅ Permisos de lectura OK"
        
        return False, f"⚠️  Sin permisos de lectura para: {filepath}"
    
    @staticmethod
    def get_permission_advice(tool_name: str) -> str:
        """
        Proporciona consejos sobre permisos para herramientas específicas.
        
        Args:
            tool_name: Nombre de la herramienta
            
        Returns:
            Mensaje con consejos
        """
        advice = {
            'network_sniffer': """
🔒 CAPTURA DE PAQUETES - Requiere permisos especiales

❓ ¿Por qué se necesita sudo?
   La captura de paquetes requiere acceso a "raw sockets" del kernel.
   Esto permite leer TODOS los paquetes de la red, no solo los de tu app.

🛡️  Razón de seguridad:
   Sin esta protección, cualquier programa podría espiar tu tráfico:
   • Contraseñas que envías
   • Datos bancarios  
   • Conversaciones privadas

💡 OPCIONES:

1️⃣  Ejecutar con sudo (RECOMENDADO):
   sudo python main.py

2️⃣  Agregar tu usuario al grupo wireshark:
   sudo usermod -a -G wireshark $USER
   newgrp wireshark

3️⃣  Usar tcpdump (ya tiene permisos):
   tcpdump -i eth0 -c 10 -w captura.pcap
""",
            'analyze_log': """
🔒 ANÁLISIS DE LOGS DEL SISTEMA - Requiere permisos especiales

❓ ¿Por qué se necesita sudo?
   Los archivos en /var/log/ tienen permisos restrictivos:
   • Solo root puede leer /var/log/auth.log
   • Solo root y grupo 'adm' pueden leer /var/log/syslog
   • Contienen información sensible del sistema

🛡️  Razón de seguridad:
   Estos logs contienen:
   • Intentos de login (exitosos y fallidos)
   • Comandos ejecutados con sudo
   • Información de servicios del sistema

💡 OPCIONES:

1️⃣  Para logs del sistema:
   sudo python main.py

2️⃣  Agregar usuario al grupo adm:
   sudo usermod -a -G adm $USER
   newgrp adm

3️⃣  Para tus propios logs:
   NO se necesita sudo para logs en /tmp, /home/usuario, etc.
""",
            'tail_log': """
🔒 MONITOREO DE LOGS - Puede requerir permisos

📄 LOGS QUE REQUIEREN SUDO:
   • /var/log/auth.log
   • /var/log/syslog
   • /var/log/kern.log
   • /var/log/apache2/*

📄 LOGS QUE NO REQUIEREN SUDO:
   • Archivos en /home/usuario
   • Archivos en /tmp
   • Logs de tus aplicaciones

💡 SOLUCIÓN:
   sudo python main.py  (solo si necesitas logs del sistema)
""",
            'nmap_stealth': """
🔒 ESCANEO NMAP STEALTH - Requiere permisos especiales

❓ ¿Por qué se necesita sudo?
   Los escaneos SYN (stealth) envían paquetes TCP especiales:
   • No completan el handshake TCP
   • Construyen paquetes personalizados
   • Requieren raw sockets como la captura de paquetes

🎭 ¿Por qué se llama "stealth"?
   • Más difícil de detectar que un escaneo normal
   • No queda registrado en logs de conexión completa
   • Usado para pentesting y auditorías de seguridad

💡 OPCIONES:

1️⃣  Usar escaneo básico (NO requiere sudo):
   python main.py
   Elegir tipo: "basic" o "service"

2️⃣  Para scans avanzados:
   sudo python main.py
   Elegir tipo: "stealth"
"""
        }
        
        return advice.get(tool_name, """
ℹ️  Esta herramienta puede requerir permisos especiales dependiendo 
   de la operación específica que se realice.
""")
    
    @staticmethod
    def suggest_solution(operation: str) -> str:
        """
        Sugiere solución cuando falta permiso.
        
        Args:
            operation: Tipo de operación (capture, read_log, scan)
            
        Returns:
            Mensaje con solución sugerida
        """
        solutions = {
            'capture': """
💡 SOLUCIÓN RÁPIDA:
   Ejecuta: sudo python main.py
   
   Luego selecciona la opción de captura de paquetes.
""",
            'read_log': """
💡 SOLUCIÓN RÁPIDA:
   Para logs del sistema: sudo python main.py
   Para logs de usuario: No se requiere sudo
   
   Archivos típicos que requieren sudo:
   • /var/log/auth.log
   • /var/log/syslog
   • /var/log/kern.log
""",
            'scan': """
💡 SOLUCIÓN RÁPIDA:
   Para scans básicos: NO se necesita sudo
   Para scans avanzados (SYN, stealth): sudo python main.py
"""
        }
        
        return solutions.get(operation, "💡 Ejecuta: sudo python main.py")
    
    @staticmethod
    def check_and_warn() -> dict:
        """
        Verifica permisos actuales y genera reporte.
        
        Returns:
            Diccionario con estado de permisos
        """
        status = {
            'is_root': PermissionChecker.is_root(),
            'can_capture': PermissionChecker.can_capture_packets()[0],
            'warnings': []
        }
        
        if not status['is_root']:
            status['warnings'].append(
                "⚠️  No estás ejecutando como root. Algunas herramientas pueden fallar."
            )
        
        if not status['can_capture']:
            status['warnings'].append(
                "⚠️  No puedes capturar paquetes. Usa 'sudo python main.py' si lo necesitas."
            )
        
        return status
    
    @staticmethod
    def show_permission_status():
        """Muestra el estado actual de permisos de forma amigable"""
        print("\n" + "="*70)
        print("🔒 ESTADO DE PERMISOS DEL SISTEMA")
        print("="*70 + "\n")
        
        status = PermissionChecker.check_and_warn()
        
        # Usuario actual
        import getpass
        username = getpass.getuser()
        print(f"👤 Usuario actual: {username}")
        
        # Root status
        if status['is_root']:
            print("🔓 Privilegios: ROOT (superusuario)")
            print("   ✅ Puedes ejecutar TODAS las herramientas")
        else:
            print("👤 Privilegios: Usuario normal")
            print("   ℹ️  Algunas herramientas pueden requerir sudo")
        
        print()
        
        # Capacidades específicas
        can_capture, capture_msg = PermissionChecker.can_capture_packets()
        print(f"📡 Captura de paquetes: {capture_msg}")
        
        # Logs comunes
        common_logs = ['/var/log/auth.log', '/var/log/syslog']
        print(f"\n📄 Acceso a logs del sistema:")
        for log in common_logs:
            can_read, read_msg = PermissionChecker.can_read_file(log)
            status_icon = "✅" if can_read else "⚠️ "
            print(f"   {status_icon} {log}")
        
        # Advertencias
        if status['warnings']:
            print("\n" + "-"*70)
            print("⚠️  ADVERTENCIAS:")
            for warning in status['warnings']:
                print(f"   {warning}")
        
        # Consejos
        if not status['is_root']:
            print("\n" + "-"*70)
            print("💡 CONSEJOS:")
            print("   • Para herramientas que requieren permisos: sudo python main.py")
            print("   • Para consultas básicas (WHOIS, DNS): No se necesita sudo")
            print("   • Para escaneos nmap básicos: No se necesita sudo")
        
        print("\n" + "="*70 + "\n")


# Funciones auxiliares para usar en las herramientas

def require_root(tool_name: str) -> Optional[str]:
    """
    Verifica si se ejecuta como root, retorna mensaje de error si no.
    
    Args:
        tool_name: Nombre de la herramienta que requiere root
        
    Returns:
        None si OK, mensaje de error si falta permiso
    """
    if not PermissionChecker.is_root():
        return f"""❌ Error: Esta herramienta requiere privilegios de root/sudo

{PermissionChecker.get_permission_advice(tool_name)}

{PermissionChecker.suggest_solution('capture')}
"""
    return None


def check_file_readable(filepath: str) -> Optional[str]:
    """
    Verifica si un archivo es legible, retorna mensaje si no.
    
    Args:
        filepath: Ruta del archivo a verificar
        
    Returns:
        None si OK, mensaje de error si no se puede leer
    """
    can_read, msg = PermissionChecker.can_read_file(filepath)
    
    if not can_read:
        return f"""{msg}

{PermissionChecker.suggest_solution('read_log')}
"""
    return None
