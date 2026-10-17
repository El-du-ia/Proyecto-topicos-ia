"""
Herramientas del agente.

Una herramienta es una función normal de Python decorada con @tool. El esquema
JSON que recibe el modelo se genera a partir de los type hints y del docstring
(estilo Google, sección "Args:"), así que documentar la función ES definir la
herramienta:

    @tool(sensitive=True, category="network", risks=("Puede activar alertas del IDS",))
    def port_scan(target: str, ports: str = "top100", ctx: ToolContext | None = None) -> str:
        '''Escanea puertos TCP de un host.

        Args:
            target: IP o dominio a escanear.
            ports: 'top100', 'top1000' o una lista como '22,80,443'.
        '''

El parámetro `ctx` (si existe) no se expone al modelo: el Runner lo inyecta con
la configuración, el alcance permitido y la información del sistema.
"""

from __future__ import annotations

import inspect
import re
import types
import typing
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Union, get_args, get_origin

from ..errors import ToolError

if TYPE_CHECKING:
    from ..compat import SystemInfo
    from ..config import Settings
    from ..security.scope import Scope

__all__ = ["Availability", "Tool", "ToolContext", "ToolError", "ToolRegistry", "tool"]


@dataclass(frozen=True)
class Availability:
    """Si una herramienta puede usarse en este equipo y, si no, por qué."""

    ok: bool
    detail: str = ""

    @classmethod
    def yes(cls, detail: str = "") -> Availability:
        return cls(True, detail)

    @classmethod
    def no(cls, detail: str) -> Availability:
        return cls(False, detail)


@dataclass
class ToolContext:
    settings: Settings
    scope: Scope
    system: SystemInfo


Validator = Callable[[dict[str, Any], ToolContext], None]

_JSON_TYPES: dict[Any, str] = {str: "string", int: "integer", float: "number", bool: "boolean"}
_SECTION_RE = re.compile(r"^\s*(Args|Arguments|Returns?|Raises|Yields|Examples?|Notes?):\s*$")
_ARG_RE = re.compile(r"^\s+(\w+)\s*(?:\([^)]*\))?:\s*(.*)$")


def _json_schema(annotation: Any) -> dict[str, Any]:
    if annotation in _JSON_TYPES:
        return {"type": _JSON_TYPES[annotation]}
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Literal:
        return {"type": _JSON_TYPES[type(args[0])], "enum": list(args)}
    if origin in (Union, types.UnionType):
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _json_schema(non_none[0])
    if annotation in (list, tuple, set) or origin in (list, tuple, set):
        schema: dict[str, Any] = {"type": "array"}
        if args:
            schema["items"] = _json_schema(args[0])
        return schema
    if annotation is dict or origin is dict:
        return {"type": "object"}
    raise TypeError(f"Tipo de parámetro no soportado en una herramienta: {annotation!r}")


