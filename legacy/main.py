#!/usr/bin/env python3
"""
AGENTE INTELIGENTE DE CIBERSEGURIDAD
Punto de entrada principal del sistema

Fase 1 - MVP:
- Ejecuta herramientas de CAI y personalizadas
- Solicita confirmación para acciones sensibles
- Traduce resultados técnicos a lenguaje simple
- Registra todas las acciones

Uso:
    python main.py
    sudo python main.py  (para herramientas que requieren privilegios)
"""

import sys
import os

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.agent_controller import CybersecurityAgent
from src.core.tool_manager import ToolManager
from src.core.interpreter import ResultInterpreter
from src.core.permissions import PermissionChecker
from src.ui.cli_interface import CLI
from src.ui.prompts import UserPrompts
from src.ui.custom_terminal import run_custom_cai_terminal
from src.ui.terminal_commands import create_cybersecurity_commands
from src.models.conversation_memory import ConversationMemory

# Importar herramientas personalizadas
from src.tools.cai_tools_wrapper import network_sniffer_tool
from src.tools.nmap_tool import nmap_scan_tool, nmap_ping_sweep
from src.tools.whois_tool import whois_lookup_tool, dns_lookup_tool, reverse_dns_lookup_tool
from src.tools.log_analyzer_tool import analyze_log_tool, tail_log_tool

from src.tools.report_generator_tool import generate_report_tool

from cai.agents.network_traffic_analyzer import network_security_analyzer_agent
from cai.cli import run_cai_cli


def setup_agent():
    """
    Configura el agente con todas las herramientas y extensiones.
    
    Returns:
        Tupla (agent_controller, tool_manager, interpreter, memory)
    """
    CLI.print_step(1, 4, "Inicializando controlador del agente...")
    controller = CybersecurityAgent(agent=network_security_analyzer_agent)
    
    CLI.print_step(2, 4, "Cargando herramientas personalizadas...")
    tool_manager = ToolManager(network_security_analyzer_agent)
    
    # Registrar herramientas personalizadas con metadatos
    tool_manager.register_tool(network_sniffer_tool, {
        "category": "network",
        "is_sensitive": True,
        "requires_root": True
    })
    
    tool_manager.register_tool(nmap_scan_tool, {
        "category": "network",
        "is_sensitive": True,
        "requires_root": False
    })
    
    tool_manager.register_tool(nmap_ping_sweep, {
        "category": "network",
        "is_sensitive": True,
        "requires_root": False
    })
    
    tool_manager.register_tool(whois_lookup_tool, {
        "category": "reconnaissance",
        "is_sensitive": False,
        "requires_root": False
    })
    
    tool_manager.register_tool(dns_lookup_tool, {
        "category": "reconnaissance",
        "is_sensitive": False,
        "requires_root": False
    })
    
    tool_manager.register_tool(reverse_dns_lookup_tool, {
        "category": "reconnaissance",
        "is_sensitive": False,
        "requires_root": False
    })
    
    tool_manager.register_tool(analyze_log_tool, {
        "category": "analysis",
        "is_sensitive": False,
        "requires_root": False
    })
    
    tool_manager.register_tool(tail_log_tool, {
        "category": "analysis",
        "is_sensitive": False,
        "requires_root": False
    })
    
    tool_manager.register_tool(generate_report_tool, {
        "category": "utility",
        "is_sensitive": False,
        "requires_root": False
    })

    CLI.print_step(3, 4, "Inicializando intérprete de resultados...")
    interpreter = ResultInterpreter()
    
    CLI.print_step(4, 4, "Configurando memoria conversacional...")
    memory = ConversationMemory(controller.session_id)
    
    CLI.print_success("Sistema inicializado correctamente\n")
    
    return controller, tool_manager, interpreter, memory


def show_main_menu(tool_manager: ToolManager):
    """Muestra el menú principal con opciones"""
    CLI.print_section_header("MENÚ PRINCIPAL", "🏠")
    
    print("Opciones disponibles:\n")
    print("  1️⃣  Iniciar chat interactivo con el agente")
    print("  2️⃣  Ver todas las herramientas disponibles")
    print("  3️⃣  Ver historial de sesión")
    print("  4️⃣  Ver estado de permisos del sistema")
    print("  5️⃣  Ver ayuda y ejemplos")
    print("  6️⃣  Salir\n")
    
    choice = CLI.prompt_input("Selecciona una opción", "1")
    return choice


