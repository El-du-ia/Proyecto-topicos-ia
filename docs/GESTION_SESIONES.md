# Sistema de Gestión de Sesiones Persistentes 🔄

## 📋 Descripción

El sistema de gestión de sesiones permite **guardar, cargar y reanudar conversaciones** completas con el agente de ciberseguridad. Ahora puedes:

- ✅ **Guardar automáticamente** todas tus conversaciones
- ✅ **Listar sesiones anteriores** con información detallada
- ✅ **Reanudar conversaciones** desde donde las dejaste
- ✅ **Buscar sesiones** por contenido
- ✅ **Mantener el contexto completo** entre sesiones

## 🎯 Problema Resuelto

**ANTES:**
- ❌ Cada vez que cerrabas el agente, perdías el contexto
- ❌ No podías regresar a conversaciones anteriores
- ❌ Tenías que explicar todo desde cero cada vez

**AHORA:**
- ✅ Todo se guarda automáticamente
- ✅ Puedes reanudar cualquier conversación
- ✅ El agente recuerda todo el contexto anterior

## 🚀 Uso Básico

### 1. Listar Sesiones Guardadas

```bash
🤖 dui-IA > /sessions
```

**Output:**
```
====================================================================================================
📚 SESIONES GUARDADAS
====================================================================================================

#    Session ID       Fecha                Mensajes   Usuario    Preview                       
----------------------------------------------------------------------------------------------------
1    0a28b9e5         20251128             3          root       hola                          
2    c88156e8         20251127             5          root       escanea 192.168.1.1           
3    6b0fab72         20251127             10         root       analiza el tráfico de red     
====================================================================================================

💡 Usa '/load <session_id>' para reanudar una sesión
   Ejemplo: /load 0a28b9e5
```

### 2. Reanudar una Sesión

```bash
🤖 dui-IA > /load 0a28b9e5
```

**Output:**
```
🔄 Cargando sesión: 0a28b9e5...
✓ Sesión cargada: 3 mensajes
📅 Creada: 2025-11-28T21:57:54.738632+01:00
📝 Último mensaje: 2025-11-28T22:30:12.125571+01:00

📝 Resumen de la conversación anterior:
----------------------------------------------------------------------
👤 Usuario: hola
🤖 Asistente: ¡Hola! Soy tu asistente de seguridad de red...
👤 Usuario: cuanto es 2 * 2 + 3
🤖 Asistente: ¡Claro! 2 multiplicado por 2 es 4...
----------------------------------------------------------------------
✅ Puedes continuar la conversación desde donde la dejaste
```

### 3. Continuar la Conversación

Una vez cargada, continúa normalmente:

```bash
🤖 dui-IA > ahora escanea 192.168.1.1

# El agente RECUERDA toda la conversación anterior
# y puede hacer referencias a lo que hablaron antes
```

### 4. Buscar Sesiones por Contenido

```bash
🤖 dui-IA > /search escaneo
```

Encuentra todas las sesiones donde hablaste de escaneos.

### 5. Ver Historial Actual

```bash
🤖 dui-IA > /history
```

Muestra todo el historial de la sesión actual.

### 6. Información de la Sesión Actual

```bash
🤖 dui-IA > /info
```

**Output:**
```
====================================================================================================
📊 INFORMACIÓN DE LA SESIÓN ACTUAL
====================================================================================================

🆔 Session ID: 0a28b9e5-8aa4-4403-b676-88382911df02
📝 Estado: Sesión cargada (reanudada)
📅 Creada: 2025-11-28T21:57:54.738632+01:00
🕐 Última actividad: 2025-11-28T22:30:12.125571+01:00
👤 Usuario: root

💬 Estadísticas de Conversación:
   • Total de mensajes: 8
   • Mensajes del usuario: 4
   • Respuestas del asistente: 4
   • Turnos de conversación: 4

🖥️  Sistema:
   • Usuario actual: kali
   • Directorio de trabajo: /home/kali/Proyecto_Topicos_IA/Proyecto-topicos-ia
   • Privilegios: ROOT

🤖 Agente:
   • Nombre: Network Security Analyzer
   • Herramientas registradas: 14

📁 Archivos:
   • Logs: logs/
   • Memoria: memory/
   • Archivos de esta sesión: 1

💰 Costos:
   • Costo de esta sesión: $0.000234
====================================================================================================
```

## 📁 Estructura de Datos

### Logs de Sesión (JSONL)

Ubicación: `logs/cai_{session_id}_{timestamp}_{user}_{os}_{ip}.jsonl`

Cada línea es un evento JSON:

```json
{"event": "session_start", "timestamp": "...", "session_id": "..."}
{"event": "user_message", "content": "hola", "timestamp": "..."}
{"event": "assistant_message", "content": "¡Hola!...", "timestamp": "..."}
{"model": "gemini/gemini-2.5-flash", "messages": [...], "usage": {...}}
```

### Memoria Conversacional (JSON)

Ubicación: `memory/{session_id}_memory.json`

```json
{
  "metadata": {
    "session_id": "0a28b9e5...",
    "created_at": "2025-11-28T21:57:54",
    "last_updated": "2025-11-28T22:30:12"
  },
  "messages": [
    {
      "role": "user",
      "content": "hola",
      "timestamp": "2025-11-28T21:57:54"
    },
    {
      "role": "assistant",
      "content": "¡Hola! Soy tu asistente...",
      "timestamp": "2025-11-28T21:58:03"
    }
  ]
}
```

## 🔧 API de SessionManager

### Importar

```python
from src.models.session_manager import SessionManager

session_mgr = SessionManager()
```

### Métodos Principales

