# Terminal Totalmente Personalizada

## ✨ ¿Qué cambió?

### ANTES ❌
- Se usaba `run_cai_cli()` de CAI directamente
- CAI manejaba todo el loop de input/comandos
- Los comandos personalizados NO funcionaban
- Aparecía el banner de CAI
- Interfaz controlada por CAI, no personalizable

### AHORA ✅
- **Loop personalizado completo** que reemplaza el de CAI
- **Comandos personalizados funcionan** (se procesan antes de CAI)
- **Banner personalizado único** (sin interferencia de CAI)
- **Control total del input/output**
- **Integración transparente con CAI** (solo usamos el Runner para ejecutar queries)

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────┐
│             CustomCAITerminal                       │
│  (Loop personalizado + Comandos personalizados)    │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ Input del usuario
                   ▼
         ┌─────────────────────┐
         │ ¿Es comando /xxx?   │
         └──────┬──────────────┘
                │
       ┌────────┴────────┐
       │                 │
       ▼ SÍ              ▼ NO
┌──────────────┐   ┌─────────────┐
│ Ejecutar     │   │ Enviar a    │
│ comando      │   │ CAI Runner  │
│ personalizado│   │             │
└──────────────┘   └─────────────┘
                         │
                         ▼
                   ┌─────────────┐
                   │ Agente CAI  │
                   │ + Tools     │
                   └─────────────┘
```

---

## 🎯 Comandos Personalizados Disponibles

### Comandos de Sistema
| Comando | Descripción |
|---------|-------------|
| `/help`, `/ayuda` | Muestra ayuda completa |
| `/clear` | Limpia la pantalla |
| `/exit`, `/quit`, `/salir` | Sale de la terminal |
| `/status`, `/estado` | Estado del sistema y sesión |
| `/permisos`, `/perms` | Estado de permisos |
| `/cost` | Costos de API |

### Comandos de Información
| Comando | Descripción |
|---------|-------------|
| `/tools`, `/herramientas` | Lista herramientas disponibles |
| `/examples`, `/ejemplos` | Ejemplos de uso |

### Comandos Personalizados Adicionales
Puedes agregar tus propios comandos pasando un diccionario `custom_commands` al constructor.

---

## 💬 Ejemplos de Uso

### 1️⃣ Usar Comandos Personalizados
```
🤖 > /help
📚 AYUDA DEL TERMINAL PERSONALIZADO
...

🤖 > /permisos
📋 Estado de Permisos del Sistema
...

🤖 > /tools
🛠️  HERRAMIENTAS DE CIBERSEGURIDAD
...
```

### 2️⃣ Interactuar con el Agente
```
🤖 > escanea 192.168.1.1

[El agente procesa la solicitud y ejecuta herramientas]
```

### 3️⃣ Comando Personalizado + Agente
```
🤖 > /examples
💡 EJEMPLOS DE USO
...

🤖 > captura 10 paquetes en eth0
[El agente ejecuta network_sniffer]
```

---

## 🔧 Cómo Funciona el Flujo

### 1. Usuario ingresa texto
```python
def get_user_input(self) -> Optional[str]:
    prompt = CLI.color_text("🤖 > ", 'cyan', bold=True)
    user_input = input(prompt).strip()
    return user_input
```

### 2. Se verifica si es comando personalizado
```python
def handle_custom_command(self, user_input: str) -> Optional[bool]:
    cmd = user_input.strip().lower()
    
    if cmd in ['/exit', '/quit', '/salir']:
        return None  # Salir
    
    if cmd in ['/help', '/ayuda']:
        self.display_help()
        return True  # Comando manejado
    
    # ... más comandos ...
    
    return False  # No es comando, pasar al agente
```

### 3. Si no es comando, se envía al agente
```python
def run_agent_query(self, query: str):
    runner = Runner(agent=self.agent)
    response = runner.run(
        starting_agent=self.agent,
        context_variables=self.context_variables,
        user_message=query
    )
    # Mostrar respuesta
```

### 4. Loop principal
```python
def run(self, max_turns: float = inf):
    self.display_startup_info()
    
    while self.turn_count < max_turns:
        user_input = self.get_user_input()
        if user_input is None:
            break
        
        result = self.handle_custom_command(user_input)
        if result is None:  # Salir
            break
        elif result is True:  # Comando manejado
            continue
        
        # Enviar al agente
        self.run_agent_query(user_input)
        self.turn_count += 1
