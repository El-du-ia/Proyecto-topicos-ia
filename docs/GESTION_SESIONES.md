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
1    fc0f7408-604     30/11/2025           22         002650     un resuemn vijo               
2    dbe30747-03a     30/11/2025           0          121119                                   
3    d6f92af5-3ca     30/11/2025           2          002604     hola                          
4    bd5f315d-532     30/11/2025           0          114815                                   
5    bc82e497-5be     30/11/2025           0          110817                                   
6    bb7090f9-89f     30/11/2025           0          120657                                   
7    bae6c614-dd5     30/11/2025           0          115556                                   
8    b832484e-521     30/11/2025           0          110505                                   
9    b6ec2cce-eb2     30/11/2025           0          114555                                   
10   9443f801-d00     30/11/2025           36         112058     hola                          
11   92768461-6db     30/11/2025           0          114937                                   
12   8c4eac9f-09e     30/11/2025           0          005749                                   
13   82527d74-9af     30/11/2025           0          114739                                   
14   7b58ffb2-13d     30/11/2025           0          121330                                   
15   75b645dd-79c     30/11/2025           2          110100     dame un resumen de la conversa
16   70414aca-549     30/11/2025           0          115240                                   
17   69646a2d-519     30/11/2025           26         113546     dame un analisis de lo que se 
18   657557fc-f28     30/11/2025           0          122246                                   
19   556aa820-89f     30/11/2025           0          112730                                   
20   1c59b53d-ed4     30/11/2025           0          114903                                   
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
💾 Session ID de CAI actualizado: 0a28b9e5-8aa4-44...
📝 Los nuevos mensajes se guardarán en: logs/cai_0a28b9e5...jsonl

💉 Historial inyectado al modelo del agente: 3 mensajes
✅ ✓ Sesión cargada: 3 mensajes
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

**Nota Importante:** Observa que ahora indica "Session ID de CAI actualizado" - esto significa que todos los nuevos mensajes se guardarán en la misma sesión original, no en una nueva.

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

### 2. Reutilización de Sesiones (ACTUALIZADO ✨)

**PROBLEMA ANTERIOR:**
- Cada inicio creaba una sesión NUEVA
- `/load` solo cargaba el contexto
- Nuevos mensajes se guardaban en sesión diferente
- ❌ Perdías continuidad real

**SOLUCIÓN ACTUAL:**

Cuando haces `/load`, ahora:

1. ✅ **Carga el contexto** de la sesión (mensajes anteriores)
2. ✅ **Cambia el `session_id` de CAI** al de la sesión cargada
3. ✅ **Actualiza el archivo de log** para escribir en el original
4. ✅ **Inyecta el historial** en `agent.model.message_history`

**Resultado:**
- Todos los nuevos mensajes se guardan en la **misma sesión**
- Conversación verdaderamente continua entre reinicios
- Un solo archivo de log por conversación completa

```python
def _reuse_cai_session(self, session_id: str, log_filepath: str):
    """Reutiliza una sesión existente de CAI"""
    from cai.cli import get_session_recorder
    
    # Obtener el recorder global (singleton)
    recorder = get_session_recorder()
    
    # Extraer UUID con regex robusto
    uuid_pattern = r'cai_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})_'
    match = re.search(uuid_pattern, os.path.basename(log_filepath))
    
    if match:
        full_session_id = match.group(1)
        
        # ¡CLAVE! Cambiar el session_id del recorder
        recorder.session_id = full_session_id
        recorder.filename = log_filepath
        
        # Ahora los nuevos mensajes se guardan en la sesión original
```

### 3. Manejo de Mensajes con Tool Calls

**Tipos de Mensajes del Asistente:**

1. **Solo Texto** (`content` tiene string):
   ```json
   {
     "role": "assistant",
     "content": "He completado el escaneo..."
   }
   ```

