"""
ToolManager: Gestiona la carga y ejecución de herramientas (CAI + personalizadas)
"""

from typing import List, Dict, Any, Callable
from cai.sdk.agents import Agent, function_tool
import importlib
import inspect


class ToolManager:
    """
    Gestor centralizado de herramientas del agente.
    
    Funcionalidades:
    - Cargar herramientas de CAI
    - Cargar herramientas personalizadas
    - Listar herramientas disponibles
    - Ejecutar herramientas con validación
    """
    
    def __init__(self, agent: Agent):
        """
        Inicializa el gestor de herramientas.
        
        Args:
            agent: Agente de CAI al que agregar herramientas
        """
        self.agent = agent
        self.custom_tools: List[Callable] = []
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        
        print("[*] ToolManager inicializado")
    
    def register_tool(self, tool_function: Callable, metadata: Dict[str, Any] = None):
        """
        Registra una herramienta personalizada en el agente.
        
        Args:
            tool_function: Función decorada con @function_tool
            metadata: Metadatos adicionales (descripción, categoría, sensibilidad)
        """
        # Manejar FunctionTool objects de CAI
        if hasattr(tool_function, 'name'):
            tool_name = tool_function.name
        elif hasattr(tool_function, '__name__'):
            tool_name = tool_function.__name__
        else:
            tool_name = str(tool_function)
        
        # Agregar al agente
        if hasattr(self.agent, 'tools'):
            self.agent.tools.append(tool_function)
        
        # Guardar en la lista de herramientas personalizadas
        self.custom_tools.append(tool_function)
        
        # Guardar metadatos
        # Obtener descripción de la función
        if hasattr(tool_function, 'description'):
            description = tool_function.description
        elif hasattr(tool_function, '__doc__'):
            description = tool_function.__doc__ or "Sin descripción"
        else:
            description = "Sin descripción"
        
        default_metadata = {
            "name": tool_name,
            "description": description,
            "category": "general",
            "is_sensitive": False,
            "requires_root": False
        }
        
        if metadata:
            default_metadata.update(metadata)
        
        self.tool_metadata[tool_name] = default_metadata
        
        print(f"[+] Herramienta registrada: {tool_name}")
    
    def load_tools_from_module(self, module_path: str):
        """
        Carga todas las herramientas de un módulo Python.
        
        Args:
            module_path: Ruta del módulo (ej: 'src.tools.nmap_tool')
        """
        try:
            module = importlib.import_module(module_path)
            
            # Buscar todas las funciones que son herramientas
            for name, obj in inspect.getmembers(module):
                # Detectar FunctionTool objects de CAI
                if callable(obj) and (hasattr(obj, '__wrapped__') or 
                                     hasattr(obj, 'name') or 
                                     str(type(obj).__name__) == 'FunctionTool'):
                    # Es una función decorada con @function_tool
                    self.register_tool(obj)
            
            print(f"[+] Herramientas cargadas desde: {module_path}")
        except Exception as e:
            print(f"[-] Error cargando herramientas de {module_path}: {e}")
    
    def get_tool_by_name(self, tool_name: str) -> Callable:
        """Obtiene una herramienta por su nombre"""
        for tool in self.custom_tools:
            # Manejar FunctionTool objects
            current_name = tool.name if hasattr(tool, 'name') else getattr(tool, '__name__', None)
            if current_name == tool_name:
                return tool
        return None
    
    def list_tools(self, category: str = None) -> List[Dict[str, Any]]:
        """
        Lista todas las herramientas disponibles.
        
        Args:
            category: Filtrar por categoría (opcional)
            
        Returns:
            Lista de metadatos de herramientas
        """
        tools = list(self.tool_metadata.values())
        
        if category:
            tools = [t for t in tools if t.get("category") == category]
        
        return tools
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Obtiene información detallada de una herramienta"""
        return self.tool_metadata.get(tool_name, {})
    
    def validate_tool_args(self, tool_name: str, args: Dict[str, Any]) -> tuple[bool, str]:
        """
        Valida los argumentos de una herramienta antes de ejecutarla.
        
        Args:
            tool_name: Nombre de la herramienta
            args: Argumentos a validar
            
        Returns:
            (es_válido, mensaje_error)
        """
        tool = self.get_tool_by_name(tool_name)
        
        if not tool:
            return False, f"Herramienta '{tool_name}' no encontrada"
        
        # Obtener signature de la función
        sig = inspect.signature(tool)
        
        # Verificar argumentos requeridos
        for param_name, param in sig.parameters.items():
            if param.default == inspect.Parameter.empty:  # Argumento requerido
                if param_name not in args:
                    return False, f"Argumento requerido faltante: {param_name}"
        
        return True, "Argumentos válidos"
    
    def print_tools_table(self):
        """Imprime una tabla formateada con todas las herramientas"""
        print("\n" + "="*80)
        print("🛠️  HERRAMIENTAS DISPONIBLES")
        print("="*80 + "\n")
        
        # Agrupar por categoría
        categories = {}
        for tool_meta in self.tool_metadata.values():
            cat = tool_meta.get("category", "general")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool_meta)
        
        for category, tools in categories.items():
            print(f"📦 {category.upper()}")
            print("-" * 80)
            
            for tool in tools:
                name = tool["name"]
                desc = tool["description"].split("\n")[0][:60]  # Primera línea, max 60 chars
                sensitive = "⚠️ " if tool.get("is_sensitive") else ""
                root = "🔒" if tool.get("requires_root") else ""
                
                print(f"  {sensitive}{root} {name}")
                print(f"     {desc}")
                print()
        
        print("="*80 + "\n")
    
    def get_sensitive_tools(self) -> List[str]:
        """Retorna lista de nombres de herramientas sensibles"""
        return [
            name for name, meta in self.tool_metadata.items() 
            if meta.get("is_sensitive", False)
        ]