def handle_quick_command(controller: CybersecurityAgent, tool_manager: ToolManager, 
                        interpreter: ResultInterpreter):
    """Maneja la ejecución de comandos rápidos"""
    CLI.print_section_header("COMANDO RÁPIDO", "⚡")
    
    print("Ejemplos de comandos:")
    for suggestion in UserPrompts.SUGGESTIONS[:5]:
        print(f"  • {suggestion}")
    print()
    
    command = CLI.prompt_input("Ingresa tu comando")
    
    if not command:
        CLI.print_warning("No se ingresó ningún comando")
        return
    
    CLI.print_info(f"Procesando: {command}")
    CLI.print_warning("Nota: En esta versión MVP, los comandos rápidos son limitados.")
    CLI.print_info("Para funcionalidad completa, usa el modo 'Chat interactivo' (opción 1)")


def show_session_history(controller: CybersecurityAgent):
    """Muestra el historial de la sesión actual"""
    CLI.print_section_header("HISTORIAL DE SESIÓN", "📜")
    
    summary = controller.get_session_summary()
    
    print(f"🆔 Session ID: {summary['session_id']}")
    print(f"⏱️  Inicio: {summary['start_time']}")
    print(f"📊 Total de acciones: {summary['total_actions']}")
    print(f"✅ Aprobaciones del usuario: {summary['user_approvals']}")
    print(f"❌ Rechazos del usuario: {summary['user_rejections']}")
    print(f"\n🛠️  Herramientas usadas:")
    
    if summary['tools_used']:
        for tool in summary['tools_used']:
            if tool:
                print(f"   • {tool}")
    else:
        print("   (Ninguna herramienta ejecutada aún)")
    
    print()


