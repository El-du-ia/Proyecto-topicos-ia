# Arquitectura del Agente Inteligente de Ciberseguridad

## Visión General

El sistema está diseñado como una arquitectura modular de 4 capas que permite extensibilidad, mantenibilidad y separación de responsabilidades.

```
┌─────────────────────────────────────────────────────────────┐
│                      CAPA DE USUARIO                        │
│                   (main.py + UI Layer)                      │
│  - Interfaz CLI                                             │
│  - Menús y navegación                                       │
│  - Manejo de entrada/salida                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   CAPA DE CONTROL                           │
│                 (Core Controllers)                          │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐│
│  │ AgentController │  │ ToolManager  │  │   Interpreter  ││
│  │                 │  │              │  │                ││
│  │ - Orquestación  │  │ - Registro   │  │ - Traducción   ││
│  │ - Confirmación  │  │ - Validación │  │ - Formateo     ││
│  │ - Logging       │  │ - Ejecución  │  │ - Explicación  ││
│  └─────────────────┘  └──────────────┘  └────────────────┘│
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 CAPA DE HERRAMIENTAS                        │
│                   (Tools Layer)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Nmap   │  │  Scapy   │  │  WHOIS   │  │   Logs   │  │
│  │  Tools   │  │  Sniffer │  │  & DNS   │  │ Analyzer │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │         CAI Tools Wrapper                           │  │
│  │  (Integración con herramientas oficiales de CAI)    │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  CAPA DE DATOS                              │
│                 (Models & Storage)                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────┐ │
│  │ Conversation    │  │  Session Logs   │  │  Reports   │ │
│  │    Memory       │  │     (JSON)      │  │  (Future)  │ │
│  └─────────────────┘  └─────────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Componentes Principales

### 1. AgentController (Orquestador)

**Responsabilidad**: Coordinar el flujo de ejecución y decisiones del agente.

```python
class CybersecurityAgent:
    - __init__(agent, log_dir)
    - is_sensitive_action(command, tool_name) -> bool
    - request_user_confirmation(description, risks) -> bool
    - execute_with_confirmation(tool_name, args, desc, risks)
    - _log_action(action_type, data)
    - get_session_summary() -> dict
```

**Flujo de Decisión**:
```
Usuario → Input → ¿Es sensible? 
                     │
                     ├─ Sí → Solicitar confirmación → ¿Aprobado?
                     │                                   │
                     │                                   ├─ Sí → Ejecutar
                     │                                   └─ No → Cancelar
                     │
                     └─ No → Ejecutar directamente
                                    │
                                    └→ Registrar → Interpretar → Mostrar
```

### 2. ToolManager (Gestor de Herramientas)

**Responsabilidad**: Cargar, validar y gestionar herramientas personalizadas.

```python
class ToolManager:
    - register_tool(function, metadata)
    - load_tools_from_module(module_path)
    - get_tool_by_name(name) -> callable
    - list_tools(category) -> list
    - validate_tool_args(tool_name, args) -> (bool, str)
    - print_tools_table()
```

**Metadatos de Herramientas**:
```python
{
    "name": "tool_name",
    "description": "Qué hace",
    "category": "network|reconnaissance|analysis",
    "is_sensitive": bool,
    "requires_root": bool
}
```

### 3. ResultInterpreter (Traductor)

**Responsabilidad**: Convertir salidas técnicas a lenguaje comprensible.

```python
class ResultInterpreter:
    - interpret_nmap_output(raw) -> dict
    - interpret_packet_capture(raw, count) -> dict
    - interpret_whois(raw) -> dict
    - interpret_log_analysis(findings) -> dict
    - format_interpretation(interpretation) -> str