2. **Solo Tool Calls** (`content` es `None`):
   ```json
   {
     "role": "assistant",
     "content": null,
     "tool_calls": [
       {
         "function": {"name": "nmap_scan", "arguments": "..."}
       }
     ]
   }
   ```

3. **Texto + Tool Calls** (ambos):
   ```json
   {
     "role": "assistant",
     "content": "Voy a escanear esa IP...",
     "tool_calls": [...]
   }
   ```

**¿Por qué `content: None`?**

Cuando el agente decide ejecutar una herramienta:
- No necesita decir nada todavía → `content: None`
- Después la herramienta se ejecuta
- Luego el agente explica el resultado con texto

**Visualización Mejorada:**

Ahora cuando ves el historial:
```
👤 Usuario: escanea mi red local
🤖 Asistente: [🔧 Ejecutó: nmap_ping_sweep]
🤖 Asistente: Se encontraron 6 dispositivos activos...
```

En lugar de:
```
🤖 Asistente: [Sin contenido de texto]  # ❌ Poco informativo
```

### 4. Envío al LLM

**❓ Pregunta común:** ¿Se reenvía todo el historial en cada mensaje?

**✅ Respuesta:** **NO**. El historial se inyecta **UNA SOLA VEZ** al cargar la sesión.

---

#### 🔄 Flujo Detallado

**1️⃣ Al cargar sesión (`/load abc123`):**

```python
def load_session_context(session_id):
    # Cargar mensajes desde logs
    messages = session_mgr.get_session_context(session_id)
    
    # ¡CLAVE! Inyectar UNA VEZ al modelo
    agent.model.message_history.clear()
    for msg in messages:
        agent.model.add_to_message_history(msg)
    
    # Ahora agent.model.message_history tiene:
    # [msg1, msg2, msg3, ..., msgN]
```

**Estado después de `/load`:**
```python
agent.model.message_history = [
    {"role": "user", "content": "hola"},               # ← Mensaje 1 (cargado)
    {"role": "assistant", "content": "¡Hola!..."},     # ← Mensaje 2 (cargado)
    {"role": "user", "content": "escanea 192.168.1.1"}, # ← Mensaje 3 (cargado)
    {"role": "assistant", "content": "Escaneando..."}  # ← Mensaje 4 (cargado)
]
```

---

**2️⃣ Usuario escribe nuevo mensaje:**

```python
🤖 dui-IA > dame un resumen

# run_agent_query("dame un resumen")
```

**¿Qué se envía al LLM?**

```python
# ❌ INCORRECTO (lo que podrías pensar):
Runner.run_sync(
    starting_agent=agent,
    input=[msg1, msg2, msg3, msg4, "dame un resumen"]  # ❌ NO enviamos todo
)

# ✅ CORRECTO (lo que realmente pasa):
Runner.run_sync(
    starting_agent=agent,
    input="dame un resumen"  # ← Solo el mensaje nuevo
)
```

**¿Por qué funciona?**

Porque **CAI automáticamente usa `agent.model.message_history`**:

```python
# Internamente, CAI hace esto:
def Runner.run_sync(starting_agent, input):
    # 1. Tomar el historial del modelo
    messages = starting_agent.model.message_history.copy()
    
    # 2. Añadir el nuevo mensaje
    messages.append({"role": "user", "content": input})
    
    # 3. Enviar AL LLM (Gemini/GPT)
    llm_response = send_to_llm(messages)  # ← Aquí va TODO el contexto
    
    # 4. Añadir respuesta al historial
    starting_agent.model.message_history.append({
        "role": "assistant", 
        "content": llm_response
    })
```

---

**3️⃣ Después de la respuesta:**

```python
# Estado actualizado automáticamente:
agent.model.message_history = [
    {"role": "user", "content": "hola"},                    # ← Cargado
    {"role": "assistant", "content": "¡Hola!..."},          # ← Cargado
    {"role": "user", "content": "escanea 192.168.1.1"},     # ← Cargado
    {"role": "assistant", "content": "Escaneando..."},      # ← Cargado
    {"role": "user", "content": "dame un resumen"},         # ← Nuevo (añadido)
    {"role": "assistant", "content": "Resumen: ..."}        # ← Respuesta (añadida)
]

# Luego sincronizamos a conversation_history (local)
_sync_history_from_agent()
```

