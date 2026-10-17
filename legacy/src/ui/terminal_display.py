"""
Funciones de presentación y display para la terminal personalizada
Maneja toda la salida visual de la terminal
"""

import os
from cai.util import COST_TRACKER
from ..ui.cli_interface import CLI
from ..core.permissions import PermissionChecker


def display_startup_info(show_custom_banner: bool = True, show_permissions: bool = True):
    """Muestra información inicial personalizada"""
    if show_custom_banner:
        CLI.print_banner()
    
    if show_permissions:
        perm_status = PermissionChecker.check_and_warn()
        if perm_status['warnings']:
            for warning in perm_status['warnings']:
                CLI.print_warning(warning)
            print()
        elif perm_status['is_root']:
            CLI.print_success("✓ Ejecutando con privilegios completos")
            print()


def display_help(custom_commands: dict = None):
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
    print("\n🔄 Gestión de Sesiones:")
    print("  /sessions       - Listar sesiones guardadas")
    print("  /load <id>      - Reanudar una sesión anterior")
    print("  /search <texto> - Buscar sesiones por contenido")
    print("  /history        - Ver historial de la sesión actual")
    print("  /info           - Información de la sesión actual")
    print("\n🚪 Salir:")
    print("  /exit, /quit    - Salir")
    
    if custom_commands:
        print("\n🔵 Comandos Adicionales:")
        for cmd_name, cmd_func in custom_commands.items():
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


def display_status(agent, turn_count: int):
    """Muestra el estado actual del sistema"""
    print("\n" + "="*70)
    print("📊 ESTADO DEL SISTEMA")
    print("="*70)
    
    is_root = PermissionChecker.is_root()
    can_capture = PermissionChecker.can_capture_packets()[0]
    
    print(f"\n👤 Usuario: {os.getenv('USER', 'unknown')}")
    print(f"🔐 Privilegios: {'ROOT' if is_root else 'Usuario normal'}")
    print(f"📡 Captura de paquetes: {'✓ Disponible' if can_capture else '✗ No disponible'}")
    
    agent_name = getattr(agent, 'name', 'Unknown')
    print(f"\n🤖 Agente activo: {agent_name}")
    print(f"🔄 Turnos ejecutados: {turn_count}")
    
    if hasattr(agent, 'tools') and agent.tools:
        tool_count = len(agent.tools)
        print(f"🛠️  Herramientas: {tool_count} registradas")
    
    print("\n" + "="*70 + "\n")


def display_costs():
    """Muestra costos de API con explicación del cálculo"""
    try:
        print("\n" + "="*70)
        print("💰 COSTOS DE LA SESIÓN")
        print("="*70)
        
        # Costo total
        total_cost = COST_TRACKER.session_total_cost
        print(f"\n💵 Costo total: ${total_cost:.6f}")
        
        # Detalles de tokens
        input_tokens = COST_TRACKER.interaction_input_tokens
        output_tokens = COST_TRACKER.interaction_output_tokens
        reasoning_tokens = COST_TRACKER.interaction_reasoning_tokens
        
        if input_tokens > 0 or output_tokens > 0:
            print(f"\n📊 Tokens de última interacción:")
            print(f"   • Entrada:      {input_tokens:,} tokens")
            print(f"   • Salida:       {output_tokens:,} tokens")
            if reasoning_tokens > 0:
                print(f"   • Razonamiento: {reasoning_tokens:,} tokens")
            print(f"   • Total:        {input_tokens + output_tokens + reasoning_tokens:,} tokens")
        
        # Explicación del cálculo
        print(f"\n📋 Cómo se calcula:")
        print(f"   Costo = (tokens_entrada × precio_entrada) +")
        print(f"           (tokens_salida × precio_salida)")
        print(f"\n   • Los precios se obtienen de LiteLLM o pricing.json local")
        print(f"   • Se acumula el costo de cada interacción en la sesión")
        print(f"   • Modelos locales/gratuitos muestran $0.00")
        
        if total_cost == 0:
            print(f"\n💡 Nota: El costo es $0 porque:")
            print(f"   • Estás usando un modelo local/gratuito, o")
            print(f"   • No se han registrado interacciones con la API aún")
        
        print("\n" + "="*70 + "\n")
    except Exception as e:
        CLI.print_warning(f"No se pudieron obtener los costos: {e}")


def display_tools():
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


def display_examples():
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


def display_goodbye():
    """Muestra mensaje de despedida"""
    print("\n" + "="*70)
    CLI.print_success("¡Hasta pronto! Sesión finalizada")
    
    # Mostrar estadísticas finales
    try:
        total_cost = COST_TRACKER.session_total_cost
        print(f"💰 Costo total: ${total_cost:.6f}")
    except:
        pass
    
    print("="*70 + "\n")
