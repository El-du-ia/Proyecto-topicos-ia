"""
Terminal personalizada basada en CAI CLI
Extiende la funcionalidad de cai.cli con características personalizadas
Implementa un loop personalizado que intercepta comandos antes de CAI
"""

from typing import Optional, Dict, Any
from datetime import datetime
from math import inf

# Importar componentes de CAI
from cai.sdk.agents import Agent, Runner

# Importar nuestros módulos refactorizados
from ..ui.cli_interface import CLI
from ..ui import terminal_display
from ..ui.session_commands import SessionCommands
from ..ui.terminal_commands import CommandHandler
from ..models.session_manager import SessionManager


class CustomCAITerminal:
    """
    Terminal personalizada que REEMPLAZA el CLI de CAI con uno propio.
    Maneja comandos personalizados y luego envía queries al agente de CAI.
    """
    
    def __init__(self, agent: Agent, show_custom_banner: bool = True, 
                 show_permissions: bool = True, custom_commands: Dict[str, callable] = None,
                 session_id: Optional[str] = None):
        """
        Inicializa la terminal personalizada.
        
        Args:
            agent: Agente de CAI a usar
            show_custom_banner: Mostrar nuestro banner personalizado
            show_permissions: Mostrar estado de permisos
            custom_commands: Diccionario de comandos personalizados {nombre: función}
            session_id: ID de sesión a reanudar (opcional)
        """
        self.agent = agent
        self.show_custom_banner = show_custom_banner
        self.show_permissions = show_permissions
        self.context_variables = {}
        
        # Inicializar componentes modulares
        session_manager = SessionManager()
        self.session_commands = SessionCommands(session_manager, agent)
        self.command_handler = CommandHandler(agent, self.session_commands, custom_commands)
        
        # Si se proporciona un session_id, cargar el contexto
        if session_id:
            self.session_commands.load_session_context(session_id)
            self.session_commands.current_session_id = session_id
        
    
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
    
    def _sync_history_from_agent(self):
        """Sincroniza conversation_history desde agent.model.message_history para mantener consistencia"""
        try:
            if hasattr(self.agent, 'model') and hasattr(self.agent.model, 'message_history'):
                # Actualizar nuestro historial local con el del agente (es la fuente de verdad)
                agent_history = self.agent.model.message_history
                
                # Solo sincronizar si hay diferencia de longitud
                if len(agent_history) != len(self.session_commands.conversation_history):
                    self.session_commands.conversation_history = [
                        {
                            'role': msg.get('role', 'unknown'),
                            'content': msg.get('content', ''),
                            'timestamp': msg.get('timestamp', datetime.now().isoformat())
                        }
                        for msg in agent_history
                        if msg.get('role') in ['user', 'assistant']  # Solo user y assistant, no tool messages
                    ]
        except Exception as e:
            # Fallar silenciosamente para no interrumpir el flujo
            pass
    
    
    def run_agent_query(self, query: str):
        """Ejecuta una consulta en el agente de CAI (el historial ya está en agent.model.message_history)"""
        try:
            # Agregar el nuevo mensaje del usuario a nuestro tracking local
            self.session_commands.add_user_message(query)
            
            print()  # Línea en blanco antes de la respuesta
            
            # NOTA: No necesitamos pasar el historial completo aquí.
            # El agente ya tiene el historial en agent.model.message_history.
            # Runner.run_sync() automáticamente añade el nuevo mensaje al historial interno.
            response = Runner.run_sync(
                starting_agent=self.agent,
                input=query,
                context=self.context_variables,
                max_turns=20
            )
            
            # Extraer contenido de la respuesta
            assistant_response = ""
            
            # NO imprimir aquí - CAI ya muestra la respuesta en su cuadro
            # Solo extraer para guardar en historial
            if hasattr(response, 'final_output') and response.final_output:
                assistant_response = response.final_output
            elif hasattr(response, 'messages') and response.messages:
                for message in response.messages:
                    if hasattr(message, 'content') and message.content:
                        assistant_response += message.content + "\n"
            elif hasattr(response, 'output') and response.output:
                assistant_response = response.output
            
            # Agregar respuesta del asistente a nuestro tracking local
            self.session_commands.add_assistant_message(assistant_response)
            
            # Sincronizar nuestro historial local con el del agente para mantener consistencia
            self._sync_history_from_agent()
            
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
        terminal_display.display_startup_info(self.show_custom_banner, self.show_permissions)
        
        print("\n💡 Escribe /help para ver comandos disponibles")
        print("💡 Escribe /exit para salir\n")
        
        # Loop principal
        while self.session_commands.turn_count < max_turns:
            # Obtener input del usuario
            user_input = self.get_user_input()
            
            if user_input is None:
                break
            
            if not user_input:
                continue
            
            # Manejar comando personalizado usando el command_handler
            result = self.command_handler.handle_command(user_input)
            
            if result is None:  # Salir
                break
            elif result is True:  # Comando manejado
                continue
            
            # No es comando, enviar al agente
            self.run_agent_query(user_input)
            self.session_commands.turn_count += 1
        
        # Mensaje de despedida
        terminal_display.display_goodbye()


def run_custom_cai_terminal(agent: Agent, **kwargs):
    """
    Función de conveniencia para ejecutar la terminal personalizada.
    
    Args:
        agent: Agente de CAI a usar
        **kwargs: Argumentos adicionales para CustomCAITerminal
    """
    terminal = CustomCAITerminal(agent, **kwargs)
    terminal.run()