---

#### 📊 Comparación Visual

**❌ Lo que NO hacemos (ineficiente):**
```
Usuario: "dame resumen"
    ↓
Construir: [msg1, msg2, msg3, msg4, "dame resumen"]
    ↓
Enviar todo al LLM (5 mensajes) ← ❌ Reenviar historial cada vez
    ↓
Respuesta
```

**✅ Lo que SÍ hacemos (eficiente):**
```
/load abc123
    ↓
Inyectar historial UNA VEZ → agent.model.message_history
    ↓
Usuario: "dame resumen"
    ↓
Runner.run_sync(input="dame resumen")  ← Solo mensaje nuevo
    ↓
CAI toma agent.model.message_history (ya tiene todo)
    ↓
Añade mensaje nuevo → Envía al LLM
    ↓
Respuesta → Añade a agent.model.message_history
```

---

#### 🎯 Respuesta a tu pregunta:

**"¿Memory/history carga todo el historial nuevamente cada vez?"**

**NO.** El flujo es:

1. **Una sola vez** (al `/load`):
   - Cargar historial desde `logs/` o `memory/`
   - Inyectar a `agent.model.message_history`

2. **Cada mensaje nuevo** (queries posteriores):
   - Solo enviar el mensaje nuevo
   - CAI usa automáticamente el historial que YA está en `agent.model.message_history`

3. **El LLM recibe** (cada vez):
   - TODO el contexto (historial completo + mensaje nuevo)
   - Pero nosotros no lo reenviamos manualmente
   - CAI lo gestiona internamente

---

#### 💡 Ventajas de este diseño:

1. **Eficiencia en código:**
   - No reconstruimos el historial cada vez
   - Solo pasamos el mensaje nuevo

2. **Consistencia:**
   - `agent.model.message_history` es la fuente de verdad
   - CAI lo gestiona automáticamente

3. **Contexto completo al LLM:**
   - El LLM sí recibe TODO el historial
   - Pero CAI se encarga de eso internamente
   - Nosotros solo inyectamos una vez al cargar

4. **Sincronización:**
   - Después de cada respuesta: `_sync_history_from_agent()`
   - Mantiene `conversation_history` actualizado

---

**Ventajas:**
- ✅ Eficiente: historial se inyecta una vez, no se reenvía manualmente
- ✅ CAI maneja el contexto internamente (toma `agent.model.message_history`)
- ✅ El LLM SÍ recibe contexto completo (CAI se encarga)
- ✅ Sincronización automática de ambos historiales

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
3. **Reanudación Real**: Nuevos mensajes se guardan en la sesión original (no en sesión nueva)
4. **Búsqueda Rápida**: Encuentra sesiones antiguas fácilmente
5. **Auditoría Completa**: Logs detallados de cada interacción
6. **Carga Instantánea**: Contexto disponible inmediatamente
7. **Sincronización Automática**: Dos historiales (local y CAI) siempre consistentes
8. **Manejo Robusto**: Tolera mensajes con `content: None` (tool calls)

## ⚙️ Detalles Técnicos

### Sincronización de Historiales

El sistema mantiene **dos historiales** que se mantienen sincronizados para diferentes propósitos:

#### 📋 Historial 1: `conversation_history` (Local/Simple)

**Propósito:** Interfaz con el usuario
- 📍 **Ubicación:** `src/ui/session_commands.py`
- 💾 **Persistencia:** `memory/{session_id}_memory.json`
- 📊 **Formato:** Lista simple de diccionarios

