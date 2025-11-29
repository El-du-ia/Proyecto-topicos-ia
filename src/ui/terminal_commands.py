"""
Manejador de comandos de la terminal personalizada
Enruta y procesa todos los comandos del usuario
"""

from typing import Optional, Dict, Any, Callable

from ..ui.cli_interface import CLI
from ..ui import terminal_display
from ..core.permissions import PermissionChecker


class CommandHandler:
    """Manejador centralizado de comandos de terminal"""
    
    def __init__(self, agent, session_commands, custom_commands: Dict[str, Callable] = None):
        """
        Inicializa el manejador de comandos.
        
        Args:
            agent: Agente de CAI
            session_commands: Instancia de SessionCommands
            custom_commands: Diccionario de comandos personalizados adicionales
        """
        self.agent = agent
        self.session_commands = session_commands
        self.custom_commands = custom_commands or {}
    
    def handle_command(self, user_input: str) -> Optional[bool]:
        """
        Maneja comandos personalizados.
        
        Args:
            user_input: Input del usuario
            
        Returns:
            True si se manejó el comando
            False si debe pasarse al agente
            None si debe salir
        """
        cmd = user_input.strip()
        cmd_lower = cmd.lower()
        
        # Comandos de salida
        if cmd_lower in ['/exit', '/quit', '/salir']:
            return None
        
        # Ayuda
        if cmd_lower in ['/ayuda', '/help']:
            terminal_display.display_help(self.custom_commands)
            return True
        
        # Limpiar pantalla
        if cmd_lower == '/clear':
            CLI.clear_screen()
            return True
        
        # Permisos
        if cmd_lower in ['/permisos', '/permissions', '/perms']:
            PermissionChecker.show_permission_status()
            return True
        
        # Estado
        if cmd_lower in ['/status', '/estado']:
            terminal_display.display_status(self.agent, self.session_commands.turn_count)
            return True
        
        # Costos
        if cmd_lower == '/cost':
            terminal_display.display_costs()
            return True
        
        # Tools
        if cmd_lower in ['/tools', '/herramientas']:
            terminal_display.display_tools()
            return True
        
        # Examples
        if cmd_lower in ['/examples', '/ejemplos']:
            terminal_display.display_examples()
            return True
        
        # === COMANDOS DE SESIONES ===
        
        # Listar sesiones
        if cmd_lower in ['/sessions', '/sesiones']:
            self.session_commands.display_sessions()
            return True
        
        # Cargar sesión
        if cmd_lower.startswith('/load '):
            session_id = cmd[6:].strip()
            self.session_commands.load_session_command(session_id)
            return True
        
        # Buscar sesiones
        if cmd_lower.startswith('/search '):
            query = cmd[8:].strip()
            self.session_commands.search_sessions_command(query)
            return True
        
        # Ver historial actual
        if cmd_lower in ['/history', '/historial']:
            self.session_commands.display_current_history()
            return True
        
        # Info de sesión actual
        if cmd_lower in ['/info', '/session', '/sesion']:
            self.session_commands.display_session_info()
            return True
        
        # Comandos personalizados adicionales
        for cmd_name, cmd_func in self.custom_commands.items():
            if cmd_lower == f'/{cmd_name}':
                try:
                    cmd_func()
                except Exception as e:
                    CLI.print_error(f"Error ejecutando comando: {e}")
                return True
        
        # No es un comando personalizado, enviar al agente
        return False


# Funciones de conveniencia para crear comandos personalizados

def create_cybersecurity_commands():
    """Crea un diccionario de comandos personalizados para ciberseguridad"""
    
    def cmd_tools():
        """Lista todas las herramientas disponibles"""
        print("\n🛠️  Herramientas de Ciberseguridad disponibles:")
        print("  • network_sniffer - Captura de paquetes")
        print("  • nmap_scan - Escaneo de red")
        print("  • whois_lookup - Información de dominios")
        print("  • analyze_log - Análisis de logs")
        print("\nPregunta al agente para usarlas!\n")
    
    def cmd_examples():
        """Muestra ejemplos de uso"""
        print("\n💡 EJEMPLOS DE USO:")
        print("="*70)
        print("\n1. Escaneo de red:")
        print("   'escanea 192.168.1.1 con nmap básico'")
        print("\n2. Información de dominio:")
        print("   'busca información whois de google.com'")
        print("\n3. Captura de tráfico:")
        print("   'captura 20 paquetes en la interfaz eth0'")
        print("\n4. Análisis de logs:")
        print("   'analiza el log /var/log/auth.log buscando errores'")
        print("\n" + "="*70 + "\n")
    
    def cmd_perms():
        """Muestra guía de permisos"""
        PermissionChecker.show_permission_status()
        print("\n💡 Para más información: python demo_permisos.py\n")
    
    return {
        'tools': cmd_tools,
        'examples': cmd_examples,
        'perms': cmd_perms,
    }
