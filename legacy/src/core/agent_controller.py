"""
AgentController: Coordina el flujo conversacional y la ejecución de herramientas
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from cai.sdk.agents import Agent
from cai.agents.network_traffic_analyzer import network_security_analyzer_agent
import json
import os


class CybersecurityAgent:
    """
    Controlador principal del agente inteligente de ciberseguridad.
    
    Responsabilidades:
    - Coordinar la conversación con el usuario
    - Decidir qué herramientas ejecutar
    - Solicitar confirmación para acciones sensibles
    - Registrar todas las interacciones
    """
    
    def __init__(self, agent: Optional[Agent] = None, log_dir: str = "logs"):
        """
        Inicializa el controlador del agente.
        
        Args:
            agent: Agente de CAI a utilizar (por defecto: network_security_analyzer_agent)
            log_dir: Directorio para guardar logs de sesión
        """
        self.agent = agent or network_security_analyzer_agent
        self.log_dir = log_dir
        self.session_id = self._generate_session_id()
        self.action_history: List[Dict[str, Any]] = []
        self.sensitive_commands = [
            'nmap', 'tcpdump', 'wireshark', 'metasploit', 
            'exploit', 'attack', 'scan', 'penetration'
        ]
        
        # Crear directorio de logs si no existe
        os.makedirs(log_dir, exist_ok=True)
        
        print(f"[*] Agente de Ciberseguridad iniciado")
        print(f"[*] Session ID: {self.session_id}")
        print(f"[*] Logs: {self.log_dir}/{self.session_id}.json\n")
    
    def _generate_session_id(self) -> str:
        """Genera un ID único para la sesión actual"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}"
    
    def is_sensitive_action(self, command: str, tool_name: str) -> bool:
        """
        Determina si una acción requiere confirmación del usuario.
        
        Args:
            command: Comando a ejecutar
            tool_name: Nombre de la herramienta
            
        Returns:
            True si la acción es sensible y requiere confirmación
        """
        command_lower = command.lower()
        
        # Verificar si contiene palabras clave sensibles
        for sensitive_word in self.sensitive_commands:
            if sensitive_word in command_lower:
                return True
        
        # Herramientas específicas que siempre requieren confirmación
        sensitive_tools = ['nmap_scan_tool', 'network_sniffer_tool', 'exploit_tool']
        if tool_name in sensitive_tools:
            return True
        
        return False
    
    def request_user_confirmation(self, action_description: str, risks: List[str]) -> bool:
        """
        Solicita confirmación del usuario antes de ejecutar una acción sensible.
        
        Args:
            action_description: Descripción de lo que se va a hacer
            risks: Lista de riesgos potenciales
            
        Returns:
            True si el usuario aprueba, False en caso contrario
        """
        print("\n" + "="*70)
        print("⚠️  CONFIRMACIÓN REQUERIDA")
        print("="*70)
        print(f"\n📋 Acción: {action_description}\n")
        
        if risks:
            print("⚠️  Riesgos potenciales:")
            for risk in risks:
                print(f"   • {risk}")
            print()
        
        while True:
            response = input("¿Deseas continuar con esta acción? [s/n]: ").lower().strip()
            if response in ['s', 'si', 'yes', 'y']:
                print("✅ Acción aprobada por el usuario\n")
                self._log_action("user_approval", {"action": action_description, "approved": True})
                return True
            elif response in ['n', 'no']:
                print("❌ Acción cancelada por el usuario\n")
                self._log_action("user_approval", {"action": action_description, "approved": False})
                return False
            else:
                print("Por favor responde 's' para sí o 'n' para no.")
    
    def execute_with_confirmation(self, tool_name: str, tool_args: Dict[str, Any], 
                                  description: str, risks: List[str]) -> Optional[Any]:
        """
        Ejecuta una herramienta con confirmación previa si es necesaria.
        
        Args:
            tool_name: Nombre de la herramienta
            tool_args: Argumentos para la herramienta
            description: Descripción de la acción
            risks: Lista de riesgos
            
        Returns:
            Resultado de la herramienta o None si fue cancelada
        """
        # Verificar si requiere confirmación
        command_str = str(tool_args)
        if self.is_sensitive_action(command_str, tool_name):
            if not self.request_user_confirmation(description, risks):
                return None
        
        # Ejecutar la herramienta
        print(f"[*] Ejecutando: {tool_name}")
        self._log_action("tool_execution", {
            "tool": tool_name,
            "args": tool_args,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"status": "executed", "tool": tool_name, "args": tool_args}
    
    def _log_action(self, action_type: str, data: Dict[str, Any]):
        """Registra una acción en el historial de la sesión"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "action_type": action_type,
            "data": data
        }
        
        self.action_history.append(log_entry)
        
        # Guardar en archivo
        log_file = os.path.join(self.log_dir, f"{self.session_id}.json")
        with open(log_file, 'w') as f:
            json.dump(self.action_history, f, indent=2)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen de la sesión actual"""
        return {
            "session_id": self.session_id,
            "start_time": self.action_history[0]["timestamp"] if self.action_history else None,
            "total_actions": len(self.action_history),
            "tools_used": list(set([
                a["data"].get("tool") for a in self.action_history 
                if a["action_type"] == "tool_execution"
            ])),
            "user_approvals": sum(1 for a in self.action_history 
                                 if a["action_type"] == "user_approval" and a["data"]["approved"]),
            "user_rejections": sum(1 for a in self.action_history 
                                  if a["action_type"] == "user_approval" and not a["data"]["approved"])
        }
    
    def show_help(self):
        """Muestra información de ayuda al usuario"""
        help_text = """
╔══════════════════════════════════════════════════════════════════════╗
║         AGENTE INTELIGENTE DE CIBERSEGURIDAD - AYUDA                 ║
╚══════════════════════════════════════════════════════════════════════╝

🔹 COMANDOS DISPONIBLES:
   • help          - Muestra este mensaje de ayuda
   • tools         - Lista todas las herramientas disponibles
   • history       - Muestra el historial de acciones
   • summary       - Muestra resumen de la sesión actual
   • clear         - Limpia la pantalla
   • exit/quit     - Sale del programa

🔹 EJEMPLOS DE USO:
   • "Escanea la IP 192.168.1.1"
   • "Captura 100 paquetes en eth0"
   • "Analiza el archivo de log /var/log/syslog"
   • "Busca información WHOIS de google.com"

🔹 NOTAS:
   ⚠️  El agente pedirá confirmación antes de ejecutar acciones sensibles
   📝  Todas las acciones quedan registradas en logs/
   🤖  Las respuestas se traducen automáticamente a lenguaje simple

╚══════════════════════════════════════════════════════════════════════╝
        """
        print(help_text)