**Estructura:**
```python
conversation_history = [
    {
        "role": "user",
        "content": "escanea 192.168.1.1",
        "timestamp": "2025-11-30T12:00:00"
    },
    {
        "role": "assistant",
        "content": "He completado el escaneo...",
        "timestamp": "2025-11-30T12:00:15"
    }
]
```

**Usado para:**
- ✅ Mostrar resúmenes al usuario (`/load`, `/history`)
- ✅ Estadísticas de conversación (`/info`)
- ✅ Búsqueda de sesiones (`/search`)
- ✅ Persistencia entre reinicios

**Características:**
- Solo mensajes `user` y `assistant`
- No incluye mensajes `tool` (internos de CAI)
- Incluye timestamp para tracking
- Formato legible y simple

---

#### 🤖 Historial 2: `agent.model.message_history` (CAI/OpenAI)

**Propósito:** Comunicación con el LLM
- 📍 **Ubicación:** Interno de CAI (`OpenAIChatCompletionsModel`)
- 💾 **Persistencia:** Solo en memoria (RAM)
- 📊 **Formato:** Protocolo OpenAI Chat Completions

**Estructura Completa:**
```python
agent.model.message_history = [
    # 1. Mensaje del usuario
    {
        "role": "user",
        "content": "escanea 192.168.1.1"
    },
    
    # 2. Asistente decide usar herramienta (content puede ser None)
    {
        "role": "assistant",
        "content": None,  # ← Puede ser None
        "tool_calls": [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "nmap_scan",
                    "arguments": '{"target": "192.168.1.1"}'
                }
            }
        ]
    },
    
    # 3. Resultado de la herramienta
    {
        "role": "tool",
        "tool_call_id": "call_abc123",
        "content": "Host is up. Ports: 22/open, 80/open..."
    },
    
    # 4. Asistente interpreta el resultado
    {
        "role": "assistant",
        "content": "He completado el escaneo de 192.168.1.1..."
    }
]
```

**Usado para:**
- ✅ Enviar contexto al LLM (Gemini, GPT, etc.)
- ✅ Mantener estado de tool calls
- ✅ Seguimiento de ejecución de herramientas
- ✅ Validación de protocolo OpenAI

**Características:**
- Incluye mensajes `user`, `assistant`, y `tool`
- Sigue especificación OpenAI Chat Completions
- `content` puede ser `None` en tool calls
- CAI lo gestiona automáticamente

---

#### 🔄 ¿Por qué Dos Historiales?

**Separación de Responsabilidades:**

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO PREGUNTA                          │
│              "escanea 192.168.1.1"                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴────────────────────┐
        │                                        │
        ↓                                        ↓
┌──────────────────────┐            ┌──────────────────────────┐
│ conversation_history │            │ agent.model.             │
│      (Simple)        │            │ message_history          │
│                      │            │    (OpenAI)              │
├──────────────────────┤            ├──────────────────────────┤
│ ✅ Guarda mensaje    │            │ ✅ Guarda mensaje        │
│ ✅ Con timestamp     │            │ ✅ Sin timestamp         │
│ ❌ Sin tool messages │            │ ✅ Con tool messages     │
│ ✅ Para mostrar UI   │            │ ✅ Para enviar LLM       │
└──────────────────────┘            └──────────────────────────┘
        │                                        │
        │      Agente ejecuta herramienta        │
        │      (nmap_scan)                       │
        │                                        │
        │                                        ↓
        │                            ┌──────────────────────┐
        │                            │ + assistant (tool)   │
        │                            │ + tool (resultado)   │
        │                            │ + assistant (texto)  │
        │                            └──────────────────────┘
        │                                        │
        │        Se sincronizan después          │
        │                                        │
        ↓                                        ↓
