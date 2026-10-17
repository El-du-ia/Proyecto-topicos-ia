"""
Herramienta de análisis de logs del sistema
"""

from cai.sdk.agents import function_tool
import re
from datetime import datetime
from typing import List, Dict, Any
import os
from ..core.permissions import PermissionChecker


@function_tool
def analyze_log_tool(log_file_path: str, patterns: str = "errors", max_lines: int = 1000) -> str:
    """
    Analiza archivos de log del sistema en busca de eventos importantes, errores o patrones sospechosos.
    
    Útil para detectar:
    - Intentos de acceso fallidos
    - Errores del sistema
    - Comportamiento anómalo
    - Actividad sospechosa

    Args:
        log_file_path: Ruta al archivo de log (ej: '/var/log/syslog' o '/var/log/auth.log')
        patterns: Tipo de análisis:
                  - 'errors': Busca errores y fallos
                  - 'auth': Analiza intentos de autenticación
                  - 'suspicious': Busca actividad sospechosa
                  - 'all': Análisis completo
        max_lines: Número máximo de líneas a analizar (por defecto 1000, últimas líneas)
        
    Returns:
        Resumen del análisis con hallazgos importantes
    """
    # Verificar que el archivo existe
    if not os.path.exists(log_file_path):
        return f"❌ Error: No se encontró el archivo: {log_file_path}"
    
    # Verificar permisos de lectura
    can_read, message = PermissionChecker.can_read_file(log_file_path)
    if not can_read:
        advice = PermissionChecker.get_permission_advice("analyze_log")
        return f"{message}\n\n{advice}"
    
    try:
        
        print(f"[*] Analizando log: {log_file_path}")
        print(f"[*] Patrón de búsqueda: {patterns}")
        print(f"[*] Máximo de líneas: {max_lines}")
        
        # Leer las últimas N líneas del archivo
        with open(log_file_path, 'r', errors='ignore') as f:
            lines = f.readlines()
            if len(lines) > max_lines:
                lines = lines[-max_lines:]  # Solo últimas max_lines líneas
        
        # Definir patrones de búsqueda
        pattern_config = {
            "errors": {
                "regex": [
                    r'\berror\b', r'\bfail(ed)?\b', r'\bcrash(ed)?\b',
                    r'\bexception\b', r'\bwarning\b', r'\bcritical\b'
                ],
                "name": "Errores y Fallos"
            },
            "auth": {
                "regex": [
                    r'Failed password', r'authentication failure', 
                    r'Invalid user', r'refused connect', r'Connection closed'
                ],
                "name": "Autenticación"
            },
            "suspicious": {
                "regex": [
                    r'brute.?force', r'attack', r'exploit', r'malware',
                    r'unauthorized', r'suspicious', r'intrusion'
                ],
                "name": "Actividad Sospechosa"
            }
        }
        
        # Determinar qué patrones usar
        if patterns == "all":
            search_patterns = pattern_config
        elif patterns in pattern_config:
            search_patterns = {patterns: pattern_config[patterns]}
        else:
            return f"❌ Error: Patrón inválido '{patterns}'. Usa: errors, auth, suspicious, all"
        
        # Realizar análisis
        findings: List[Dict[str, Any]] = []
        
        for category, config in search_patterns.items():
            for line_num, line in enumerate(lines, 1):
                for pattern in config["regex"]:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append({
                            "category": config["name"],
                            "line_number": len(lines) - max_lines + line_num if len(lines) > max_lines else line_num,
                            "content": line.strip(),
                            "pattern": pattern
                        })
                        break  # Solo un match por línea
        
        # Generar reporte
        if not findings:
            return f"✅ Análisis completado: No se encontraron eventos del tipo '{patterns}' en las últimas {len(lines)} líneas."
        
        output = f"📊 ANÁLISIS DE LOG: {os.path.basename(log_file_path)}\n"
        output += "=" * 70 + "\n\n"
        output += f"📁 Archivo: {log_file_path}\n"
        output += f"📏 Líneas analizadas: {len(lines)}\n"
        output += f"🔍 Hallazgos: {len(findings)}\n\n"
        
        # Agrupar por categoría
        by_category: Dict[str, List[Dict]] = {}
        for finding in findings:
            cat = finding["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(finding)
        
        # Mostrar resumen por categoría
        output += "📋 RESUMEN POR CATEGORÍA:\n"
        output += "-" * 70 + "\n"
        for category, items in by_category.items():
            output += f"\n🔹 {category}: {len(items)} eventos\n"
            
            # Mostrar primeros 5 ejemplos
            for item in items[:5]:
                output += f"   Línea {item['line_number']}: {item['content'][:80]}...\n"
            
            if len(items) > 5:
                output += f"   ... y {len(items) - 5} eventos más\n"
        
        output += "\n" + "=" * 70 + "\n"
        
        # Agregar recomendaciones
        output += "\n💡 RECOMENDACIONES:\n"
        
        if "Actividad Sospechosa" in by_category:
            output += "  ⚠️  Se detectó actividad sospechosa. Revisa los logs inmediatamente.\n"
        
        if "Autenticación" in by_category and len(by_category["Autenticación"]) > 10:
            output += "  ⚠️  Múltiples fallos de autenticación. Posible ataque de fuerza bruta.\n"
        
        if "Errores y Fallos" in by_category and len(by_category["Errores y Fallos"]) > 50:
            output += "  ⚠️  Alto número de errores. El sistema puede estar comprometido o tener problemas.\n"
        
        output += f"  📄 Considera guardar este reporte para análisis posterior.\n"
        
        return output
    
    except PermissionError:
        advice = PermissionChecker.get_permission_advice("analyze_log")
        return f"❌ Error: Permiso denegado para leer {log_file_path}\n\n{advice}"
    except Exception as e:
        return f"❌ Error durante el análisis: {str(e)}"


@function_tool
def tail_log_tool(log_file_path: str, lines: int = 20) -> str:
    """
    Muestra las últimas N líneas de un archivo de log en tiempo real.
    
    Equivalente a 'tail -n' de Linux.

    Args:
        log_file_path: Ruta al archivo de log
        lines: Número de líneas a mostrar (por defecto 20)
        
    Returns:
        Últimas líneas del archivo
    """
    # Verificar permisos
    if not os.path.exists(log_file_path):
        return f"❌ Error: No se encontró el archivo: {log_file_path}"
    
    can_read, message = PermissionChecker.can_read_file(log_file_path)
    if not can_read:
        advice = PermissionChecker.get_permission_advice("tail_log")
        return f"{message}\n\n{advice}"
    
    try:
        
        with open(log_file_path, 'r', errors='ignore') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) >= lines else all_lines
        
        output = f"📄 Últimas {len(last_lines)} líneas de: {os.path.basename(log_file_path)}\n"
        output += "=" * 70 + "\n\n"
        output += "".join(last_lines)
        
        return output
    
    except PermissionError:
        advice = PermissionChecker.get_permission_advice("tail_log")
        return f"❌ Error: Permiso denegado\n\n{advice}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


# Exportar herramientas
__all__ = ['analyze_log_tool', 'tail_log_tool']
