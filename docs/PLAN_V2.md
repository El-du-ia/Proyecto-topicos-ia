# Plan dui-IA v2

## Objetivos

1. **Multiplataforma**: Windows y Linux como prioridad. macOS después, pero sin
   decisiones que lo impidan (CI ya lo prueba sin bloquear).
2. **Sin CAI**: CAI está desactualizado. Se conserva su arquitectura
   (Agente → Runner → Herramientas) con un núcleo propio.
3. **Cualquier LLM**, en la nube o local, mediante LiteLLM. Para pruebas, Gemini.
4. **Herramientas que funcionen en todos los sistemas**: implementadas en Python
   cuando se puede; si dependen de algo externo (nmap, Npcap), se detecta y hay
   alternativa.
5. **Terminal mejorada**.
6. **uv en todo** (instalación, ejecución, pruebas, CI).
7. **Documentar y probar en cada fase**.
8. **Mantener la filosofía de v1**: confirmación, explicaciones simples, registro,
   y ahora además el **alcance permitido**.

## Fases

### ✅ Fase 0 · Base del proyecto
- [x] Rama `v2`; código v1 movido a `legacy/` y docs v1 a `docs/legacy/`
- [x] `pyproject.toml` + `uv.lock` (Python 3.11–3.13; `.python-version` = 3.12)
- [x] Defensa de cadena de suministro: `exclude-newer` en uv y LiteLLM fijado a 1.103.x
      (las versiones 1.82.7/1.82.8 de LiteLLM fueron comprometidas en 2026)
- [x] `ruff` (lint + formato) y `pytest`
- [x] CI en GitHub Actions: Windows y Linux (obligatorios) + macOS (informativo)

### ✅ Fase 1 · Núcleo propio
- [x] `@tool`: esquema JSON generado desde type hints + docstring
- [x] `Runner`: ciclo modelo ↔ herramientas con límite de pasos
- [x] Confirmación de herramientas sensibles **impuesta por el Runner**
      (si nadie puede confirmar, se rechaza)
- [x] Validación de argumentos y del alcance **antes** de pedir confirmación
- [x] Alcance permitido (`Scope`): redes privadas por defecto, `DUI_SCOPE` y `/scope add`
- [x] Auditoría JSONL de confirmaciones y ejecuciones
- [x] Cliente LiteLLM (cualquier proveedor o modelo local) con errores amigables
- [x] Costo y tokens por sesión
- [x] Terminal base (rich + prompt_toolkit) y `dui-ia --check`
- [x] Herramientas pasivas migradas y mejoradas: DNS (más tipos de registro), DNS inverso
      (IPv6), WHOIS por RDAP con respaldo por el puerto 43 (sin binario `whois`)
- [x] Reportes en Markdown
- [x] Reintentos con espera creciente ante errores pasajeros del proveedor (503, límites)
- [x] Probado con Gemini real en Windows

### ⏳ Fase 2 · Plataforma y herramientas activas
- [ ] `network_interfaces`: interfaces de red (psutil + scapy)
- [ ] `local_connections`: puertos abiertos y conexiones del propio equipo (psutil)
- [ ] `port_scan`: nmap si está instalado (salida XML); si no, escáner TCP propio
      (asyncio, sin privilegios)
- [ ] `host_discovery`: ARP (scapy, con privilegios) → ping → sondeo TCP
- [ ] `packet_capture`: scapy (Npcap en Windows, root o capabilities en Linux)
- [ ] `analyze_logs`: Linux (journalctl, /var/log) y Windows (Visor de eventos,
      p. ej. 4625 = inicio de sesión fallido), con el mismo formato de salida
- [ ] Restricción de rutas de escritura y lectura

### ✅ Fase 3 · Sesiones persistentes
- [x] SQLite (`<datos>/dui.db`): `sessions`, `messages` (mensaje completo, incluidas las
      llamadas a herramientas y sus resultados) y `audit`; borrado en cascada
- [x] Auditoría en la misma base (se eliminó el JSONL: una sola fuente de verdad)
- [x] Autoguardado atómico por turno; título automático tomado de la primera pregunta
- [x] `/sessions`, `/resume`, `/load` (por número o parte del ID), `/rename`, `/delete`
      (con confirmación), `/export` (Markdown/JSON), `/history`, `/audit`
- [x] `dui-ia --resume` y `--session <ID>`; el banner ofrece retomar la última sesión
- [x] `/search` de texto completo con FTS5 (sin distinguir acentos ni mayúsculas), con
      respaldo en LIKE si SQLite no trae FTS5
- [x] Recorte del contexto en sesiones largas (`DUI_MAX_HISTORY`) sin separar una llamada
      a herramienta de su resultado
- [ ] Resumen automático de lo recortado (por ahora solo se recorta)

### ✅ Fase 4 · Terminal
- [x] Respuestas en streaming (también cuando el modelo usa herramientas); sin reintentos
      después de haber mostrado texto, para no duplicar la respuesta
- [x] Barra de estado: modelo, sesión, tokens, costo y privilegios
- [x] Modo sin emojis (`--ascii`, `DUI_ASCII`), automático en la consola clásica de Windows;
      el modelo también deja de usar emojis (niveles de riesgo `[ALTO]`, `[BAJO]`...)
- [x] Autocompletado de comandos con su descripción, alias incluidos
- [x] Ayuda agrupada (General / Sesiones) con atajos de teclado
- [x] Terminal dividida en módulos: `terminal.py`, `hooks.py`, `commands.py`, `symbols.py`
- [ ] Mejoras de usabilidad a partir de pruebas con usuarios reales

### ⏳ Fase 5 · Cierre
- [ ] Reportes en HTML
- [ ] Scripts `install.ps1` e `install.sh`
- [ ] Prueba manual en macOS
- [ ] Ejecutable opcional (PyInstaller)
- [ ] Eliminar `legacy/`

## Riesgos

- **macOS**: sin equipo propio, solo CI. La captura de tráfico no se puede probar en CI.
- **Modelos locales pequeños**: algunos no soportan *function calling*. Se documentan
  los que sí funcionan.
- **Herramientas que requieren privilegios**: no se pueden probar por completo en CI.
  Se prueban con `subprocess` simulado y de forma manual.