┌──────────────────────┐            ┌──────────────────────────┐
│ Actualizado con      │   ◄────    │ Filtrado: solo user/     │
│ solo mensajes de     │    SYNC    │ assistant con content    │
│ texto del asistente  │            │                          │
└──────────────────────┘            └──────────────────────────┘
```

---

#### 🔄 Proceso de Sincronización

**Método:** `_sync_history_from_agent()`

```python
def _sync_history_from_agent(self):
    """Sincroniza desde agent.model.message_history (fuente de verdad)"""
    
    # 1. Obtener historial completo de CAI
    agent_history = self.agent.model.message_history
    
    # 2. Verificar si hay diferencia
    if len(agent_history) != len(self.conversation_history):
        
        # 3. Filtrar y transformar
        self.conversation_history = [
            {
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': msg.get('timestamp', datetime.now().isoformat())
            }
            for msg in agent_history
            # ¡CLAVE! Solo user/assistant, NO tool messages
            if msg['role'] in ['user', 'assistant'] and msg.get('content')
        ]
```

**¿Cuándo se sincroniza?**
- ✅ Después de cada respuesta del agente
- ✅ Al cargar una sesión (inicialmente)
- ✅ Solo si hay diferencia de longitud (eficiencia)

**¿Por qué `agent.model.message_history` es la "fuente de verdad"?**
- CAI lo gestiona automáticamente
- Incluye tool calls que nosotros no vemos
- Runner.run_sync() lo actualiza directamente
- Garantiza consistencia con el LLM

---

#### 📊 Ejemplo Completo de Sincronización

**Escenario:** Usuario pide escaneo, agente ejecuta `nmap_scan`

**1. Estado Inicial:**
```python
conversation_history = []
agent.model.message_history = []
```

**2. Usuario escribe:**
```python
# add_user_message() añade a ambos:
conversation_history = [
    {"role": "user", "content": "escanea 192.168.1.1", "timestamp": "..."}
]

agent.model.message_history = [
    {"role": "user", "content": "escanea 192.168.1.1"}
]
```

**3. Runner.run_sync() ejecuta el agente:**
```python
# CAI añade automáticamente:
agent.model.message_history = [
    {"role": "user", "content": "escanea 192.168.1.1"},
    {"role": "assistant", "content": None, "tool_calls": [...]},  # ← Tool call
    {"role": "tool", "tool_call_id": "...", "content": "..."},    # ← Resultado
    {"role": "assistant", "content": "He completado el escaneo..."} # ← Respuesta
]

# Pero conversation_history sigue igual (solo tiene 1 mensaje)
```

**4. Sincronización automática:**
```python
_sync_history_from_agent()

# Ahora conversation_history se actualiza:
conversation_history = [
    {"role": "user", "content": "escanea 192.168.1.1", "timestamp": "..."},
    # No incluye mensaje con tool_calls (content: None)
    # No incluye mensaje tool (interno)
    {"role": "assistant", "content": "He completado el escaneo...", "timestamp": "..."}
]
```

**5. Usuario ve historial limpio:**
```
👤 Usuario: escanea 192.168.1.1
🤖 Asistente: He completado el escaneo...
```

Sin ver los detalles internos de tool calls.

---

#### ⚠️ Casos Especiales

**Caso 1: Mensaje con `content: None`**
```python
# En agent.model.message_history:
{"role": "assistant", "content": None, "tool_calls": [...]}

# Se filtra en sincronización (no se añade a conversation_history)
# Porque: if msg.get('content')  # None es falsy
```

**Caso 2: Solo Tool Calls sin respuesta de texto**
```python
agent.model.message_history = [
    {"role": "user", "content": "escanea"},
    {"role": "assistant", "content": None, "tool_calls": [...]},
    {"role": "tool", "content": "..."}
    # ← Agente no genera respuesta de texto adicional
]

# conversation_history solo tiene:
[{"role": "user", "content": "escanea"}]
# No hay mensaje del asistente visible para el usuario
```

**Caso 3: Múltiples Tool Calls en cadena**
```python
# CAI puede hacer múltiples tool calls:
agent.model.message_history = [
    {"role": "user", ...},
    {"role": "assistant", "tool_calls": [...]},  # Tool 1
    {"role": "tool", ...},
    {"role": "assistant", "tool_calls": [...]},  # Tool 2
    {"role": "tool", ...},
    {"role": "assistant", "content": "Resultado final..."}
]

