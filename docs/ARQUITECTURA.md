# Arquitectura de dui-IA v2

Se conserva la arquitectura de CAI (un **agente** con instrucciones y
**herramientas**, ejecutado por un **runner**), pero con un núcleo propio de
unas pocas centenas de líneas que controlamos por completo.

```
┌──────────────────────────────────────────────────────────────────┐
│ ui/                      Terminal (rich + prompt_toolkit)        │
│   comandos /…, streaming, barra de estado, confirmación          │
│   implementa RunHooks ──────────────┐                            │
└──────────────┬──────────────────────┼────────────────────────────┘
               │ run(history, input)  │ confirm(), on_tool_end()…
┌──────────────▼──────────────────────┴────────────────────────────┐
│ agent/runner.py           Runner                                 │
│   1. modelo → 2. ¿tool calls? → 3. validar (args + alcance)      │
│   → 4. confirmar si es sensible → 5. ejecutar → 6. auditar → 1   │
├───────────────┬───────────────────────────┬──────────────────────┤
│ agent/llm.py  │ agent/agent.py            │ security/            │
│ LLMClient     │ Agent: nombre,            │ scope.py  Scope      │
│ └ LiteLLM     │ instrucciones (prompt),   │ audit.py  AuditLog   │
│   (cualquier  │ ToolRegistry              │                      │
│    proveedor) │                           │                      │
└───────────────┴─────────────┬─────────────┴──────────────────────┘
                              │ Tool.invoke(args, ctx)
┌─────────────────────────────▼────────────────────────────────────┐
│ tools/        recon.py (DNS, WHOIS) · reports.py · …             │
│ storage/      sessions.py: SQLite (sesiones, mensajes, auditoría)│
│ compat.py     SO, privilegios, binarios, consejos por sistema    │
│ config.py     Settings (.env / variables DUI_*)                  │
└──────────────────────────────────────────────────────────────────┘
```

## Piezas

### `agent/tools.py`: herramientas
- `@tool` convierte una función en `Tool`. El esquema JSON para el modelo sale de los
  type hints (`str`, `int`, `bool`, `Literal[...]`, `list[...]`, `X | None`) y del
  docstring (descripción + sección `Args:`).
- Metadatos: `sensitive` (pide confirmación), `category`, `risks` (se muestran al
  confirmar), `check` (¿está disponible en este equipo?) y `validator` (validación
  previa, p. ej. del alcance).
- Si la función tiene un parámetro `ctx`, recibe un `ToolContext` con `settings`,
  `scope` y `system`. Ese parámetro no se le muestra al modelo.

### `agent/runner.py`: el ciclo
- Por cada tool call: comprueba que exista → que los argumentos sean JSON →
  que esté disponible → `validate` (argumentos + validador) → **confirmación si es
  sensible** → ejecución → auditoría.
- Los errores no rompen la sesión: se le devuelven al modelo como texto, para que
  los explique.
- `RunHooks` desacopla la interfaz. Por defecto, `confirm()` **rechaza**.
- `max_turns` evita ciclos infinitos y las salidas largas se truncan.

### `agent/llm.py`: modelos
- `LLMClient` es una interfaz mínima (`complete(messages, tools)`). `LiteLLMClient`
  habla con cualquier proveedor. Las pruebas usan un `FakeLLM`.
- Los mensajes siguen el formato de OpenAI, el estándar que LiteLLM traduce a cada
  proveedor.

### `security/`
- `Scope`: decide qué objetivos se pueden analizar de forma activa. Por defecto,
  redes privadas, loopback y link-local; además, lo que diga `DUI_SCOPE` o `/scope add`.
  Un dominio permitido incluye sus subdominios. Un nombre se permite solo si
  **todas** sus IPs están en el alcance. Rechaza objetivos que parecen opciones
  (`-iL`) o caracteres de shell.
- `AuditLog`: un registro por evento (`confirmation`, `tool_execution`, `tool_blocked`,
  `scope_added`) en la tabla `audit` de la sesión actual. Sin base de datos (pruebas),
  queda en memoria.

### `storage/sessions.py`: sesiones (SQLite)
- Un solo archivo, `<datos>/dui.db`, con `sqlite3` de la biblioteca estándar (igual en todos
  los sistemas). Modo WAL y claves foráneas con `ON DELETE CASCADE`.
- `messages.payload` guarda cada mensaje **completo** en formato OpenAI (incluidos
  `tool_calls` y los mensajes `tool`), así que al reanudar el modelo ve exactamente lo
  mismo que antes.
- Cada turno (pregunta → herramientas → respuesta) se guarda en **una transacción**: o se
  guarda entero o no se guarda nada.
- `messages_fts` (FTS5, `remove_diacritics`) indexa el texto para `/search`; lo mantienen
  triggers. Si SQLite no trae FTS5, se busca con `LIKE`.