def run_interactive_mode(controller: CybersecurityAgent):
    """
    Ejecuta el modo interactivo usando el terminal personalizado basado en CAI.
    
    Este modo usa la terminal de CAI pero con personalizaciones:
    - Banner personalizado
    - Comandos adicionales (/permisos, /tools, /examples)
    - Verificación de permisos
    - Interfaz mejorada
    """
    CLI.print_section_header("MODO INTERACTIVO", "💬")
    
    print("Iniciando terminal personalizada basada en CAI...")
    print("El agente puede:")
    print("  • Ejecutar todas las herramientas disponibles")
    print("  • Solicitar confirmación para acciones sensibles")
    print("  • Explicar resultados en lenguaje simple")
    print("  • Responder preguntas sobre ciberseguridad\n")
    
    print("💡 Comandos especiales:")
    print("  /help, /ayuda   - Mostrar ayuda completa")
    print("  /permisos       - Ver estado de permisos del sistema")
    print("  /tools          - Listar herramientas disponibles")
    print("  /examples       - Ver ejemplos de uso")
    print("  /status         - Estado del sistema y sesión")
    print("  /exit, /quit    - Salir\n")
    
    CLI.print_warning(UserPrompts.get_warning("escaneo_red"))
    print()
    
    CLI.wait_for_key("Presiona Enter para iniciar la terminal")
    
    # IMPORTANTE: Suprimir el banner de CAI antes de iniciar
    os.environ['CAI_NO_BANNER'] = '1'
    
    try:
        # Modificar las instrucciones del agente para la Fase 1
        original_instructions = network_security_analyzer_agent.instructions
        
        def enhanced_instructions(context, agent):
            base_prompt = original_instructions(context, agent) if callable(original_instructions) else str(original_instructions)
            
            return base_prompt + """

INSTRUCCIONES ADICIONALES - Fase 1 MVP:

1. CONFIRMACIÓN ANTES DE EJECUTAR:
   - SIEMPRE pregunta al usuario antes de ejecutar herramientas sensibles
   - Explica claramente qué vas a hacer y cuáles son los riesgos
   - Espera confirmación explícita

2. EXPLICACIONES SIMPLES:
   - Traduce TODOS los resultados técnicos a lenguaje simple
   - Usa analogías y ejemplos del mundo real
   - Evita jerga técnica innecesaria
   - Explica qué significa cada hallazgo para la seguridad

3. REGISTRO DE ACCIONES:
   - Menciona que todas las acciones quedan registradas
   - Ofrece generar un reporte al final

4. HERRAMIENTAS DISPONIBLES:
   - network_sniffer_tool: Captura paquetes de red
   - nmap_scan_tool: Escanea puertos y servicios
   - nmap_ping_sweep: Descubre hosts activos
   - whois_lookup_tool: Consulta información de dominios
   - dns_lookup_tool: Resuelve nombres de dominio
   - reverse_dns_lookup_tool: DNS inverso
   - analyze_log_tool: Analiza archivos de log
   - tail_log_tool: Muestra últimas líneas de log

5. **GENERACIÓN AUTOMÁTICA DE REPORTES (CRÍTICO: FORMATO)**:
   - Si detectas el marcador `---REPORTE_REQUERIDO:ANALYSIS---`, debes hacer dos cosas:
     a) Primero, genera tu explicación SIMPLE para el usuario y pregúntale si desea el reporte completo.
     b) Si el usuario confirma, **DEBES GENERAR EL TEXTO COMPLETO DEL REPORTE PROFESIONAL** siguiendo estrictamente el siguiente PROMPT.

--- PROMPT PARA GENERACIÓN DE REPORTE TÉCNICO ---

Genera un Reporte Técnico de Análisis de Seguridad de Red completamente estructurado y profesional usando únicamente la información disponible en el contexto de la conversación (resultado crudo y tu análisis).
No inventes información; si un campo no aplica, indícalo como “No se encontraron datos relevantes”.

El reporte debe seguir exactamente esta estructura:

1. Resumen Ejecutivo
Explica, en lenguaje claro pero técnico:
– Qué se analizó
– Cuál era el objetivo
– Hallazgos principales
– Conclusión rápida sobre riesgos

2. Alcance del Análisis
Describe según los datos:
– Segmentos de red analizados
– Dispositivos involucrados
– Tiempo o duración de captura
– Herramientas utilizadas (solo las que realmente aparezcan)

3. Detalles Técnicos del Análisis
3.1 Captura de Tráfico
– Interfaz usada
– Cantidad de paquetes capturados
– Archivos generados
– Observaciones técnicas

3.2 Protocolos y Conversaciones
Para cada uno detectado: ICMP, ARP, TCP, UDP, etc.
– Volumen de tráfico
– Conversaciones principales
– Anomalías detectadas (si las hay)

3.3 Identificación y Perfilado de Dispositivos
De cada IP encontrada:
– Resultados de DNS Reverse
– Resultados de Nmap (puertos abiertos/cerrados/filtrados)
– Vendor MAC (si está presente)
– Hipótesis funcional (basada en comportamiento)

3.4 Comportamientos Destacados de Dispositivos
Describe comportamientos llamativos o fuera de patrón.
– Explica si el comportamiento es normal o sospechoso
– Incluye contexto del usuario (si está dentro de los datos)

4. Evaluación de Seguridad
– Riesgos detectados
– Actividades sospechosas o descartadas
– Evaluación general de postura de seguridad

5. Recomendaciones
Lista recomendaciones aplicables según el análisis:
– Configuración
– Monitoreo
– Endurecimiento
– Higiene de red

6. Conclusión Final
Una frase clara indicando:
– Si se detectó actividad maliciosa
– Estado general de seguridad
– Próximos pasos sugeridos

--- FIN DEL PROMPT ---

   c) **Llama a la herramienta** `generate_report_tool`. El parámetro `analysis_summary` debe contener **todo el texto** generado por el PROMPT anterior.

RECUERDA: Tu objetivo es hacer la ciberseguridad accesible para usuarios sin conocimientos técnicos.
"""
        
        network_security_analyzer_agent.instructions = enhanced_instructions
        
        # Crear comandos personalizados para la terminal
        custom_commands = create_cybersecurity_commands()
        
        # Ejecutar la terminal personalizada (basada en CAI pero mejorada)
        run_custom_cai_terminal(
            agent=network_security_analyzer_agent,
            show_custom_banner=False,  # Ya mostramos banner en main()
            show_permissions=False,     # Ya mostramos permisos en main()
            custom_commands=custom_commands
        )
        
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        CLI.print_info("Sesión interrumpida por el usuario")
    except Exception as e:
        CLI.print_error(f"Error durante la sesión: {e}")
    finally:
        print()