```

---

## 🎨 Personalización Avanzada

### Agregar Comandos Personalizados

```python
def my_custom_command():
    """Descripción de mi comando"""
    print("¡Hola desde mi comando!")

custom_cmds = {
    'micomando': my_custom_command
}

terminal = CustomCAITerminal(
    agent=mi_agente,
    custom_commands=custom_cmds
)
terminal.run()
```

Luego puedes usar `/micomando` en la terminal.

### Personalizar el Banner

```python
def mi_banner_personalizado():
    print("""
    ╔══════════════════════════════════════╗
    ║      MI HERRAMIENTA PERSONALIZADA    ║
    ╚══════════════════════════════════════╝
    """)

# Modificar display_startup_info en CustomCAITerminal
# o llamar antes de terminal.run()
```

### Agregar Pre/Post Procesamiento

Puedes extender la clase:

```python
class MiTerminalExtendida(CustomCAITerminal):
    def run_agent_query(self, query: str):
        # Pre-procesamiento
        query = query.upper()  # Ejemplo
        
        # Llamar al método original
        super().run_agent_query(query)
        
        # Post-procesamiento
        print("✓ Consulta completada")
```

---

## 🔍 Diferencias Técnicas Clave

### Uso de CAI

#### ANTES (custom_terminal.py antiguo):
```python
def run(self):
    os.environ['CAI_NO_BANNER'] = '1'
    run_cai_cli(self.agent, ...)  # CAI controla TODO
```
❌ Problema: `run_cai_cli` maneja su propio input loop, comandos NO personalizables

#### AHORA:
```python
def run(self):
    self.display_startup_info()
    while ...:
        user_input = self.get_user_input()
        if self.handle_custom_command(user_input):
            continue
        self.run_agent_query(user_input)  # Solo Runner de CAI
```
✅ Solución: Loop propio, comandos propios, CAI solo para ejecutar queries

---

## 📊 Componentes de CAI Utilizados

### ✅ Usamos
- `Agent`: Agente con herramientas
- `Runner`: Para ejecutar queries contra el agente
- `COST_TRACKER`: Para tracking de costos

### ❌ NO Usamos (controlamos nosotros)
- `run_cai_cli()`: Loop de input
- `get_user_input()`: Captura de input
- `display_banner()`: Banner
- `create_key_bindings()`: Bindings de teclado
- `FuzzyCommandCompleter`: Autocompletado

Esto nos da **control total** del flujo.

---

## 🚀 Cómo Ejecutar

```bash
python main.py
# Selecciona opción 1: Modo Interactivo

# Verás:
# - TU banner personalizado
# - Estado de permisos
# - Prompt personalizado: 🤖 >
# - Comandos personalizados funcionando
```

---

## 🐛 Troubleshooting

### Los comandos /xxx no funcionan
✅ SOLUCIONADO: Ahora el loop es propio, todos los comandos funcionan

### Aparece el banner de CAI
✅ SOLUCIONADO: Ya no usamos `run_cai_cli()`, no hay banner de CAI

### El agente no responde
- Verifica que el agente tenga herramientas registradas
- Chequea logs de CAI
- Usa `/status` para ver estado

### Errores de permisos
- Usa `/permisos` para ver estado
- Ejecuta con `sudo` si es necesario
- Revisa `docs/PERMISOS.md`

---

## 📚 Referencias

- `src/ui/custom_terminal.py`: Implementación completa
- `main.py`: Integración en el sistema
- `ejemplo_terminal_personalizada.py`: Ejemplos de extensión
- `docs/PERMISOS.md`: Sistema de permisos

---

## ✨ Ventajas de esta Arquitectura

1. **Control Total**: Manejas cada aspecto del flujo
2. **Extensible**: Fácil agregar comandos/funcionalidades
3. **Transparente**: Integración limpia con CAI
4. **Personalizable**: Banner, prompts, comandos, todo tuyo
5. **Mantenible**: Código claro y bien estructurado
6. **Compatible**: Usa APIs estables de CAI (Agent, Runner)

---

¡Disfruta tu terminal totalmente personalizada! 🎉
