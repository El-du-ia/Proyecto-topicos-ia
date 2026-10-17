"""
Modelo de memoria conversacional para el agente
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class ConversationMemory:
    """
    Gestiona la memoria de conversaciones del agente.
    
    Funcionalidades:
    - Guardar historial de mensajes
    - Recordar contexto de sesiones anteriores
    - Persistir memoria en disco
    """
    
    def __init__(self, session_id: str, memory_dir: str = "memory"):
        """
        Inicializa la memoria conversacional.
        
        Args:
            session_id: ID único de la sesión
            memory_dir: Directorio donde guardar la memoria
        """
        self.session_id = session_id
        self.memory_dir = memory_dir
        self.messages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }
        
        # Crear directorio si no existe
        os.makedirs(memory_dir, exist_ok=True)
        
        # Cargar memoria existente si hay
        self._load_memory()
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """
        Agrega un mensaje a la memoria.
        
        Args:
            role: 'user', 'assistant', o 'system'
            content: Contenido del mensaje
            metadata: Datos adicionales del mensaje
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        self.metadata["last_updated"] = datetime.now().isoformat()
        self._save_memory()
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Obtiene los últimos N mensajes"""
        return self.messages[-count:] if len(self.messages) >= count else self.messages
    
    def get_all_messages(self) -> List[Dict[str, Any]]:
        """Obtiene todos los mensajes de la sesión"""
        return self.messages.copy()
    
    def clear_memory(self):
        """Borra toda la memoria de la sesión"""
        self.messages = []
        self.metadata["last_updated"] = datetime.now().isoformat()
        self._save_memory()
    
    def _get_memory_file(self) -> str:
        """Obtiene la ruta del archivo de memoria"""
        return os.path.join(self.memory_dir, f"{self.session_id}_memory.json")
    
    def _save_memory(self):
        """Guarda la memoria en disco"""
        memory_data = {
            "metadata": self.metadata,
            "messages": self.messages
        }
        
        with open(self._get_memory_file(), 'w') as f:
            json.dump(memory_data, f, indent=2)
    
    def _load_memory(self):
        """Carga la memoria desde disco si existe"""
        memory_file = self._get_memory_file()
        
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r') as f:
                    memory_data = json.load(f)
                
                self.metadata = memory_data.get("metadata", self.metadata)
                self.messages = memory_data.get("messages", [])
                
                print(f"[*] Memoria cargada: {len(self.messages)} mensajes")
            except Exception as e:
                print(f"[!] Error cargando memoria: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen de la sesión"""
        user_messages = sum(1 for m in self.messages if m["role"] == "user")
        assistant_messages = sum(1 for m in self.messages if m["role"] == "assistant")
        
        return {
            "session_id": self.session_id,
            "created_at": self.metadata["created_at"],
            "last_updated": self.metadata["last_updated"],
            "total_messages": len(self.messages),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
        }
