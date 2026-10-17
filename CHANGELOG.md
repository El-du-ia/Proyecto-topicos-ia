# Cambios

## 2.0.0.dev0 (en desarrollo, rama `v2`)

### Pantalla de inicio

- Logo "DUI-IA" en letras grandes con degradado de color (fuente de bloques; en `--ascii`,
  fuente ASCII). En terminales angostas se muestra solo el nombre.
- Panel "Listo para ayudarte" con modelo, sistema, privilegios, alcance, herramientas
  disponibles, sesión y tres preguntas de ejemplo para empezar.

### Herramientas del propio equipo y corrección del streaming

**Agregado**
- `network_interfaces` y `local_connections` (psutil): interfaces, puertos abiertos y
  conexiones del equipo, con aviso de servicios delicados expuestos a la red.
- `analyze_logs`: registros de seguridad en Windows (Visor de eventos) y Linux (journalctl o
  `/var/log`); macOS experimental. Pide confirmación porque el contenido se envía al modelo.
- `analyze_log_file`: análisis de un archivo de log; rechaza archivos con secretos.
- `pyte` como dependencia de desarrollo para probar lo que se ve en una terminal real.

**Corregido**
- Con respuestas más altas que la terminal, el panel de la respuesta se repetía muchas veces
  en pantalla. Ahora hay una vista previa limitada a la altura de la pantalla y la respuesta
  completa se imprime una sola vez al final.

**Pendiente**: pruebas automáticas de las cuatro herramientas nuevas.

113 pruebas.

### Fase 4: terminal

**Agregado**
- Respuestas en streaming (`DUI_STREAM`, `--no-stream`), también con llamadas a herramientas.
- Barra de estado con modelo, sesión, tokens, costo y privilegios.
- Modo sin emojis (`--ascii`, `DUI_ASCII`), automático en la consola clásica de Windows. El
  modelo recibe la instrucción de no usar emojis.
- Autocompletado de comandos con descripción; ayuda agrupada con atajos de teclado.

**Cambiado**
- La terminal se dividió en `terminal.py`, `hooks.py`, `commands.py` y `symbols.py`.
- `LLMClient.complete()` acepta `on_text` para recibir el texto en streaming.

112 pruebas.

### Fase 3: sesiones persistentes

**Agregado**
- Sesiones en SQLite (`<datos>/dui.db`) con autoguardado atómico por turno. Se guarda
  la conversación completa, incluidos los resultados de herramientas.
- Comandos `/sessions`, `/resume`, `/load`, `/search`, `/history`, `/audit`, `/rename`,
  `/export` (Markdown/JSON) y `/delete`, con alias en español.
- `dui-ia --resume` y `dui-ia --session <ID>`; el banner ofrece retomar la última sesión.
- Búsqueda de texto completo (FTS5) sin distinguir acentos ni mayúsculas.
- Recorte de contexto en sesiones largas (`DUI_MAX_HISTORY`).
- Reintentos automáticos ante errores pasajeros del proveedor (p. ej. 503 de Gemini) y
  mensajes de error legibles cuando el proveedor responde en JSON.

**Cambiado**
- La auditoría pasa de archivos JSONL a la tabla `audit` de la misma base.
- Las pruebas ya no leen el `.env` del desarrollador.

**Corregido**
- En Windows, la entrada redirigida (stdin) se leía como cp1252 y rompía los acentos.

97 pruebas.

### Fases 0 y 1: base del proyecto y núcleo propio

**Agregado**
- Proyecto gestionado con uv (`pyproject.toml`, `uv.lock`, comando `dui-ia`).
- Núcleo propio inspirado en CAI: `@tool`, `Agent`, `Runner`, `LLMClient`.
- Soporte para cualquier modelo vía LiteLLM, incluidos los locales (Ollama, LM Studio).
- Confirmación de herramientas sensibles impuesta por el Runner.
- Alcance permitido (`DUI_SCOPE`, `--scope`, `/scope add`): por defecto, solo redes privadas.
- Auditoría JSONL de confirmaciones, ejecuciones y bloqueos.
- Terminal nueva con rich + prompt_toolkit: paneles, confirmación, historial y autocompletado.
- `dui-ia --check`: diagnóstico del sistema, del modelo y de las herramientas.
- Herramientas: `dns_lookup` (A/AAAA/MX/TXT/NS/CNAME/SOA), `reverse_dns` (con IPv6),
  `whois_lookup` (RDAP + WHOIS por el puerto 43, sin binarios externos) y
  `generate_report` (Markdown).
- CI en Windows, Linux y macOS. 69 pruebas.

**Cambiado**
- Los datos se guardan en la carpeta de datos del sistema (`%LOCALAPPDATA%\dui-IA`,
  `~/.local/share/dui-IA`) y no en la carpeta del proyecto.
- Configuración con variables `DUI_*`. `CAI_MODEL` sigue funcionando.

**Corregido (respecto a v1)**
- La confirmación existía solo en el prompt: `execute_with_confirmation` nunca se llamaba.
- La auditoría siempre quedaba vacía.
- El marcador de reporte de nmap no coincidía con el que esperaba el prompt.
- Fallos en Windows: `os.geteuid`, `which`, `USER` y archivos sin UTF-8.

Ver el avance en [docs/PLAN_V2.md](docs/PLAN_V2.md).
