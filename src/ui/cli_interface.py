"""
CLI Interface - Interfaz de línea de comandos amigable para el agente
"""

import os
import sys
from typing import Optional
from datetime import datetime


class CLI:
    """
    Interfaz de línea de comandos con mejoras visuales y UX optimizada.
    """
    
    # Códigos de color ANSI
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'gray': '\033[90m',
    }
    
    @staticmethod
    def clear_screen():
        """Limpia la pantalla de la terminal"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    @staticmethod
    def color_text(text: str, color: str, bold: bool = False) -> str:
        """
        Colorea un texto para la terminal.
        
        Args:
            text: Texto a colorear
            color: Color a aplicar
            bold: Si el texto debe ser negrita
            
        Returns:
            Texto con códigos de color ANSI
        """
        prefix = CLI.COLORS.get('bold', '') if bold else ''
        color_code = CLI.COLORS.get(color, '')
        reset = CLI.COLORS.get('reset', '')
        
        return f"{prefix}{color_code}{text}{reset}"
    
    @staticmethod
    def print_banner():
        """Imprime el banner de bienvenida del sistema"""
        CLI.clear_screen()
        
        banner = r"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║       ███████╗██╗         ██████╗ ██╗   ██╗██╗      ██╗ █████╗           ║
║       ██╔════╝██║         ██╔══██╗██║   ██║██║      ██║██╔══██╗          ║
║       █████╗  ██║         ██║  ██║██║   ██║██║█████╗██║███████║          ║
║       ██╔══╝  ██║         ██║  ██║██║   ██║██║╚════╝██║██╔══██║          ║
║       ███████╗███████╗    ██████╔╝╚██████╔╝██║      ██║██║  ██║          ║
║       ╚══════╝╚══════╝    ╚═════╝  ╚═════╝ ╚═╝      ╚═╝╚═╝  ╚═╝          ║
║                                                                          ║
║              🛡️  AGENTE INTELIGENTE DE CIBERSEGURIDAD  🛡️                  ║
║                                                                          ║
║                   Construido sobre CAI Framework                         ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
        """
        
        print(CLI.color_text(banner, 'cyan', bold=True))
        print(CLI.color_text("  v0.1.0 - Fase 1 MVP", 'gray'))
        print(CLI.color_text(f"  Sesión iniciada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", 'gray'))
        print(CLI.color_text("  Escribe 'help' para ver comandos disponibles", 'yellow'))
        print(CLI.color_text("  Escribe 'exit' o 'quit' para salir\n", 'yellow'))
        print("=" * 78 + "\n")
    
    @staticmethod
    def print_section_header(title: str, icon: str = "📋"):
        """Imprime un encabezado de sección"""
        print("\n" + "=" * 78)
        print(CLI.color_text(f"{icon}  {title}", 'cyan', bold=True))
        print("=" * 78 + "\n")
    
    @staticmethod
    def print_success(message: str):
        """Imprime un mensaje de éxito"""
        print(CLI.color_text(f"✅ {message}", 'green'))
    
    @staticmethod
    def print_error(message: str):
        """Imprime un mensaje de error"""
        print(CLI.color_text(f"❌ {message}", 'red'))
    
    @staticmethod
    def print_warning(message: str):
        """Imprime una advertencia"""
        print(CLI.color_text(f"⚠️  {message}", 'yellow'))
    
    @staticmethod
    def print_info(message: str):
        """Imprime información"""
        print(CLI.color_text(f"ℹ️  {message}", 'blue'))
    
    @staticmethod
    def print_step(step_number: int, total_steps: int, description: str):
        """Imprime un paso de un proceso"""
        progress = f"[{step_number}/{total_steps}]"
        print(CLI.color_text(f"{progress} ", 'magenta', bold=True) + description)
    
    @staticmethod
    def prompt_input(prompt_text: str, default: Optional[str] = None) -> str:
        """
        Solicita entrada del usuario con un prompt personalizado.
        
        Args:
            prompt_text: Texto del prompt
            default: Valor por defecto (opcional)
            
        Returns:
            Input del usuario
        """
        if default:
            prompt = CLI.color_text(f"🤖 {prompt_text}", 'cyan') + f" [{default}]: "
        else:
            prompt = CLI.color_text(f"🤖 {prompt_text}", 'cyan') + ": "
        
        user_input = input(prompt).strip()
        
        if not user_input and default:
            return default
        
        return user_input
    
    @staticmethod
    def prompt_yes_no(question: str, default: bool = False) -> bool:
        """
        Solicita confirmación sí/no del usuario.
        
        Args:
            question: Pregunta a hacer
            default: Valor por defecto
            
        Returns:
            True si el usuario confirma, False en caso contrario
        """
        default_str = "S/n" if default else "s/N"
        prompt = CLI.color_text(f"❓ {question}", 'yellow') + f" [{default_str}]: "
        
        response = input(prompt).strip().lower()
        
        if not response:
            return default
        
        return response in ['s', 'si', 'yes', 'y', 'sí']
    
    @staticmethod
    def print_loading(message: str = "Procesando"):
        """Imprime un mensaje de carga"""
        print(CLI.color_text(f"⏳ {message}...", 'blue'), end='', flush=True)
    
    @staticmethod
    def clear_loading():
        """Limpia la línea de carga"""
        print('\r' + ' ' * 80 + '\r', end='', flush=True)
    
    @staticmethod
    def print_table(headers: list, rows: list):
        """
        Imprime una tabla formateada.
        
        Args:
            headers: Lista de encabezados
            rows: Lista de listas con los datos
        """
        if not rows:
            print(CLI.color_text("  (Sin datos)", 'gray'))
            return
        
        # Calcular anchos de columna
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Imprimir encabezados
        header_str = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
        print(CLI.color_text(header_str, 'cyan', bold=True))
        print("-" * len(header_str))
        
        # Imprimir filas
        for row in rows:
            row_str = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
            print(row_str)
    
    @staticmethod
    def wait_for_key(message: str = "Presiona Enter para continuar"):
        """Espera a que el usuario presione una tecla"""
        input(CLI.color_text(f"\n{message}...", 'gray'))
    
    @staticmethod
    def print_box(content: str, title: Optional[str] = None, color: str = 'white'):
        """
        Imprime contenido dentro de una caja.
        
        Args:
            content: Contenido a mostrar
            title: Título opcional de la caja
            color: Color del borde
        """
        lines = content.split('\n')
        max_width = max(len(line) for line in lines) if lines else 0
        
        # Límite de ancho
        box_width = min(max_width + 4, 76)
        
        # Imprimir borde superior
        if title:
            title_str = f"═══ {title} "
            border_top = "╔" + title_str + "═" * (box_width - len(title_str) - 1) + "╗"
        else:
            border_top = "╔" + "═" * (box_width - 2) + "╗"
        
        print(CLI.color_text(border_top, color))
        
        # Imprimir contenido
        for line in lines:
            # Truncar si es muy largo
            if len(line) > box_width - 4:
                line = line[:box_width - 7] + "..."
            
            padded_line = "║ " + line.ljust(box_width - 4) + " ║"
            print(CLI.color_text(padded_line, color))
        
        # Imprimir borde inferior
        border_bottom = "╚" + "═" * (box_width - 2) + "╝"
        print(CLI.color_text(border_bottom, color))
