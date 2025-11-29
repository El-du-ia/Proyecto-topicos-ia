# 🖥️ Implementación de la Terminal Personalizada

## 📝 Descripción General

Sistema de terminal personalizada modular que extiende CAI Framework, proporcionando comandos personalizados, gestión de sesiones, y control total del flujo de interacción mientras mantiene toda la potencia del agente inteligente.

---

## 🏗️ Arquitectura Modular

```
┌──────────────────────────────────────────────────────────────┐
│                     CustomCAITerminal                        │
│                  (Coordinador Principal)                     │
└────────────┬─────────────────────────────────────────────────┘
             │
             ├─► terminal_display.py    (Visualización)
             │   • display_help()
             │   • display_costs()
             │   • display_status()
             │   • display_tools()
             │   • display_examples()
             │   • display_startup_info()
             │   • display_goodbye()
             │
             ├─► terminal_commands.py   (Manejador de Comandos)
             │   • CommandHandler
             │   • handle_command()
             │   • create_cybersecurity_commands()
             │
             ├─► session_commands.py    (Gestión de Sesiones)
             │   • SessionCommands
             │   • load_session_context()
             │   • display_sessions()
             │   • search_sessions_command()
             │   • display_current_history()
             │   • display_session_info()
             │
             └─► CAI Runner              (Motor de IA)
                 • run_agent_query()
                 • Agent + Tools
                 • Context management
```

---

## 📁 Estructura de Archivos

### `custom_terminal.py` (177 líneas)
**Responsabilidad**: Coordinación principal y loop de ejecución



### `terminal_display.py` (197 líneas)
**Responsabilidad**: Todas las funciones de visualización



### `terminal_commands.py` (162 líneas)
**Responsabilidad**: Routing y procesamiento de comandos



### `session_commands.py` (198 líneas)
**Responsabilidad**: Gestión completa de sesiones

---

## 🎯 Flujo de Ejecución

### 1. Inicialización
```python
# En main.py
from src.ui.custom_terminal import run_custom_cai_terminal
from src.ui.terminal_commands import create_cybersecurity_commands

# Crear comandos personalizados opcionales
custom_cmds = create_cybersecurity_commands()

# Ejecutar terminal
run_custom_cai_terminal(
    agent=agent,
    custom_commands=custom_cmds,
    session_id=None  # O un ID para reanudar
)
```

### 2. Loop Principal (custom_terminal.py)
```
┌─────────────────────────────────┐
│ 1. display_startup_info()      │ ← Banner + permisos
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 2. while turn_count < max:     │
│    user_input = get_input()    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 3. handle_command(user_input)  │ ← CommandHandler
└────────────┬────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
   True/None      False
   (manejado)   (continuar)
      │             │
      │             ▼
      │    ┌────────────────────┐
      │    │ run_agent_query()  │ ← Enviar a CAI
      │    └────────────────────┘
      │
      ▼
┌─────────────────────────────────┐
│ 4. display_goodbye()            │ ← Mensaje final
└─────────────────────────────────┘
```

### 3. Procesamiento de Comandos (terminal_commands.py)
```python
# Ejemplo de flujo de un comando
user_input = "/load abc123"

# CommandHandler.handle_command()
if cmd.startswith('/load '):
    session_id = cmd[6:].strip()  # "abc123"
    self.session_commands.load_session_command(session_id)
    return True  # Comando manejado

# Si fuera otro tipo
if cmd in ['/help', '/ayuda']:
    terminal_display.display_help(self.custom_commands)
    return True

# Si no es comando conocido
return False  # Dejar que CAI lo procese
```

### 4. Interacción con Agente (custom_terminal.py)
```python
def run_agent_query(self, query: str):
    # 1. Agregar al historial
    self.session_commands.add_user_message(query)
    
    # 2. Preparar contexto histórico
    messages_for_cai = []
    if len(self.session_commands.conversation_history) > 1:
        for msg in self.session_commands.conversation_history[:-1]:
            messages_for_cai.append({
                'role': msg['role'],
                'content': msg['content']
            })
    
    # 3. Ejecutar con CAI Runner
    response = Runner.run_sync(
        starting_agent=self.agent,
        input=query,
        context=self.context_variables,
        max_turns=20
    )
    
    # 4. Guardar respuesta
    self.session_commands.add_assistant_message(response.final_output)
```

---

## 💬 Comandos Disponibles