#### `list_sessions(limit=20)`

Lista todas las sesiones ordenadas por fecha.

```python
sessions = session_mgr.list_sessions(limit=10)
for session in sessions:
    print(f"ID: {session['session_id']}")
    print(f"Mensajes: {session['total_interactions']}")
```

#### `load_session(session_id)`

Carga una sesión completa con todos sus datos.

```python
session_data = session_mgr.load_session("0a28b9e5")
if session_data:
    messages = session_data['messages']
    events = session_data['events']
```

#### `get_session_context(session_id)`

Obtiene solo los mensajes para reanudar (más ligero).

```python
context = session_mgr.get_session_context("0a28b9e5")
# Retorna: [{"role": "user", "content": "..."}, ...]
```

#### `search_sessions(query, limit=10)`

Busca sesiones por contenido.

```python
results = session_mgr.search_sessions("escaneo de red")
```

#### `get_session_statistics()`

Obtiene estadísticas generales.

```python
stats = session_mgr.get_session_statistics()
print(f"Total sesiones: {stats['total_sessions']}")
print(f"Total mensajes: {stats['total_messages']}")
```

## 💻 Comandos de Terminal

| Comando | Descripción |
|---------|-------------|
| `/sessions` | Lista todas las sesiones guardadas |
| `/load <id>` | Carga y reanuda una sesión específica |
| `/search <texto>` | Busca sesiones que contengan ese texto |
| `/history` | Muestra el historial de la sesión actual |
| `/info` | Información detallada de la sesión actual |

## 🎬 Ejemplo Completo

### Sesión 1: Crear y trabajar

```bash
$ python main.py

🤖 dui-IA > escanea 192.168.1.1
[Agente escanea la red]

🤖 dui-IA > qué puertos encontraste abiertos
[Agente responde basándose en el escaneo anterior]

🤖 dui-IA > /exit
```

### Sesión 2: Reanudar (días después)

```bash
$ python main.py

🤖 dui-IA > /sessions
[Ve lista de sesiones]

🤖 dui-IA > /load c88156e8
✓ Sesión cargada: 4 mensajes

🤖 dui-IA > recuérdame qué puertos estaban abiertos

[El agente RECUERDA el escaneo de hace días y responde]
```

## 🔍 Cómo Funciona Internamente

### 1. Guardado Automático

Cuando usas el agente, **TODO se guarda automáticamente**:

- CAI guarda logs en formato JSONL
- ConversationMemory guarda mensajes estructurados
- Cada mensaje se timestampea

### 2. Carga de Contexto

Cuando haces `/load`:

1. SessionManager lee el archivo JSONL
2. Extrae todos los mensajes (user + assistant)
3. Los carga en `conversation_history`
4. El siguiente query incluye este historial

### 3. Envío al LLM

Cuando escribes un mensaje:

```python
# Se construyen los mensajes incluyendo historial
messages = [
    # Mensajes antiguos de la sesión cargada
    {"role": "user", "content": "escanea 192.168.1.1"},
    {"role": "assistant", "content": "He escaneado..."},
    # Tu nuevo mensaje
    {"role": "user", "content": "qué puertos encontraste"}
]

# Se envía todo al LLM
response = Runner.run_sync(
    starting_agent=agent,
    input=new_query,
    # El historial le da contexto al agente
)
```

El LLM ve **TODA la conversación anterior** y responde con contexto completo.

## 🛠️ Ejemplo de Uso Programático

```python
#!/usr/bin/env python3
from src.models.session_manager import SessionManager
from src.ui.custom_terminal import CustomCAITerminal
from cai.agents.network_traffic_analyzer import network_security_analyzer_agent

# Crear sesión normal
terminal = CustomCAITerminal(network_security_analyzer_agent)
terminal.run()

# --- Más tarde, reanudar ---

# Listar sesiones
session_mgr = SessionManager()
sessions = session_mgr.list_sessions()

# Reanudar la última sesión
last_session_id = sessions[0]['session_id']

terminal_resumed = CustomCAITerminal(
    network_security_analyzer_agent,
    session_id=last_session_id  # ¡Clave!
)
terminal_resumed.run()  # Continúa con contexto completo
```

## 📊 Ventajas

1. **Persistencia Total**: Nada se pierde, todo queda guardado
2. **Contexto Continuo**: El agente recuerda conversaciones pasadas
3. **Búsqueda Rápida**: Encuentra sesiones antiguas fácilmente
4. **Auditoría Completa**: Logs detallados de cada interacción
5. **Reanudación Instantánea**: Carga rápida de contexto

## ⚠️ Consideraciones

### Privacidad

- Los logs contienen **TODO** lo que escribes y el agente responde
- Se guardan en texto plano en `logs/` y `memory/`
- Si trabajas con datos sensibles, considera encriptación

### Almacenamiento

- Cada sesión puede ocupar varios KB o MB según la conversación
- Los logs JSONL crecen con cada mensaje
- Limpia sesiones antiguas periódicamente

### Performance

- Cargar sesiones con 100+ mensajes puede ser lento
- El LLM tiene límites de tokens de contexto
- Para conversaciones muy largas, considera resumir

## 🔮 Mejoras Futuras

- [ ] Exportar sesiones a PDF/Markdown
- [ ] Comprimir logs antiguos automáticamente
- [ ] Base de datos SQLite para búsquedas más rápidas
- [ ] Etiquetas/tags para organizar sesiones
- [ ] Fusionar múltiples sesiones relacionadas
- [ ] Análisis de sentimiento en conversaciones
- [ ] Backup automático a la nube (AWS S3)

**Autor:** dui-IA Team  
**Última actualización:** 2025-11-29