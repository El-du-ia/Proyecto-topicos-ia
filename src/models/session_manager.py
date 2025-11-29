"""
Session Manager - Gestiona sesiones persistentes y reanudación de conversaciones
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class SessionManager:
    """
    Gestiona sesiones de conversación persistentes.
    
    Permite:
    - Listar todas las sesiones guardadas
    - Cargar una sesión anterior con todo su contexto
    - Reanudar conversaciones desde donde se quedaron
    - Buscar sesiones por fecha, contenido, etc.
    """
    
    def __init__(self, logs_dir: str = "logs", memory_dir: str = "memory"):
        """
        Inicializa el gestor de sesiones.
        
        Args:
            logs_dir: Directorio de logs de CAI
            memory_dir: Directorio de memoria conversacional
        """
        self.logs_dir = logs_dir
        self.memory_dir = memory_dir
        self.sessions_cache: Dict[str, Dict] = {}
        
    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Lista todas las sesiones disponibles ordenadas por fecha.
        
        Args:
            limit: Número máximo de sesiones a retornar
            
        Returns:
            Lista de diccionarios con información de cada sesión
        """
        sessions = []
        
        # Buscar archivos de log de CAI
        if os.path.exists(self.logs_dir):
            for filename in sorted(os.listdir(self.logs_dir), reverse=True):
                if filename.startswith('cai_') and filename.endswith('.jsonl'):
                    session_info = self._parse_session_from_log(filename)
                    if session_info:
                        sessions.append(session_info)
                        if len(sessions) >= limit:
                            break
        
        return sessions
    
    def _parse_session_from_log(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Extrae información básica de una sesión desde su archivo de log.
        
        Args:
            filename: Nombre del archivo de log
            
        Returns:
            Diccionario con información de la sesión o None si hay error
        """
        filepath = os.path.join(self.logs_dir, filename)
        
        try:
            # Extraer información del nombre del archivo
            # Formato: cai_{session_id}_{timestamp}_{user}_{os}_{kernel}_{ip}.jsonl
            parts = filename.replace('.jsonl', '').split('_')
            
            if len(parts) < 3:
                return None
            
            session_id = parts[1]  # El UUID después de 'cai_'
            timestamp_str = parts[2] if len(parts) > 2 else "unknown"
            user = parts[3] if len(parts) > 3 else "unknown"
            
            # Leer primera y última línea para obtener info de sesión
            with open(filepath, 'r') as f:
                lines = f.readlines()
                
            if not lines:
                return None
            
            # Primera línea debe ser session_start
            first_event = json.loads(lines[0])
            
            # Contar mensajes
            user_messages = 0
            assistant_messages = 0
            last_timestamp = first_event.get('timestamp', '')
            
            for line in lines:
                try:
                    event = json.loads(line)
                    if event.get('event') == 'user_message':
                        user_messages += 1
                    elif event.get('event') == 'assistant_message':
                        assistant_messages += 1
                    if 'timestamp' in event:
                        last_timestamp = event['timestamp']
                except:
                    continue
            
            # Obtener preview del último mensaje del usuario
            last_user_message = ""
            for line in reversed(lines):
                try:
                    event = json.loads(line)
                    if event.get('event') == 'user_message':
                        last_user_message = event.get('content', '')[:100]
                        break
                except:
                    continue
            
            return {
                'session_id': session_id,
                'filename': filename,
                'filepath': filepath,
                'timestamp': timestamp_str,
                'user': user,
                'start_time': first_event.get('timestamp', ''),
                'last_activity': last_timestamp,
                'user_messages': user_messages,
                'assistant_messages': assistant_messages,
                'total_interactions': user_messages + assistant_messages,
                'last_message_preview': last_user_message
            }
            
        except Exception as e:
            print(f"[!] Error parseando {filename}: {e}")
            return None
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Carga una sesión completa con todo su contexto.
        
        Args:
            session_id: ID de la sesión a cargar (puede ser el UUID o el filename)
            
        Returns:
            Diccionario con toda la información de la sesión
        """
        # Buscar el archivo de log correspondiente
        log_file = None
        
        if os.path.exists(self.logs_dir):
            for filename in os.listdir(self.logs_dir):
                if session_id in filename and filename.endswith('.jsonl'):
                    log_file = os.path.join(self.logs_dir, filename)
                    break
        
        if not log_file or not os.path.exists(log_file):
            return None
        
        # Cargar todos los eventos del log
        events = []
        messages = []
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        events.append(event)
                        
                        # Extraer mensajes para reconstruir conversación
                        if event.get('event') == 'user_message':
                            messages.append({
                                'role': 'user',
                                'content': event.get('content', ''),
                                'timestamp': event.get('timestamp', '')
                            })
                        elif event.get('event') == 'assistant_message':
                            messages.append({
                                'role': 'assistant',
                                'content': event.get('content', ''),
                                'timestamp': event.get('timestamp', '')
                            })
                    except:
                        continue
            
            # Extraer información adicional
            session_info = self._parse_session_from_log(os.path.basename(log_file))
            
            return {
                'session_info': session_info,
                'events': events,
                'messages': messages,
                'message_count': len(messages),
                'loaded_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[!] Error cargando sesión: {e}")
            return None
    
    def get_session_context(self, session_id: str) -> Optional[List[Dict[str, str]]]:
        """
        Obtiene solo los mensajes de contexto de una sesión para reanudar.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Lista de mensajes en formato CAI-compatible
        """
        session_data = self.load_session(session_id)
        
        if not session_data:
            return None
        
        return session_data.get('messages', [])
    
    def search_sessions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca sesiones que contengan cierto texto en sus mensajes.
        
        Args:
            query: Texto a buscar
            limit: Número máximo de resultados
            
        Returns:
            Lista de sesiones que coinciden con la búsqueda
        """
        matching_sessions = []
        query_lower = query.lower()
        
        sessions = self.list_sessions(limit=100)  # Buscar en más sesiones
        
        for session_info in sessions:
            # Buscar en el preview del último mensaje
            if query_lower in session_info.get('last_message_preview', '').lower():
                matching_sessions.append(session_info)
                if len(matching_sessions) >= limit:
                    break
        
        return matching_sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Elimina una sesión y todos sus archivos asociados.
        
        Args:
            session_id: ID de la sesión a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        deleted = False
        
        # Eliminar log de CAI
        if os.path.exists(self.logs_dir):
            for filename in os.listdir(self.logs_dir):
                if session_id in filename:
                    try:
                        os.remove(os.path.join(self.logs_dir, filename))
                        deleted = True
                    except Exception as e:
                        print(f"[!] Error eliminando {filename}: {e}")
        
        # Eliminar memoria conversacional
        if os.path.exists(self.memory_dir):
            for filename in os.listdir(self.memory_dir):
                if session_id in filename:
                    try:
                        os.remove(os.path.join(self.memory_dir, filename))
                    except Exception as e:
                        print(f"[!] Error eliminando {filename}: {e}")
        
        return deleted
    
    def print_sessions_table(self, sessions: List[Dict[str, Any]]):
        """
        Imprime una tabla formateada de sesiones.
        
        Args:
            sessions: Lista de sesiones a mostrar
        """
        if not sessions:
            print("\n📭 No hay sesiones guardadas\n")
            return
        
        print("\n" + "="*100)
        print("📚 SESIONES GUARDADAS")
        print("="*100)
        print(f"\n{'#':<4} {'Session ID':<16} {'Fecha':<20} {'Mensajes':<10} {'Usuario':<10} {'Preview':<30}")
        print("-"*100)
        
        for idx, session in enumerate(sessions, 1):
            session_id_short = session['session_id'][:12]
            timestamp = session.get('timestamp', 'unknown')
            
            # Formatear fecha de YYYYMMDD_HHMMSS a DD/MM/YYYY HH:MM:SS
            if timestamp != 'unknown' and len(timestamp) >= 8:
                try:
                    if '_' in timestamp:
                        date_part, time_part = timestamp.split('_')
                    else:
                        date_part = timestamp
                        time_part = ''
                    
                    year = date_part[:4]
                    month = date_part[4:6]
                    day = date_part[6:8]
                    
                    if time_part and len(time_part) >= 6:
                        hour = time_part[:2]
                        minute = time_part[2:4]
                        second = time_part[4:6]
                        formatted_timestamp = f"{day}/{month}/{year} {hour}:{minute}"
                    else:
                        formatted_timestamp = f"{day}/{month}/{year}"
                except:
                    formatted_timestamp = timestamp
            else:
                formatted_timestamp = timestamp
            
            messages = session.get('total_interactions', 0)
            user = session.get('user', 'unknown')
            preview = session.get('last_message_preview', '')[:30]
            
            print(f"{idx:<4} {session_id_short:<16} {formatted_timestamp:<20} {messages:<10} {user:<10} {preview:<30}")
        
        print("="*100 + "\n")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de todas las sesiones.
        
        Returns:
            Diccionario con estadísticas
        """
        sessions = self.list_sessions(limit=1000)
        
        total_sessions = len(sessions)
        total_messages = sum(s.get('total_interactions', 0) for s in sessions)
        
        # Contar por usuario
        users = {}
        for session in sessions:
            user = session.get('user', 'unknown')
            users[user] = users.get(user, 0) + 1
        
        return {
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'users': users,
            'average_messages_per_session': total_messages / total_sessions if total_sessions > 0 else 0
        }