### 🟢 Comandos de Sistema
| Comando | Descripción | Módulo |
|---------|-------------|--------|
| `/help`, `/ayuda` | Ayuda completa | terminal_display |
| `/clear` | Limpiar pantalla | cli_interface |
| `/exit`, `/quit`, `/salir` | Salir | terminal_commands |
| `/status`, `/estado` | Estado del sistema | terminal_display |
| `/cost` | Costos de API | terminal_display |

### 🔄 Comandos de Sesiones
| Comando | Descripción | Módulo |
|---------|-------------|--------|
| `/sessions` | Listar sesiones guardadas | session_commands |
| `/load <id>` | Reanudar sesión | session_commands |
| `/search <texto>` | Buscar sesiones | session_commands |
| `/history` | Ver historial actual | session_commands |
| `/info` | Info detallada de sesión | session_commands |

### 🛠️ Comandos de Información
| Comando | Descripción | Módulo |
|---------|-------------|--------|
| `/tools` | Lista de herramientas | terminal_display |
| `/examples` | Ejemplos de uso | terminal_display |
| `/permisos` | Estado de permisos | permissions |

### 🔵 Comandos Personalizados Adicionales
Se pueden agregar mediante `custom_commands` en la inicialización.

---

## 🎨 Personalización

### Agregar Nuevos Comandos

#### 1. Crear función del comando
```python
# En terminal_commands.py o archivo propio

def cmd_generar_reporte():
    """Genera un reporte de las herramientas ejecutadas"""
    print("\n📊 GENERANDO REPORTE...")
    # Tu lógica aquí
    print("✅ Reporte guardado en reports/reporte.pdf\n")

def cmd_exportar_sesion():
    """Exporta la sesión actual a JSON"""
    print("\n💾 EXPORTANDO SESIÓN...")
    # Tu lógica aquí
    print("✅ Sesión exportada\n")
```

#### 2. Registrar comandos
```python
# En main.py
from src.ui.terminal_commands import create_cybersecurity_commands

def mis_comandos_personalizados():
    """Mis comandos adicionales"""
    return {
        'reporte': cmd_generar_reporte,
        'exportar': cmd_exportar_sesion,
    }

# Combinar con comandos base
custom_cmds = {
    **create_cybersecurity_commands(),
    **mis_comandos_personalizados()
}

# Ejecutar con comandos personalizados
run_custom_cai_terminal(agent, custom_commands=custom_cmds)
```

#### 3. Usar en terminal
```bash
🤖 dui-IA > /reporte
📊 GENERANDO REPORTE...
✅ Reporte guardado en reports/reporte.pdf

🤖 dui-IA > /exportar
💾 EXPORTANDO SESIÓN...
✅ Sesión exportada
```

### Personalizar Visualización

#### Modificar display_help
```python
# En terminal_display.py

def display_help(custom_commands: dict = None):
    # Personalizar colores, formato, secciones
    print("\n" + "="*70)
    print("🎨 MI TERMINAL PERSONALIZADA")  # ← Cambiar título
    print("="*70)
    
    # Agregar nueva sección
    print("\n⭐ Comandos Favoritos:")
    print("  /reporte    - Mi comando favorito")
    # ... resto del código
```

#### Modificar Banner
```python
# En cli_interface.py

@staticmethod
def print_banner():
    banner = r"""
    ╔════════════════════════════════════╗
    ║     TU BANNER PERSONALIZADO        ║
    ╚════════════════════════════════════╝
    """
    print(CLI.color_text(banner, 'cyan', bold=True))
```

### Extender Funcionalidad

#### Crear subclase de CustomCAITerminal
```python
class MiTerminalExtendida(CustomCAITerminal):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.estadisticas = {'comandos_ejecutados': 0}
    
    def run_agent_query(self, query: str):
        # Pre-procesamiento
        print("🔍 Procesando tu solicitud...")
        self.estadisticas['comandos_ejecutados'] += 1
        
        # Ejecutar query original
        super().run_agent_query(query)
        
        # Post-procesamiento
        print(f"📈 Total comandos: {self.estadisticas['comandos_ejecutados']}")
```

---

## 📈 Roadmap de Mejoras

### Completado ✅
- [x] Arquitectura modular
- [x] Comandos personalizados
- [x] Gestión de sesiones
- [x] Sistema de costos mejorado
- [x] Documentación completa

### Próximas mejoras 🚧
- [ ] Autocompletado de comandos
- [ ] History de comandos (↑/↓)
- [ ] Temas de colores personalizables
- [ ] Exportación de sesiones a diferentes formatos
- [ ] Dashboard web complementario

---

**Última actualización:** 2025-11-29  
**Versión:** v2.0 - Arquitectura Modular  
**Autores:** dui-IA Team
