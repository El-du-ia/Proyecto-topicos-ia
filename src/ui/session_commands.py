"""
Comandos relacionados con la gestión de sesiones
Maneja carga, búsqueda y visualización de sesiones
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..ui.cli_interface import CLI
from ..models.session_manager import SessionManager
from ..core.permissions import PermissionChecker


class SessionCommands:
    """Manejador de comandos de sesión"""
    
    def __init__(self, session_manager: SessionManager, agent):
        self.session_manager = session_manager
        self.agent = agent
        self.current_session_id: Optional[str] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.turn_count: int = 0
    
    def load_session_context(self, session_id: str) -> bool:
        """Carga el contexto de una sesión anterior"""
        print(f"\n🔄 Cargando sesión: {session_id}...")
        
        session_data = self.session_manager.load_session(session_id)
        
        if not session_data:
            CLI.print_error(f"No se pudo cargar la sesión: {session_id}")
            return False
        
        # Cargar mensajes en el historial
        self.conversation_history = session_data.get('messages', [])
        
        CLI.print_success(f"✓ Sesión cargada: {len(self.conversation_history)} mensajes")
        print(f"📅 Creada: {session_data['session_info']['start_time']}")
        print(f"📝 Último mensaje: {session_data['session_info']['last_activity']}")
        print()
        return True
    
    def display_sessions(self):
        """Muestra lista de sesiones guardadas"""
        sessions = self.session_manager.list_sessions(limit=20)
        self.session_manager.print_sessions_table(sessions)
        
        if sessions:
            print("💡 Usa '/load <session_id>' para reanudar una sesión")
            print("   Ejemplo: /load 0a28b9e5\n")
    
    def load_session_command(self, session_id: str):
        """Carga una sesión específica"""
        if not session_id:
            CLI.print_error("Debes proporcionar un session_id")
            print("Uso: /load <session_id>")
            print("     /load 0a28b9e5")
            return
        
        if self.load_session_context(session_id):
            self.current_session_id = session_id
            
            # Mostrar resumen del historial cargado
            if self.conversation_history:
                print("📝 Resumen de la conversación anterior:")
                print("-" * 70)
                for i, msg in enumerate(self.conversation_history[-5:], 1):  # Últimos 5 mensajes
                    role = "👤 Usuario" if msg['role'] == 'user' else "🤖 Asistente"
                    content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
                    print(f"{role}: {content}")
                print("-" * 70)
                print("✅ Puedes continuar la conversación desde donde la dejaste\n")
    
    def search_sessions_command(self, query: str):
        """Busca sesiones por contenido"""
        if not query:
            CLI.print_error("Debes proporcionar un texto a buscar")
            print("Uso: /search <texto>")
            return
        
        print(f"\n🔍 Buscando '{query}'...\n")
        results = self.session_manager.search_sessions(query, limit=10)
        
        if results:
            self.session_manager.print_sessions_table(results)
        else:
            print("📭 No se encontraron sesiones con ese contenido\n")
    
    def display_current_history(self):
        """Muestra el historial de la sesión actual"""
        print("\n" + "="*70)
        print("📝 HISTORIAL DE LA SESIÓN ACTUAL")
        print("="*70)
        
        if not self.conversation_history:
            print("\n📭 No hay historial en esta sesión aún\n")
            return
        
        print(f"\nTotal de mensajes: {len(self.conversation_history)}\n")
        
        for i, msg in enumerate(self.conversation_history, 1):
            role_emoji = "👤" if msg['role'] == 'user' else "🤖"
            role_name = "Usuario" if msg['role'] == 'user' else "Asistente"
            timestamp = msg.get('timestamp', 'unknown')
            content = msg['content']
            
            print(f"{role_emoji} [{i}] {role_name} ({timestamp}):")
            print(f"   {content}\n")
        
        print("="*70 + "\n")
    
    def display_session_info(self):
        """Muestra información detallada de la sesión actual"""
        print("\n" + "="*70)
        print("📊 INFORMACIÓN DE LA SESIÓN ACTUAL")
        print("="*70)
        
        # Información básica
        if self.current_session_id:
            print(f"\n🆔 Session ID: {self.current_session_id}")
            print("📝 Estado: Sesión cargada (reanudada)")
            
            # Intentar cargar información completa de la sesión
            session_data = self.session_manager.load_session(self.current_session_id)
            if session_data and session_data.get('session_info'):
                info = session_data['session_info']
                print(f"📅 Creada: {info.get('start_time', 'unknown')}")
                print(f"🕐 Última actividad: {info.get('last_activity', 'unknown')}")
                print(f"👤 Usuario: {info.get('user', 'unknown')}")
        else:
            # Generar un session ID temporal basado en el timestamp actual
            temp_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"\n🆔 Session ID: {temp_id} (nueva)")
            print("📝 Estado: Sesión nueva (no guardada aún)")
            print(f"📅 Iniciada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Estadísticas de mensajes
        print(f"\n💬 Estadísticas de Conversación:")
        total_messages = len(self.conversation_history)
        user_msgs = sum(1 for m in self.conversation_history if m['role'] == 'user')
        assistant_msgs = sum(1 for m in self.conversation_history if m['role'] == 'assistant')
        
        print(f"   • Total de mensajes: {total_messages}")
        print(f"   • Mensajes del usuario: {user_msgs}")
        print(f"   • Respuestas del asistente: {assistant_msgs}")
        print(f"   • Turnos de conversación: {self.turn_count}")
        
        # Información del sistema
        print(f"\n🖥️  Sistema:")
        print(f"   • Usuario actual: {os.getenv('USER', 'unknown')}")
        print(f"   • Directorio de trabajo: {os.getcwd()}")
        print(f"   • Privilegios: {'ROOT' if PermissionChecker.is_root() else 'Usuario normal'}")
        
        # Información del agente
        print(f"\n🤖 Agente:")
        agent_name = getattr(self.agent, 'name', 'Network Security Analyzer')
        print(f"   • Nombre: {agent_name}")
        if hasattr(self.agent, 'tools') and self.agent.tools:
            print(f"   • Herramientas registradas: {len(self.agent.tools)}")
        
        # Ubicación de archivos
        print(f"\n📁 Archivos:")
        print(f"   • Logs: logs/")
        print(f"   • Memoria: memory/")
        if self.current_session_id:
            if os.path.exists('logs'):
                log_files = [f for f in os.listdir('logs') if self.current_session_id[:8] in f]
                if log_files:
                    print(f"   • Archivos de esta sesión: {len(log_files)}")
        
        # Costos (si está disponible)
        try:
            from cai.util import COST_TRACKER
            total_cost = COST_TRACKER.session_total_cost
            print(f"\n💰 Costos:")
            print(f"   • Costo de esta sesión: ${total_cost:.6f}")
        except:
            pass
        
        print("\n" + "="*70 + "\n")
    
    def add_user_message(self, content: str):
        """Agrega un mensaje del usuario al historial"""
        self.conversation_history.append({
            'role': 'user',
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_assistant_message(self, content: str):
        """Agrega un mensaje del asistente al historial"""
        if content.strip():
            self.conversation_history.append({
                'role': 'assistant',
                'content': content.strip(),
                'timestamp': datetime.now().isoformat()
            })
