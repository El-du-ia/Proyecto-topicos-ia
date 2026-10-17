# dui-IA · Agente inteligente de ciberseguridad 🛡️

Asistente de ciberseguridad para personas **sin conocimientos técnicos**: ejecuta
herramientas de análisis, **pide confirmación antes de cualquier acción sensible**
y **explica los resultados en lenguaje simple**.

> **v2 en desarrollo** (rama `v2`). Ya no depende de CAI: conserva su
> arquitectura (Agente → Runner → Herramientas) con un núcleo propio,
> multiplataforma y compatible con cualquier modelo de lenguaje.
> El código de v1 está en [legacy/](legacy/) como referencia.
> Avance: [docs/PLAN_V2.md](docs/PLAN_V2.md).

## Filosofía

1. **Confirmación obligatoria**: las herramientas sensibles (escaneos, capturas)
   no se ejecutan sin que el usuario lo apruebe. La impone el código, no el prompt.
2. **Alcance permitido**: solo se analizan objetivos autorizados. Por defecto, solo
   redes privadas o locales; cualquier otro objetivo hay que agregarlo de forma explícita.
3. **Explicaciones simples**: cada resultado técnico se traduce, con nivel de riesgo
   y recomendaciones.
4. **Todo queda registrado**: cada confirmación y ejecución se guarda en la auditoría.
5. **Multiplataforma**: Windows y Linux (macOS en camino), con las mismas herramientas.
6. **Cualquier LLM**: Gemini, OpenAI, Anthropic, etc., o modelos locales (Ollama, LM Studio).

## Instalación