- Las sesiones sin mensajes no se listan y se eliminan al salir (salvo que tengan auditoría).

```
sessions(id, title, model, created_at, updated_at, message_count)
messages(id, session_id → sessions, seq, role, content, payload JSON, created_at)
audit(id, session_id → sessions, timestamp, event, data JSON)
messages_fts(content)  -- índice de texto completo
```

### `agent/context.py`: contexto en sesiones largas
`select_context` envía al modelo solo los mensajes más recientes (`DUI_MAX_HISTORY`, 60
por defecto, y un límite de caracteres), y siempre empieza en un mensaje del usuario,
para no separar nunca una llamada a herramienta de su resultado (los proveedores
rechazan esos historiales). En la base se conserva todo.

### `ui/`: terminal
| Módulo | Responsabilidad |
|---|---|
| `terminal.py` | Bucle principal, comandos, pantallas, autoguardado y barra de estado |
| `hooks.py` | `TerminalHooks`: spinner, streaming con `rich.Live`, panel por herramienta, confirmación |
| `commands.py` | Catálogo de comandos agrupado, alias en español y autocompletado con descripción |
| `symbols.py` | Íconos con emoji o ASCII; detecta la consola clásica de Windows |
| `banner.py` | Pantalla de inicio: logo en letras grandes (bloques o ASCII) y panel de información |

**Streaming**: si `hooks.streaming` es True, el Runner llama a `llm.complete(..., on_text=...)`.
`LiteLLMClient` pide `stream=True`, entrega cada fragmento de texto y al final reconstruye la
respuesta completa (texto, tool calls y uso) con `litellm.stream_chunk_builder`, así que
el resto del sistema no distingue entre los dos modos. Si el proveedor falla *después* de
mostrar texto, no se reintenta (se duplicaría la respuesta). Con la salida redirigida a un
archivo, el streaming se desactiva solo.

**Por qué la vista previa y no el panel completo en vivo**: una vista en vivo (`rich.Live`)
más alta que la terminal no se puede redibujar; lo que ya subió por el scroll queda en el
historial y cada actualización deja otra copia. Por eso, mientras llega el texto se muestra
una vista previa *transitoria* que nunca supera la altura de la pantalla (solo las últimas
líneas) y, al terminar, se borra y se imprime la respuesta completa en Markdown una sola vez.
`tests/test_terminal_ui.py` lo verifica interpretando la salida con una terminal virtual
(`pyte`, dependencia solo de desarrollo).

### `tools/system.py` y `tools/logs/`: el propio equipo
- `network_interfaces` y `local_connections` usan `psutil` (igual en los tres sistemas).
- `logs/` tiene un backend por sistema que convierte sus registros a `LogEvent`; el resumen
  (`common.summarize`) es el mismo para todos: totales, fuentes, usuarios y orígenes, eventos
  repetidos agrupados.

| Sistema | Fuente | Notas |
|---|---|---|
| Windows | `wevtutil qe ... /f:RenderedXml` | *Security* requiere Administrador; su salida viene en la página ANSI (`mbcs`), no en UTF-8 |
| Linux | `journalctl -o json`, o `/var/log/auth.log`, `secure`, `syslog` | Para ver todo el sistema: root o grupos `adm`/`systemd-journal` |
| macOS | `log show --style ndjson` | Experimental: solo inicios de sesión fallidos y fallas graves |

### `compat.py`
Todo lo que depende del SO: `is_admin()` (Windows: `IsUserAnAdmin`; Unix:
`geteuid`), `find_binary()` (incluidas rutas típicas de Windows como
`C:\Program Files (x86)\Nmap`), `username()` y consejos de elevación y de captura
por sistema.

## Diferencias con v1

| v1 (con CAI) | v2 |
|---|---|
| Confirmación pedida solo en el prompt | Impuesta por el Runner |
| `execute_with_confirmation` nunca se llamaba (auditoría vacía) | Toda ejecución queda auditada |
| Tres sistemas de sesión superpuestos | Uno solo: SQLite con conversación + auditoría |
| Al reanudar se perdían los resultados de herramientas | Se guarda y restaura el mensaje completo |
| `/search` solo miraba el último mensaje | Búsqueda de texto completo (FTS5) |
| Dependía de archivos internos de CAI | Sin dependencia de CAI |
| `os.geteuid`, `which`, `/var/log`: solo Linux | Capa `compat` + herramientas multiplataforma |
| `open()` sin encoding (falla en Windows) | UTF-8 explícito en todo |
| WHOIS con el binario `whois` | RDAP + puerto 43 en Python puro |
| Marcador de reporte que no coincidía | El modelo ofrece el reporte y llama a `generate_report` |
| Solo modelos vía CAI | Cualquier modelo de LiteLLM, incluidos los locales |
