"""
Terminal personalizada basada en CAI CLI
Extiende la funcionalidad de cai.cli con características personalizadas
Implementa un loop personalizado que intercepta comandos antes de CAI
"""

import os
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from math import inf

# Importar componentes de CAI
from cai.sdk.agents import Agent, Runner
from cai.util import COST_TRACKER

# Importar nuestras utilidades
from ..ui.cli_interface import CLI
from ..core.permissions import PermissionChecker


class CustomCAITerminal:
    """
    Terminal personalizada que REEMPLAZA el CLI de CAI con uno propio.
    Maneja comandos personalizados y luego envía queries al agente de CAI.
    """
    
    def __init__(self, agent: Agent, show_custom_banner: bool = True, 
                 show_permissions: bool = True, custom_commands: Dict[str, callable] = None):
        """
        Inicializa la terminal personalizada.
        
        Args:
            agent: Agente de CAI a usar
            show_custom_banner: Mostrar nuestro banner personalizado
            show_permissions: Mostrar estado de permisos
            custom_commands: Diccionario de comandos personalizados {nombre: función}
        """
        self.agent = agent
        self.show_custom_banner = show_custom_banner
        self.show_permissions = show_permissions
        self.custom_commands = custom_commands or {}
        self.context_variables = {}
        self.turn_count = 0
        
    def display_startup_info(self):
        """Muestra información inicial personalizada"""
        if self.show_custom_banner:
            CLI.print_banner()
        
        if self.show_permissions:
            perm_status = PermissionChecker.check_and_warn()
            if perm_status['warnings']:
                for warning in perm_status['warnings']:
                    CLI.print_warning(warning)
                print()
            elif perm_status['is_root']:
                CLI.print_success("✓ Ejecutando con privilegios completos")
                print()
    
    def display_help(self):
        """Muestra ayuda personalizada"""
        print("\n" + "="*70)
        print("📚 AYUDA DEL TERMINAL PERSONALIZADO")
        print("="*70)
        
        # Comandos personalizados
        print("\n🟢 Comandos Personalizados:")
        print("  /help, /ayuda   - Mostrar esta ayuda")
        print("  /permisos       - Ver estado de permisos del sistema")
        print("  /tools          - Listar herramientas disponibles")
        print("  /examples       - Ver ejemplos de uso")
        print("  /status         - Estado del sistema y sesión")
        print("  /clear          - Limpiar pantalla")
        print("  /cost           - Ver costos de API")
        print("  /exit, /quit    - Salir")
        
        if self.custom_commands:
            print("\n🔵 Comandos Adicionales:")
            for cmd_name, cmd_func in self.custom_commands.items():
                doc = (cmd_func.__doc__ or "Sin descripción").strip().split('\n')[0]
                print(f"  /{cmd_name:<15} - {doc}")
        
        # Herramientas disponibles
        print("\n🛠️  Herramientas Disponibles:")
        print("  Solo pregunta al agente y él usará las herramientas necesarias:")
        print("  • 'escanea 192.168.1.1'")
        print("  • 'captura 10 paquetes en eth0'")
        print("  • 'busca información de google.com'")
        print("  • 'analiza el log /var/log/syslog'")
        
        print("\n💡 Tips:")
        print("  • Habla naturalmente con el agente")
        print("  • El agente pedirá confirmación antes de acciones sensibles")
        print("  • Todos los comandos empiezan con /")
        
        print("\n" + "="*70 + "\n")
    
    def handle_custom_command(self, user_input: str) -> Optional[bool]:
        """
        Maneja comandos personalizados.
        
        Args:
            user_input: Input del usuario
            
        Returns:
            True si se manejó el comando, False si debe pasarse al agente, None si debe salir
        """
        cmd = user_input.strip().lower()
        
        # Comandos de salida
        if cmd in ['/exit', '/quit', '/salir']:
            return None
        
        # Ayuda
        if cmd in ['/ayuda', '/help']:
            self.display_help()
            return True
        
        # Limpiar pantalla
        if cmd == '/clear':
            CLI.clear_screen()
            return True
        
        # Permisos
        if cmd in ['/permisos', '/permissions', '/perms']:
            PermissionChecker.show_permission_status()
            return True
        
        # Estado
        if cmd in ['/status', '/estado']:
            self.display_status()
            return True
        
        # Costos
        if cmd == '/cost':
            self.display_costs()
            return True
        
        # Tools
        if cmd in ['/tools', '/herramientas']:
            self.display_tools()
            return True
        
        # Examples
        if cmd in ['/examples', '/ejemplos']:
            self.display_examples()
            return True
        
        # Comandos personalizados adicionales
        for cmd_name, cmd_func in self.custom_commands.items():
            if cmd == f'/{cmd_name}':
                try:
                    cmd_func()
                except Exception as e:
                    CLI.print_error(f"Error ejecutando comando: {e}")
                return True
        
        # No es un comando personalizado, enviar al agente
        return False
    
    def display_status(self):
        """Muestra el estado actual del sistema"""
        print("\n" + "="*70)
        print("📊 ESTADO DEL SISTEMA")
        print("="*70)
        
        is_root = PermissionChecker.is_root()
        can_capture = PermissionChecker.can_capture_packets()[0]
        
        print(f"\n👤 Usuario: {os.getenv('USER', 'unknown')}")
        print(f"🔐 Privilegios: {'ROOT' if is_root else 'Usuario normal'}")
        print(f"📡 Captura de paquetes: {'✓ Disponible' if can_capture else '✗ No disponible'}")
        
        agent_name = getattr(self.agent, 'name', 'Unknown')
        print(f"\n🤖 Agente activo: {agent_name}")
        print(f"🔄 Turnos ejecutados: {self.turn_count}")
        
        if hasattr(self.agent, 'tools') and self.agent.tools:
            tool_count = len(self.agent.tools)
            print(f"🛠️  Herramientas: {tool_count} registradas")
        
        print("\n" + "="*70 + "\n")
    
    def display_costs(self):
        """Muestra costos de API"""
        try:
            total_cost = COST_TRACKER.get_total_cost()
            print(f"\n💰 Costo total de la sesión: ${total_cost:.6f}\n")
        except Exception as e:
            CLI.print_warning(f"No se pudieron obtener los costos: {e}")
    
    def display_tools(self):
        """Lista herramientas disponibles"""
        print("\n🛠️  HERRAMIENTAS DE CIBERSEGURIDAD\n")
        print("="*70)
        tools = [
            ("network_sniffer", "Captura de paquetes de red", "Requiere sudo"),
            ("nmap_scan", "Escaneo de puertos y servicios", "Básico: no sudo"),
            ("nmap_ping_sweep", "Descubrimiento de hosts", "No requiere sudo"),
            ("whois_lookup", "Información de dominios", "No requiere sudo"),
            ("dns_lookup", "Resolución DNS", "No requiere sudo"),
            ("reverse_dns", "DNS inverso", "No requiere sudo"),
            ("analyze_log", "Análisis de logs", "Logs sistema: sudo"),
            ("tail_log", "Monitoreo de logs", "Logs sistema: sudo"),
        ]
        
        for name, desc, perm in tools:
            print(f"• {name:<20} - {desc:<35} ({perm})")
        
        print("\n💡 Pregunta al agente para usarlas!")
        print("   Ejemplo: 'escanea 192.168.1.1 con nmap'\n")
    
    def display_examples(self):
        """Muestra ejemplos de uso"""
        print("\n💡 EJEMPLOS DE USO\n")
        print("="*70)
        print("\n1️⃣  Escaneo de red:")
        print("   🤖 > escanea 192.168.1.1")
        print("   🤖 > haz un escaneo completo de 192.168.1.0/24")
        
        print("\n2️⃣  Información de dominio:")
        print("   🤖 > busca información whois de google.com")
        print("   🤖 > qué IP tiene example.com")
        
        print("\n3️⃣  Captura de tráfico:")
        print("   🤖 > captura 20 paquetes en eth0")
        print("   🤖 > analiza el tráfico de la red")
        
        print("\n4️⃣  Análisis de logs:")
        print("   🤖 > analiza /var/log/auth.log buscando intentos fallidos")
        print("   🤖 > muestra las últimas 50 líneas de syslog")
        
        print("\n" + "="*70 + "\n")
    
    def get_user_input(self) -> Optional[str]:
        """Obtiene input del usuario con prompt personalizado"""
        try:
            prompt = CLI.color_text("🤖 dui-IA > ", 'cyan', bold=True)
            user_input = input(prompt).strip()
            return user_input
        except EOFError:
            return None
        except KeyboardInterrupt:
            print()  # Nueva línea
            return None
    
    def run_agent_query(self, query: str):
        """Ejecuta una consulta en el agente de CAI"""
        try:
            # Ejecutar query usando Runner (método estático)
            print()  # Línea en blanco antes de la respuesta
            
            response = Runner.run_sync(
                starting_agent=self.agent,
                input=query,
                context=self.context_variables,
                max_turns=20  # Permitir múltiples turnos para tool calls
            )
            
            # Mostrar respuesta
            # El resultado tiene una estructura específica de CAI
            if hasattr(response, 'messages') and response.messages:
                for message in response.messages:
                    if hasattr(message, 'content') and message.content:
                        print(message.content)
            elif hasattr(response, 'output') and response.output:
                print(response.output)
            else:
                # Fallback: intentar convertir a string
                print(str(response))
            
            print()  # Línea en blanco después de la respuesta
            
            # Actualizar contexto si es necesario
            if hasattr(response, 'context'):
                self.context_variables = response.context or {}
                
        except Exception as e:
            CLI.print_error(f"Error al ejecutar consulta: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self, max_turns: float = inf):
        """
        Ejecuta el loop principal de la terminal personalizada.
        
        Args:
            max_turns: Número máximo de turnos
        """
        # Mostrar información inicial
        self.display_startup_info()
        
        print("\n💡 Escribe /help para ver comandos disponibles")
        print("💡 Escribe /exit para salir\n")
        
        # Loop principal
        while self.turn_count < max_turns:
            # Obtener input del usuario
            user_input = self.get_user_input()
            
            if user_input is None:
                break
            
            if not user_input:
                continue
            
            # Manejar comando personalizado
            result = self.handle_custom_command(user_input)
            
            if result is None:  # Salir
                break
            elif result is True:  # Comando manejado
                continue
            
            # No es comando, enviar al agente
            self.run_agent_query(user_input)
            self.turn_count += 1
        
        # Mensaje de despedida
        print("\n" + "="*70)
        CLI.print_success("¡Hasta pronto! Sesión finalizada")
        
        # Mostrar estadísticas finales
        try:
            total_cost = COST_TRACKER.get_total_cost()
            print(f"💰 Costo total: ${total_cost:.6f}")
        except:
            pass
        
        print("="*70 + "\n")


def run_custom_cai_terminal(agent: Agent, **kwargs):
    """
    Función de conveniencia para ejecutar la terminal personalizada.
    
    Args:
        agent: Agente de CAI a usar
        **kwargs: Argumentos adicionales para CustomCAITerminal
    """
    terminal = CustomCAITerminal(agent, **kwargs)
    terminal.run()


# Ejemplo de cómo agregar comandos personalizados
def create_cybersecurity_commands():
    """Crea un diccionario de comandos personalizados para ciberseguridad"""
    
    def cmd_tools():
        """Lista todas las herramientas disponibles"""
        from ..core.tool_manager import ToolManager
        # Aquí podrías mostrar una tabla de herramientas
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