def main():
    """Función principal del programa - Inicia directamente en modo interactivo"""
    try:
        # Mostrar banner principal
        CLI.print_banner()
        
        # Verificar y mostrar estado de permisos
        perm_status = PermissionChecker.check_and_warn()
        if perm_status['warnings']:
            for warning in perm_status['warnings']:
                CLI.print_warning(warning)
            print()
        elif perm_status['is_root']:
            CLI.print_success("✓ Ejecutando con privilegios completos (root)")
            print()
        
        # Configurar agente
        controller, tool_manager, interpreter, memory = setup_agent()
        
        # Mostrar información del sistema
        CLI.print_section_header("AGENTE DE CIBERSEGURIDAD", "🤖")
        print("Este agente inteligente puede:")
        print("  • Escanear redes y hosts")
        print("  • Capturar y analizar tráfico")
        print("  • Consultar información de dominios")
        print("  • Analizar logs del sistema")
        print("  • Responder preguntas sobre ciberseguridad\n")
        
        print("💡 Comandos especiales disponibles:")
        print("  /help, /ayuda   - Mostrar ayuda completa")
        print("  /permisos       - Ver estado de permisos")
        print("  /tools          - Listar todas las herramientas")
        print("  /examples       - Ver ejemplos de uso")
        print("  /status         - Estado del sistema y sesión")
        print("  /cost           - Ver costos de API")
        print("  /exit, /quit    - Salir\n")
        
        # Mostrar advertencias si es necesario
        CLI.print_warning(UserPrompts.get_warning("escaneo_red"))
        print()
        
        CLI.wait_for_key("Presiona Enter para iniciar el agente")
        
        # IMPORTANTE: Suprimir el banner de CAI antes de iniciar
        os.environ['CAI_NO_BANNER'] = '1'
        
        try:
            # Modificar las instrucciones del agente para la Fase 1
            original_instructions = network_security_analyzer_agent.instructions
            
            def enhanced_instructions(context, agent):
                base_prompt = original_instructions(context, agent) if callable(original_instructions) else str(original_instructions)
                
                return base_prompt + """

INSTRUCCIONES ADICIONALES - Fase 1 MVP:

1. CONFIRMACIÓN ANTES DE EJECUTAR:
   - SIEMPRE pregunta al usuario antes de ejecutar herramientas sensibles
   - Explica claramente qué vas a hacer y cuáles son los riesgos
   - Espera confirmación explícita

2. EXPLICACIONES SIMPLES:
   - Traduce TODOS los resultados técnicos a lenguaje simple
   - Usa analogías y ejemplos del mundo real
   - Evita jerga técnica innecesaria
   - Explica qué significa cada hallazgo para la seguridad

3. REGISTRO DE ACCIONES:
   - Menciona que todas las acciones quedan registradas
   - Ofrece generar un reporte al final

4. HERRAMIENTAS DISPONIBLES:
   - network_sniffer_tool: Captura paquetes de red
   - nmap_scan_tool: Escanea puertos y servicios
   - nmap_ping_sweep: Descubre hosts activos
   - whois_lookup_tool: Consulta información de dominios
   - dns_lookup_tool: Resuelve nombres de dominio
   - reverse_dns_lookup_tool: DNS inverso
   - analyze_log_tool: Analiza archivos de log
   - tail_log_tool: Muestra últimas líneas de log

5. **GENERACIÓN AUTOMÁTICA DE REPORTES (CRÍTICO: FORMATO)**:
   - Si detectas el marcador `---REPORTE_REQUERIDO:ANALYSIS---`, debes hacer dos cosas:
     a) Primero, genera tu explicación SIMPLE para el usuario y pregúntale si desea el reporte completo.
     b) Si el usuario confirma, **DEBES GENERAR EL TEXTO COMPLETO DEL REPORTE PROFESIONAL** siguiendo estrictamente el siguiente PROMPT.

--- PROMPT PARA GENERACIÓN DE REPORTE TÉCNICO ---

Genera un Reporte Técnico de Análisis de Seguridad de Red completamente estructurado y profesional usando únicamente la información disponible en el contexto de la conversación (resultado crudo y tu análisis).
No inventes información; si un campo no aplica, indícalo como “No se encontraron datos relevantes”.

El reporte debe seguir exactamente esta estructura:

1. Resumen Ejecutivo
Explica, en lenguaje claro pero técnico:
– Qué se analizó
– Cuál era el objetivo
– Hallazgos principales
– Conclusión rápida sobre riesgos

2. Alcance del Análisis
Describe según los datos:
– Segmentos de red analizados
– Dispositivos involucrados
– Tiempo o duración de captura
– Herramientas utilizadas (solo las que realmente aparezcan)

3. Detalles Técnicos del Análisis
3.1 Captura de Tráfico
– Interfaz usada
– Cantidad de paquetes capturados
– Archivos generados
– Observaciones técnicas

3.2 Protocolos y Conversaciones
Para cada uno detectado: ICMP, ARP, TCP, UDP, etc.
– Volumen de tráfico
– Conversaciones principales
– Anomalías detectadas (si las hay)

3.3 Identificación y Perfilado de Dispositivos
De cada IP encontrada:
– Resultados de DNS Reverse
– Resultados de Nmap (puertos abiertos/cerrados/filtrados)
– Vendor MAC (si está presente)
– Hipótesis funcional (basada en comportamiento)

3.4 Comportamientos Destacados de Dispositivos
Describe comportamientos llamativos o fuera de patrón.
– Explica si el comportamiento es normal o sospechoso
– Incluye contexto del usuario (si está dentro de los datos)

4. Evaluación de Seguridad
– Riesgos detectados
– Actividades sospechosas o descartadas
– Evaluación general de postura de seguridad

5. Recomendaciones
Lista recomendaciones aplicables según el análisis:
– Configuración
– Monitoreo
– Endurecimiento
– Higiene de red

6. Conclusión Final
Una frase clara indicando:
– Si se detectó actividad maliciosa
– Estado general de seguridad
– Próximos pasos sugeridos

--- FIN DEL PROMPT ---

   c) **Llama a la herramienta** `generate_report_tool`. El parámetro `analysis_summary` debe contener **todo el texto** generado por el PROMPT anterior.

RECUERDA: Tu objetivo es hacer la ciberseguridad accesible para usuarios sin conocimientos técnicos.
"""
            
            network_security_analyzer_agent.instructions = enhanced_instructions
            
            # Crear comandos personalizados para la terminal
            custom_commands = create_cybersecurity_commands()
            
            # Ejecutar la terminal personalizada directamente
            run_custom_cai_terminal(
                agent=network_security_analyzer_agent,
                show_custom_banner=False,  # Ya mostramos el banner principal
                show_permissions=False,    # Ya mostramos permisos
                custom_commands=custom_commands
            )
            
        except KeyboardInterrupt:
            print("\n")
            CLI.print_info("Sesión interrumpida por el usuario")
        
        # Mostrar resumen final al salir
        summary = controller.get_session_summary()
        if summary['total_actions'] > 0:
            print("\n" + "="*70)
            CLI.print_section_header("RESUMEN DE SESIÓN", "📊")
            print(f"Total de acciones realizadas: {summary['total_actions']}")
            print(f"Herramientas utilizadas: {len(summary['tools_used'])}")
            if summary['tools_used']:
                print(f"Herramientas: {', '.join(summary['tools_used'])}")
            print(f"\n📁 Logs guardados en: logs/\n")
        
        CLI.print_success("¡Hasta pronto! Gracias por usar el Agente de Ciberseguridad")
    
    except Exception as e:
        CLI.print_error(f"Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