# conversation_history solo muestra inicio y fin:
[
    {"role": "user", ...},
    {"role": "assistant", "content": "Resultado final..."}
]
```

---

#### 🎯 Ventajas de Este Diseño

1. **Separación de Concerns:**
   - UI solo maneja mensajes relevantes para el usuario
   - CAI maneja protocolo completo de OpenAI

2. **Eficiencia:**
   - No duplicamos mensajes `tool` innecesariamente
   - Sincronización solo cuando hay cambios

3. **Flexibilidad:**
   - Podemos formatear `conversation_history` como queramos
   - No afectamos el protocolo interno de CAI

4. **Robustez:**
   - Si CAI cambia su formato, solo ajustamos `_sync_history_from_agent()`
   - `conversation_history` permanece estable

5. **Debugging:**
   - Dos vistas del mismo estado
   - Fácil comparar y detectar inconsistencias

### Validación Robusta del Session ID

El sistema usa **múltiples fallbacks** para extraer el UUID:

1. **Regex Pattern** (más robusto):
   ```python
   uuid_pattern = r'cai_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})_'
   match = re.search(uuid_pattern, filename)
   ```

2. **Split por `_`** (fallback):
   ```python
   parts = filename.split('_')
   full_session_id = parts[1]  # El UUID
   ```

3. **Session ID original** (último fallback):
   ```python
   full_session_id = session_id  # Usar el pasado como parámetro
   ```

### Manejo de Errores

- ✅ Valida que el archivo de log existe antes de usarlo
- ✅ Verifica longitud mínima del UUID (>8 caracteres)
- ✅ Traceback detallado solo en modo DEBUG
- ✅ Continúa funcionando aunque falle la reutilización de sesión

## ⚠️ Consideraciones

### Privacidad

- Los logs contienen **TODO** lo que escribes y el agente responde
- Se guardan en texto plano en `logs/` y `memory/`

### Almacenamiento

- Cada sesión puede ocupar varios KB o MB según la conversación
- Los logs JSONL crecen con cada mensaje
- Limpia sesiones antiguas periódicamente

### Performance

- Cargar sesiones con 100+ mensajes puede ser lento
- El LLM tiene límites de tokens de contexto
- Para conversaciones muy largas, considera resumir

## 🔮 Mejoras Futuras

- [ ] Exportar sesiones a PDF/Markdown(reportes)
- [ ] Comprimir logs antiguos automáticamente
- [ ] Etiquetas/tags para organizar sesiones
- [ ] Fusionar múltiples sesiones relacionadas
- [ ] Backup automático a la nube (AWS S3)
- [x] **Reutilización real de sesiones** (implementado ✅)
- [x] **Sincronización de historiales** (implementado ✅)
- [x] **Manejo robusto de tool calls** (implementado ✅)

## 🐛 Bugs Corregidos (v1.1)

### Bug #1: Sesiones fragmentadas
**Problema:** Los nuevos mensajes se guardaban en sesión diferente a la cargada.
**Solución:** Ahora el `session_id` de CAI se actualiza al cargar una sesión.

### Bug #2: Crash con `content: None`
**Problema:** Error `TypeError: object of type 'NoneType' has no len()` al mostrar historial.
**Solución:** Manejo explícito de mensajes con `content: None` (tool calls).

### Bug #3: Desincronización de historiales
**Problema:** `conversation_history` y `agent.model.message_history` podían diferir.
**Solución:** Método `_sync_history_from_agent()` sincroniza después de cada respuesta.

### Bug #4: Código duplicado
**Problema:** Construía historial para enviar al agente pero no lo usaba.
**Solución:** Eliminado código innecesario, ahora confía en `agent.model.message_history`.

**Autor:** dui-IA Team  
**Última actualización:** 2025-11-30 ✨