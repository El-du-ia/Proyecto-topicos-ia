# 🖥️ Terminal Personalizada basada en CAI

## 📝 Resumen

Hemos creado una **terminal personalizada** que **extiende el CLI de CAI** con funcionalidades adicionales, manteniendo toda la potencia de CAI pero agregando nuestras propias características.

---

## 🎯 ¿Qué es esto?

En lugar de tener dos terminales separadas:
- ❌ Una terminal tuya (main.py con menú)
- ❌ Una terminal de CAI (run_cai_cli)

Ahora tienes:
- ✅ **Una sola terminal** que combina lo mejor de ambos mundos

---

## 🏗️ Arquitectura

```
┌────────────────────────────────────────────────────────────┐
│                    TU PROGRAMA (main.py)                   │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         CustomCAITerminal (personalizada)            │ │
│  │                                                      │ │
│  │  • Banner personalizado                             │ │
│  │  • Verificación de permisos                         │ │
│  │  • Comandos adicionales (/permisos, /tools, etc.)   │ │
│  │  • Estado del sistema                               │ │
│  │                                                      │ │
│  │  ┌────────────────────────────────────────────────┐ │ │
│  │  │     CLI de CAI (base)                          │ │ │
│  │  │                                                │ │ │
│  │  │  • Procesamiento de input                     │ │ │
│  │  │  • Ejecución del agente                       │ │ │
│  │  │  • Historial y logging                        │ │ │
│  │  │  • Comandos nativos (/help, /cost, etc.)      │ │ │
│  │  └────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

---

## ✨ Características Añadidas

### 1️⃣ Banner Personalizado
```python
# En lugar del banner de CAI, muestra el tuyo
CLI.print_banner()
```

### 2️⃣ Verificación de Permisos
```python
# Muestra si tienes privilegios, puede capturar paquetes, etc.
PermissionChecker.check_and_warn()
```

### 3️⃣ Comandos Personalizados Adicionales

Además de los comandos de CAI (`/help`, `/cost`, `/exit`), agregaste:

| Comando | Descripción |
|---------|-------------|
| `/permisos` | Ver estado de permisos del sistema |
| `/tools` | Listar herramientas disponibles |
| `/examples` | Mostrar ejemplos de uso |
| `/status` | Estado del sistema y sesión |
| `/ayuda` | Ayuda en español |

### 4️⃣ Información de Inicio Mejorada
Muestra consejos útiles al iniciar la terminal.

---

## 💻 Cómo Funciona

### Archivo: `src/ui/custom_terminal.py`

```python
class CustomCAITerminal:
    """Terminal que ENVUELVE el CLI de CAI"""
    
    def __init__(self, agent, show_custom_banner=True, 
                 custom_commands=None):
        # Tu configuración personalizada
        self.agent = agent
        self.custom_commands = custom_commands
    
    def display_startup_info(self):
        # Muestra TU banner y permisos
        CLI.print_banner()
        PermissionChecker.check_and_warn()
    
    def handle_custom_command(self, user_input):
        # Intercepta comandos personalizados ANTES de CAI
        if user_input == '/permisos':
            PermissionChecker.show_permission_status()
            return True
        
        # Si no es comando tuyo, deja que CAI lo maneje
        return False
    
    def run(self):
        # 1. Muestra tu info personalizada
        self.display_startup_info()
        
        # 2. Ejecuta CAI (que maneja todo el loop de input/output)
        run_cai_cli(self.agent)
```

---

## 🔧 Cómo Agregar Más Funciones

### Opción 1: Agregar Comandos Personalizados

En `custom_terminal.py`:

```python
def create_cybersecurity_commands():
    """Tus comandos personalizados"""
    
    def cmd_scan_report():
        """Genera reporte de escaneos"""
        # Tu código aquí
        print("📊 Generando reporte...")
    
    def cmd_save_session():
        """Guarda la sesión actual"""
        # Tu código aquí
        print("💾 Guardando sesión...")
    
    return {
        'report': cmd_scan_report,
        'save': cmd_save_session,
    }
```

Uso:
```bash
🤖 > /report
📊 Generando reporte...
```

### Opción 2: Modificar el Banner

En `src/ui/cli_interface.py`:

```python
@staticmethod
def print_banner():
    # Cambia esto a tu gusto
    banner = r"""
 TU BANNER ASCII AQUÍ
    """
    print(banner)
```

### Opción 3: Interceptar Inputs Antes de CAI

En `custom_terminal.py`, método `handle_custom_command()`:

```python
def handle_custom_command(self, user_input):
    # Preprocesar antes de enviar a CAI
    if user_input.startswith('quick:'):
        # Ejecutar comando rápido
        cmd = user_input[6:]  # Quitar 'quick:'
        self.execute_quick_command(cmd)
        return True
    
    return False  # Dejar que CAI lo maneje
