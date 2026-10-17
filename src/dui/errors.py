"""Excepciones compartidas por todo el paquete."""


class DuiError(Exception):
    """Error base de dui-IA."""


class ToolError(DuiError):
    """Error esperado de una herramienta. Su mensaje se le devuelve al modelo para que lo explique."""


class LLMError(DuiError):
    """No se pudo obtener respuesta del modelo de lenguaje."""
