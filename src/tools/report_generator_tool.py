# src/tools/report_generator_tool.py (MODIFICADO)

import os
from datetime import datetime
from cai.sdk.agents import function_tool

try:
    from src.ui.cli_interface import CLI 
except ImportError:
    class CLI:
        @staticmethod
        def print_success(msg): print(f"✅ {msg}")
        @staticmethod
        def print_error(msg): print(f"❌ {msg}")


REPORTS_DIR = "logs/reports" # Usamos una subcarpeta dentro de logs/

@function_tool
def generate_report_tool(report_content_raw: str, analysis_summary: str, source_tool: str = "security_analysis") -> str:
    """
    Genera un archivo de reporte TXT, incluyendo el análisis de la IA 
    (que ya contiene la estructura profesional) y el resultado crudo.
    
    Args:
        report_content_raw: El texto completo y crudo del resultado de la herramienta.
        analysis_summary: El REPORTE COMPLETO y estructurado generado por la IA (basado en el prompt).
        source_tool: Nombre de la herramienta que generó el reporte (ej: 'nmap_scan').
        
    Returns:
        Un mensaje de confirmación con la ruta completa del archivo generado.
    """
    try:
        # Limpieza básica del nombre para el archivo
        safe_source_tool = source_tool.replace(" ", "_").lower()
        
        if not os.path.exists(REPORTS_DIR):
            os.makedirs(REPORTS_DIR)

        # Generar nombre de archivo único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{safe_source_tool}_{timestamp}.txt"
        file_path = os.path.join(REPORTS_DIR, file_name)

        # Usar un borde simple para simular el formato profesional en TXT
        REPORT_BORDER = "──────────────────────────────────────────────────────────────────────────────────────────────────────────────────\n"
        
        # Escribir el contenido estructurado
        with open(file_path, 'w', encoding='utf-8') as f:
            
            # -------------------------------------------------------------
            # SECCIÓN 1: REPORTE ESTRUCTURADO Y PROFESIONAL (Generado por la IA)
            # -------------------------------------------------------------
            f.write(REPORT_BORDER)
            f.write(f"| REPORTE DE ANÁLISIS DE SEGURIDAD (Generado por {source_tool}) |\n")
            f.write(f"| Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |\n")
            f.write(REPORT_BORDER)
            f.write("\n")
            
            # Aquí se inserta el reporte completo y formateado que la IA generó 
            # siguiendo el PROMPT de la estructura (Resumen, Alcance, Detalles, etc.)
            f.write(analysis_summary.strip())
            
            f.write("\n\n" + REPORT_BORDER)
            f.write("| FIN DEL ANÁLISIS ESTRUCTURADO |")
            f.write("\n" + REPORT_BORDER)
            
            # -------------------------------------------------------------
            # SECCIÓN 2: DATOS TÉCNICOS CRUDOS (Para auditoría y referencia)
            # -------------------------------------------------------------
            f.write("\n\n")
            f.write("## 7. DATOS TÉCNICOS CRUDOS (Para Auditoría)\n")
            f.write("=" * 40 + "\n")
            f.write(report_content_raw.strip())
            
            f.write("\n\n" + REPORT_BORDER)
            f.write("| FIN DEL REPORTE COMPLETO |")
            f.write("\n" + REPORT_BORDER)

        CLI.print_success(f"Reporte generado exitosamente en: {file_path}")
        return f"Reporte generado exitosamente en el archivo: {file_path}"
    
    except Exception as e:
        error_msg = f"Error al generar el reporte: {e}"
        CLI.print_error(error_msg)
        return error_msg
# Exportar herramientas
__all__ = ['generate_report_tool']