```

---

## 📚 Componentes de CAI que Puedes Usar

### Importables de `cai.cli`:

```python
from cai.cli import (
    Console,              # Terminal con formato
    FuzzyCommandCompleter,  # Autocompletado
    get_user_input,       # Input personalizado
    setup_session_logging,  # Logging de sesión
    display_banner,       # Banner de CAI
    run_cai_cli,          # El loop principal
)
```

### Ejemplo de Uso:

```python
from cai.cli import Console, get_user_input

console = Console()

# Input personalizado con autocompletado
user_input = get_user_input(
    prompt="🤖 > ",
    completer=my_completer
)

# Formatear output
console.print("[green]✓[/green] Completado")
```

---

## 🎨 Personalizaciones Avanzadas

### 1. Cambiar Colores del Prompt

CAI usa `rich.console`, puedes personalizarlo:

```python
from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
})

console = Console(theme=custom_theme)
```

### 2. Agregar Pre/Post Procesamiento

```python
class CustomCAITerminal(CustomCAITerminal):
    
    def preprocess_input(self, user_input):
        """Procesa input antes de enviarlo al agente"""
        # Traducir español a inglés si es necesario
        # Expandir abreviaturas
        # Validar formato
        return processed_input
    
    def postprocess_output(self, agent_output):
        """Procesa output del agente antes de mostrarlo"""
        # Formatear mejor
        # Agregar información adicional
        # Guardar en base de datos
        return formatted_output
```

### 3. Hooks de Eventos

```python
class CustomCAITerminal(CustomCAITerminal):
    
    def on_tool_call(self, tool_name, args):
        """Se ejecuta cuando el agente llama una herramienta"""
        print(f"🛠️  Ejecutando: {tool_name}")
        # Puedes agregar logging, confirmación, etc.
    
    def on_error(self, error):
        """Se ejecuta cuando hay un error"""
        print(f"❌ Error: {error}")
        # Manejo personalizado de errores
```

---

## 🚀 Comparación: Antes vs Ahora

### Antes (dos sistemas separados):

```
Usuario → main.py (menú) → opción 1 → run_cai_cli() → CAI
                         → opción 2 → tu función
                         → opción 3 → tu función
```

Problemas:
- ❌ Dos interfaces diferentes
- ❌ No puedes personalizar CAI fácilmente
- ❌ Funcionalidades duplicadas

### Ahora (sistema unificado):

```
Usuario → main.py (menú) → CustomCAITerminal → run_cai_cli()
                           ↓
                      Tu código + CAI juntos
```

Ventajas:
- ✅ Una sola interfaz
- ✅ Puedes interceptar y personalizar todo
- ✅ Mantienes la potencia de CAI
- ✅ Agregas tus funciones fácilmente

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Agregar Comando de Backup

```python
def cmd_backup():
    """Respalda la sesión actual"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_{timestamp}.jsonl"
    
    # Copiar logs
    shutil.copy("logs/latest.jsonl", backup_file)
    print(f"✅ Backup guardado: {backup_file}")

# Agregarlo
custom_commands = {
    'backup': cmd_backup
}

run_custom_cai_terminal(agent, custom_commands=custom_commands)
```

Uso:
```bash
🤖 > /backup
✅ Backup guardado: backup_20251125_143022.jsonl
```

### Ejemplo 2: Modo Debug

```python
class DebugCAITerminal(CustomCAITerminal):
    
    def __init__(self, *args, debug=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug = debug
    
    def display_startup_info(self):
        super().display_startup_info()
        
        if self.debug:
            print("🐛 MODO DEBUG ACTIVADO")
            print(f"   Herramientas: {len(self.agent.tools)}")
            print(f"   Modelo: {self.agent.model}")

# Usar
terminal = DebugCAITerminal(agent, debug=True)
terminal.run()
```

---

## 🔗 Archivos Relacionados

- `src/ui/custom_terminal.py` - Terminal personalizada (NUEVO)
- `src/ui/cli_interface.py` - Utilidades de interfaz
- `src/core/permissions.py` - Sistema de permisos
- `main.py` - Punto de entrada (usa CustomCAITerminal)

---

## 💡 Mejores Prácticas

1. **No modifiques el código de CAI directamente** - Usa wrappers y extensiones
2. **Intercepta comandos antes de CAI** - Para agregar funcionalidad
3. **Usa los componentes de CAI** - Console, logging, etc.
4. **Mantén la compatibilidad** - Tu terminal debe funcionar como CAI para el usuario
5. **Documenta tus comandos personalizados** - En `/help`

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'cai.cli'"

Asegúrate de tener CAI instalado:
```bash
pip show cai
```

### Los comandos personalizados no funcionan

Verifica que estén registrados:
```python
custom_commands = create_cybersecurity_commands()
print(custom_commands.keys())  # Debe mostrar tus comandos
```

### El banner no aparece

Verifica la configuración:
```python
run_custom_cai_terminal(
    agent,
    show_custom_banner=True  # ← Asegúrate que sea True
)
```

---

**Última actualización:** 2025-11-25  
**Versión:** Terminal Personalizada v1.0