```

**Estructura de Interpretación**:
```python
{
    "summary": "Resumen en una línea",
    "findings": ["Lista", "de", "hallazgos"],
    "severity": "critical|high|medium|low|info",
    "recommendations": ["Acción 1", "Acción 2"],
    "simple_explanation": "Explicación detallada para no expertos"
}
```

### 4. ConversationMemory (Persistencia)

**Responsabilidad**: Mantener contexto entre interacciones.

```python
class ConversationMemory:
    - add_message(role, content, metadata)
    - get_recent_messages(count) -> list
    - get_all_messages() -> list
    - clear_memory()
    - get_session_summary() -> dict
```

## Patrones de Diseño Utilizados

### 1. Strategy Pattern (Herramientas)
Cada herramienta implementa la misma interfaz (`@function_tool`) permitiendo intercambiarlas dinámicamente.

### 2. Facade Pattern (CLI)
`CLI` proporciona una interfaz simplificada para operaciones complejas de terminal.

### 3. Observer Pattern (Logging)
Cada acción notifica al sistema de logging para registro automático.

### 4. Chain of Responsibility (Confirmación)
```
Input → Validación → Clasificación → Confirmación → Ejecución
```

## Flujo de Datos

### Flujo de Ejecución de Herramienta:

```
1. Usuario ingresa comando natural
   ↓
2. CAI LLM interpreta y selecciona herramienta
   ↓
3. AgentController recibe tool_call
   ↓
4. ToolManager valida argumentos
   ↓
5. AgentController verifica si es sensible
   ↓
6. [SI ES SENSIBLE] Solicita confirmación
   ↓
7. Ejecuta herramienta
   ↓
8. Captura resultado
   ↓
9. ResultInterpreter traduce a lenguaje simple
   ↓
10. Muestra resultado al usuario
    ↓
11. Registra en logs
```

### Flujo de Memoria:

```
Usuario escribe → ConversationMemory.add_message("user", texto)
                                    ↓
                          Guarda en memory.json
                                    ↓
Agente responde → ConversationMemory.add_message("assistant", resp)
                                    ↓
                         Actualiza contexto persistente
```

## Extensibilidad

### Agregar Nueva Herramienta:

1. **Crear archivo**: `src/tools/nueva_tool.py`
2. **Implementar**:
```python
@function_tool
def nueva_herramienta(param1: str, param2: int) -> str:
    """Documentación clara"""
    # Lógica
    return resultado
```
3. **Registrar en main.py**:
```python
tool_manager.register_tool(nueva_herramienta, {
    "category": "custom",
    "is_sensitive": False,
    "requires_root": False
})
```

### Agregar Nueva Interpretación:

```python
# En interpreter.py
def interpret_nueva_tool(self, raw_output: str) -> Dict[str, Any]:
    # Parsear output
    # Generar explicación simple
    # Determinar severidad
    # Crear recomendaciones
    return interpretation
```

## Seguridad

### Niveles de Sensibilidad:

1. **Sensible + Root**: Captura de paquetes
   - Requiere confirmación
   - Requiere privilegios elevados
   
2. **Sensible**: Escaneos de red
   - Requiere confirmación
   - Usuario normal puede ejecutar
   
3. **No Sensible**: Consultas DNS, WHOIS
   - Ejecución directa
   - Sin riesgos

### Validaciones:

```python
# Antes de ejecutar CUALQUIER herramienta:
1. Validar argumentos (tipos, rangos)
2. Verificar permisos necesarios
3. Comprobar si herramienta existe
4. Solicitar confirmación si aplica
5. Registrar intención
6. Ejecutar
7. Registrar resultado
```

## Performance

### Optimizaciones Implementadas:

- **Lazy Loading**: Herramientas se cargan bajo demanda
- **Caching**: Metadatos de herramientas en memoria
- **Streaming**: Logs se escriben incrementalmente
- **Límites**: max_lines en análisis de logs para evitar OOM

---

**Principios de Diseño**:
1. **Modularidad**: Cada componente tiene una responsabilidad única
2. **Extensibilidad**: Fácil agregar nuevas herramientas
3. **Usabilidad**: Prioridad en UX para no expertos
4. **Seguridad**: Confirmación explícita para acciones sensibles
5. **Trazabilidad**: Logs completos de todas las operaciones
