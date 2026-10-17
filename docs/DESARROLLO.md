# Guía de desarrollo

Todo se hace con **uv**: no hace falta activar el entorno virtual ni usar `pip`.

## Comandos

```bash
uv sync                          # instala exactamente lo del uv.lock (+ herramientas de dev)
uv run dui-ia                    # ejecuta la aplicación
uv run dui-ia --check            # diagnóstico
uv run pytest                    # pruebas
uv run pytest tests/test_scope.py -k domains   # una prueba concreta
uv run ruff check src tests      # lint
uv run ruff format src tests     # formato
```

Antes de subir cambios: `uv run ruff format src tests && uv run ruff check src tests && uv run pytest`.
El CI ejecuta lo mismo en Windows, Linux y macOS.

## Dependencias

```bash
uv add <paquete>                 # dependencia de la aplicación
uv add --dev <paquete>           # dependencia solo para desarrollo
uv lock --upgrade-package litellm   # actualizar un paquete concreto
```

`pyproject.toml` define `exclude-newer`: uv no instala versiones publicadas después
de esa fecha. Así nos protegemos de paquetes comprometidos recién publicados (como
pasó con LiteLLM 1.82.7/1.82.8). Para actualizar dependencias:

1. Mueve `exclude-newer` a una fecha de al menos dos semanas atrás.
2. Ejecuta `uv lock --upgrade` y revisa el diff de `uv.lock`.
3. Corre las pruebas en Windows y Linux (el CI lo hace).

Sube siempre `uv.lock` al repositorio.

## Estructura

```
src/dui/
  __main__.py      punto de entrada (comando dui-ia)
  config.py        Settings desde .env / variables DUI_*
  compat.py        diferencias entre sistemas operativos
  errors.py        excepciones comunes
  agent/           núcleo: tools.py, runner.py, llm.py, agent.py, prompts.py
  security/        scope.py (alcance), audit.py (auditoría)
  tools/           herramientas de ciberseguridad
  ui/              terminal
tests/             pytest (helpers.py tiene el FakeLLM)
legacy/            código v1, solo como referencia (se eliminará)
```

## Cómo agregar una herramienta

1. Crea la función en `src/dui/tools/<categoría>.py`:

```python
from ..agent.tools import Availability, ToolContext, ToolError, tool
from ..compat import find_binary


def _check() -> Availability:
    return Availability.yes() if find_binary("nmap") else Availability.no("Instala Nmap: https://nmap.org")


def _in_scope(arguments: dict, ctx: ToolContext) -> None:
    ctx.scope.ensure_allowed(arguments["target"])


@tool(sensitive=True, category="network", check=_check, validator=_in_scope,
      risks=("Puede activar alertas de seguridad en la red",))
def mi_herramienta(target: str, rapido: bool = True, ctx: ToolContext | None = None) -> str:
    """Una línea que el modelo leerá para decidir cuándo usarla.

    Args:
        target: Qué significa este parámetro (el modelo lo lee).
        rapido: Idem.
    """
    if algo_mal:
        raise ToolError("Mensaje claro; el modelo se lo explicará al usuario.")
    return "resultado en texto"
```

2. Agrégala a `default_tools()` en `src/dui/tools/__init__.py`.
3. Escribe pruebas en `tests/` simulando la red o `subprocess` con `monkeypatch`
   (mira `tests/test_recon.py`).
4. Documéntala en la tabla de herramientas del README.

Reglas:
- **Multiplataforma**: nada de `os.geteuid`, `which` ni rutas fijas `/var/...`; usa
  `compat`. Si llamas a un programa externo, usa `compat.find_binary` y pasa los
  argumentos como lista (nunca `shell=True`).
- **Archivos**: siempre `encoding="utf-8"`.
- Todo lo que **toque la red de otros o requiera privilegios** es `sensitive=True` y
  valida el objetivo con `ctx.scope`.
- Devuelve texto claro; los errores esperados se lanzan como `ToolError`.

## Probar con un modelo real

- **Gemini** (gratis con límites): crea una key en https://aistudio.google.com/apikey y
  ponla en `.env` como `GEMINI_API_KEY`.
- **Local con Ollama**: instala https://ollama.com, ejecuta `ollama pull llama3.1` y luego
  `uv run dui-ia --model ollama_chat/llama3.1 --api-base http://localhost:11434`.