Se necesita [uv](https://docs.astral.sh/uv/). uv instala la versión de Python
correcta (3.12) por su cuenta, así que no hace falta instalarla aparte.

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
git clone https://github.com/El-du-ia/Proyecto-topicos-ia.git
cd Proyecto-topicos-ia
git checkout v2
uv sync
copy .env.example .env    # y edita .env con tu API key
```

**Linux / macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/El-du-ia/Proyecto-topicos-ia.git
cd Proyecto-topicos-ia
git checkout v2
uv sync
cp .env.example .env      # y edita .env con tu API key
```

Comprueba que todo esté bien:

```bash
uv run dui-ia --check
```

## Uso

```bash
uv run dui-ia                                   # usa el modelo de .env
uv run dui-ia --model ollama_chat/llama3.1 --api-base http://localhost:11434
uv run dui-ia --scope 203.0.113.0/24            # amplía el alcance para esta ejecución
uv run dui-ia --resume                          # continúa la última sesión
uv run dui-ia --session 47437b                  # continúa una sesión concreta (parte del ID)
uv run dui-ia --ascii                           # sin emojis (consolas antiguas, lectores de pantalla)
uv run dui-ia --no-stream                       # muestra cada respuesta completa al final
```

**En la terminal**:
- Mientras el modelo escribe, se ve una vista previa con las últimas líneas; al terminar
  aparece la respuesta completa con formato.
- Abajo hay una barra con el modelo, la sesión, los tokens, el costo y los privilegios.
- `Tab` autocompleta los comandos y muestra qué hace cada uno.
- `↑`/`↓` recorre lo que escribiste antes, incluso de otras sesiones.
- `Ctrl+C` cancela la respuesta en curso; `Ctrl+D` sale.
- En la consola clásica de Windows (conhost) se usa texto plano automáticamente. En
  Windows Terminal, PowerShell 7 o cualquier terminal de Linux se ven los emojis.

Ejemplos de preguntas:

- *¿Quién registró el dominio example.com y cuándo expira?*
- *¿Qué servidores de correo usa gmail.com?*
- *¿A quién pertenece la IP 8.8.8.8?*

| Comando | Qué hace |
|---|---|
| `/help` | Ayuda y ejemplos |
| `/tools` | Herramientas y si están disponibles en este equipo |
| `/scope`, `/scope add <objetivo>` | Ver o ampliar el alcance permitido (pide confirmar autorización) |
| `/model [nombre]` | Ver o cambiar el modelo en caliente |
| `/status` | Sistema, modelo, sesión y auditoría |
| `/cost` | Tokens y costo estimado |
| `/clear`, `/exit` | Limpiar pantalla, salir |

**Sesiones**: cada turno se guarda automáticamente, incluidos los resultados de las
herramientas, así que al reanudar el agente recuerda lo que encontró.

| Comando | Qué hace |
|---|---|
| `/sessions` | Lista las sesiones guardadas |
| `/resume` | Continúa la sesión más reciente |
| `/load <#\|ID>` | Carga una sesión por su número en la lista o por parte del ID |
| `/search <texto>` | Busca en todas las conversaciones (sin distinguir acentos ni mayúsculas) |
| `/history` | Muestra la conversación actual |
| `/audit` | Confirmaciones y ejecuciones registradas en esta sesión |
| `/rename <título>` | Cambia el título (por defecto, la primera pregunta) |
| `/export [json]` | Exporta la sesión a Markdown o JSON |
| `/delete <#\|ID>` | Borra una sesión (pide confirmación) |
| `/new` | Empieza una sesión nueva; la actual queda guardada |

También hay alias en español: `/ayuda`, `/herramientas`, `/alcance`, `/sesiones`,
`/continuar`, `/buscar`, `/exportar`, `/salir`, etc.

### Privilegios

Algunas herramientas (captura de tráfico, escaneo SYN) necesitan privilegios:

- **Windows**: abrir la terminal como Administrador. Para capturar tráfico, instalar
  [Npcap](https://npcap.com) (viene con el instalador de Nmap).
- **Linux**: `sudo .venv/bin/dui-ia`. No uses `sudo python`, porque usaría el Python
  del sistema sin las dependencias.

`/tools` y `--check` indican qué falta en tu equipo.

## Modelos

dui-IA usa [LiteLLM](https://docs.litellm.ai/docs/providers), así que cualquier
proveedor que LiteLLM soporte funciona. Basta con cambiar `DUI_MODEL` en `.env`:

| Proveedor | `DUI_MODEL` | Requiere |
|---|---|---|
| Google Gemini (por defecto) | `gemini/gemini-2.5-flash` | `GEMINI_API_KEY` |
| OpenAI | `openai/gpt-4o-mini` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-sonnet-5-5` | `ANTHROPIC_API_KEY` |
| Ollama (local) | `ollama_chat/llama3.1` | `DUI_API_BASE=http://localhost:11434` |
| LM Studio (local) | `lm_studio/<modelo>` | `DUI_API_BASE=http://localhost:1234/v1` |

El modelo tiene que soportar *function calling* (herramientas). Entre los locales,
funcionan bien Llama 3.1+, Qwen 2.5+ y Mistral Nemo.

## Herramientas

| Herramienta | Qué hace | Confirmación | Windows | Linux |
|---|---|---|---|---|
| `dns_lookup` | Registros DNS (A, AAAA, MX, TXT, NS, CNAME, SOA) | no | ✅ | ✅ |
| `reverse_dns` | Nombre asociado a una IP | no | ✅ | ✅ |
| `whois_lookup` | Registrador, fechas y dueño de dominios e IPs (RDAP, con WHOIS clásico de respaldo) | no | ✅ | ✅ |
| `network_interfaces` | Interfaces de red del equipo: estado, velocidad, IPv4/IPv6/MAC | no | ✅ | ✅ |
| `local_connections` | Puertos abiertos y conexiones del equipo con su programa; avisa de servicios delicados expuestos (RDP, SMB, Telnet, bases de datos) | no | ✅ | ✅ |
| `analyze_logs` | Registros de seguridad del equipo: inicios de sesión fallidos, cambios en cuentas, errores, servicios, antivirus | **sí** (privacidad) | ✅ Visor de eventos | ✅ journalctl / `/var/log` |
| `analyze_log_file` | Analiza un archivo de log concreto (errores, autenticación, señales de ataque) | **sí** (privacidad) | ✅ | ✅ |
| `generate_report` | Reporte en Markdown | no | ✅ | ✅ |

Las herramientas de logs piden confirmación porque su contenido (usuarios, IPs,
nombres de equipos) se envía al modelo de IA. En Windows, los inicios de sesión
fallidos y los cambios de cuentas están en el registro *Security*, que requiere
abrir la terminal como Administrador; errores, servicios y Defender se leen sin
privilegios. `analyze_log_file` rechaza archivos que suelen guardar secretos
(`.env`, claves SSH, `.pem`...). En macOS, `analyze_logs` es experimental.

## Dónde se guardan los datos

| Sistema | Carpeta |
|---|---|
| Windows | `%LOCALAPPDATA%\dui-IA` |
| Linux | `~/.local/share/dui-IA` |
| macOS | `~/Library/Application Support/dui-IA` |

Ahí están `dui.db` (SQLite con sesiones, mensajes y auditoría), los reportes
(`reports/`), las exportaciones (`exports/`) y el historial de entrada. Se puede
cambiar con `DUI_DATA_DIR`. La base se puede abrir con cualquier visor de SQLite
(por ejemplo, [DB Browser for SQLite](https://sqlitebrowser.org)).

## Documentación

- [docs/PLAN_V2.md](docs/PLAN_V2.md): plan y avance por fases
- [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md): cómo está construido
- [docs/DESARROLLO.md](docs/DESARROLLO.md): uv, pruebas, cómo agregar una herramienta
- [CHANGELOG.md](CHANGELOG.md): cambios

## Aviso legal

Analizar redes o equipos sin autorización puede ser ilegal. Usa dui-IA solo
sobre sistemas propios o con permiso explícito.
