# Cambios

## 2.0.0.dev0 (en desarrollo, rama `v2`)

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

**Pendiente**: herramientas activas (fase 2), sesiones con SQLite (fase 3) y mejoras de
la terminal (fase 4). Ver [docs/PLAN_V2.md](docs/PLAN_V2.md).
