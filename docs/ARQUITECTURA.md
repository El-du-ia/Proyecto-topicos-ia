# Arquitectura de dui-IA v2

Se conserva la arquitectura de CAI (un **agente** con instrucciones y
**herramientas**, ejecutado por un **runner**), pero con un núcleo propio de
unas pocas centenas de líneas que controlamos por completo.

```
┌──────────────────────────────────────────────────────────────────┐
│ ui/terminal.py           Terminal (rich + prompt_toolkit)        │
│   comandos /…, banner, paneles, diálogo de confirmación          │
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