def _parse_docstring(doc: str | None) -> tuple[str, dict[str, str]]:
    """Separa la descripción general y la descripción de cada argumento."""
    lines = inspect.cleandoc(doc or "").splitlines()
    description: list[str] = []
    params: dict[str, str] = {}
    section: str | None = None
    current: str | None = None
    for line in lines:
        header = _SECTION_RE.match(line)
        if header:
            section = header.group(1).lower()
            current = None
            continue
        if section is None:
            description.append(line)
        elif section in ("args", "arguments"):
            match = _ARG_RE.match(line)
            if match:
                current = match.group(1)
                params[current] = match.group(2).strip()
            elif current and line.strip():
                params[current] = f"{params[current]} {line.strip()}".strip()
    return "\n".join(description).strip(), params


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    func: Callable[..., Any]
    sensitive: bool = False
    category: str = "general"
    risks: tuple[str, ...] = ()
    check: Callable[[], Availability] | None = None
    validator: Validator | None = None
    wants_context: bool = False
    _param_names: frozenset[str] = field(default=frozenset(), repr=False)

    @classmethod
    def from_function(
        cls,
        func: Callable[..., Any],
        *,
        name: str | None = None,
        sensitive: bool = False,
        category: str = "general",
        risks: Iterable[str] = (),
        check: Callable[[], Availability] | None = None,
        validator: Validator | None = None,
    ) -> Tool:
        description, arg_docs = _parse_docstring(func.__doc__)
        hints = typing.get_type_hints(func)
        properties: dict[str, Any] = {}
        required: list[str] = []
        wants_context = False
        for param in inspect.signature(func).parameters.values():
            if param.name == "ctx":
                wants_context = True
                continue
            if param.name not in hints:
                raise TypeError(f"{func.__name__}: el parámetro '{param.name}' necesita type hint")
            schema = _json_schema(hints[param.name])
            if param.name in arg_docs:
                schema["description"] = arg_docs[param.name]
            if param.default is inspect.Parameter.empty:
                required.append(param.name)
            elif param.default is not None:
                schema["default"] = param.default
            properties[param.name] = schema
        if not description:
            raise TypeError(f"{func.__name__}: la herramienta necesita un docstring con descripción")
        parameters = {"type": "object", "properties": properties, "required": required}
        return cls(
            name=name or func.__name__,
            description=description,
            parameters=parameters,
            func=func,
            sensitive=sensitive,
            category=category,
            risks=tuple(risks),
            check=check,
            validator=validator,
            wants_context=wants_context,
            _param_names=frozenset(properties),
        )

    def availability(self) -> Availability:
        if self.check is None:
            return Availability.yes()
        try:
            return self.check()
        except Exception as exc:  # una verificación rota no debe tumbar la aplicación
            return Availability.no(f"No se pudo verificar la disponibilidad: {exc}")

    def to_openai(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def validate(self, arguments: dict[str, Any], ctx: ToolContext | None) -> None:
        """Valida argumentos ANTES de pedir confirmación. Lanza ToolError si algo no cuadra."""
        unknown = set(arguments) - self._param_names
        if unknown:
            raise ToolError(f"Argumentos desconocidos para {self.name}: {', '.join(sorted(unknown))}")
        missing = [p for p in self.parameters["required"] if p not in arguments]
        if missing:
            raise ToolError(f"Faltan argumentos obligatorios para {self.name}: {', '.join(missing)}")
        if self.validator is not None and ctx is not None:
            self.validator(arguments, ctx)

    def invoke(self, arguments: dict[str, Any], ctx: ToolContext | None = None) -> str:
        self.validate(arguments, ctx)
        kwargs = dict(arguments)
        if self.wants_context:
            kwargs["ctx"] = ctx
        result = self.func(**kwargs)
        return result if isinstance(result, str) else str(result)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Permite seguir usando la función directamente (por ejemplo en pruebas)."""
        return self.func(*args, **kwargs)


def tool(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    sensitive: bool = False,
    category: str = "general",
    risks: Iterable[str] = (),
    check: Callable[[], Availability] | None = None,
    validator: Validator | None = None,
) -> Any:
    """Convierte una función en una Tool. Se usa como @tool o @tool(sensitive=True, ...)."""

    def wrap(f: Callable[..., Any]) -> Tool:
        return Tool.from_function(
            f,
            name=name,
            sensitive=sensitive,
            category=category,
            risks=risks,
            check=check,
            validator=validator,
        )

    return wrap(func) if func is not None else wrap


class ToolRegistry:
    def __init__(self, tools: Iterable[Tool] = ()) -> None:
        self._tools: dict[str, Tool] = {}
        for t in tools:
            self.register(t)

    def register(self, t: Tool) -> None:
        if t.name in self._tools:
            raise ValueError(f"Ya existe una herramienta llamada '{t.name}'")
        self._tools[t.name] = t

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas(self) -> list[dict[str, Any]]:
        return [t.to_openai() for t in self._tools.values()]

    def __iter__(self) -> Iterator[Tool]:
        return iter(self._tools.values())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools
