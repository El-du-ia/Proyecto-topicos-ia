"""
Herramienta de escaneo Nmap
"""

from cai.sdk.agents import function_tool
import subprocess
import re
from ..core.permissions import PermissionChecker


@function_tool
def nmap_scan_tool(target: str, scan_type: str = "basic", output_file: str = None) -> str:
    """
    Realiza un escaneo de red usando Nmap para descubrir hosts y servicios.
    
    Esta herramienta es SENSIBLE y requiere confirmación del usuario antes de ejecutarse.

    Args:
        target: IP, rango de IPs o dominio a escanear (ej: '192.168.1.1' o '192.168.1.0/24')
        scan_type: Tipo de escaneo:
                   - 'basic': Escaneo básico de puertos comunes
                   - 'full': Escaneo completo de todos los puertos
                   - 'stealth': Escaneo sigiloso (SYN scan)
                   - 'service': Detección de versiones de servicios
        output_file: Archivo donde guardar los resultados (opcional)
        
    Returns:
        Resultados del escaneo o mensaje de error
    """
    try:
        # Verificar que nmap está instalado
        try:
            subprocess.run(['which', 'nmap'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            return "❌ Error: Nmap no está instalado. Instálalo con: sudo apt install nmap"
        
        # Construir comando según tipo de escaneo
        scan_commands = {
            "basic": ["nmap", target],
            "full": ["nmap", "-p-", target],
            "stealth": ["nmap", "-sS", target],
            "service": ["nmap", "-sV", target]
        }
        
        if scan_type not in scan_commands:
            return f"❌ Tipo de escaneo inválido: {scan_type}. Usa: basic, full, stealth, service"
        
        # Verificar permisos para escaneos que requieren root
        if scan_type == "stealth" and not PermissionChecker.is_root():
            advice = PermissionChecker.get_permission_advice("nmap_stealth")
            return f"⚠️  El escaneo 'stealth' requiere privilegios root\n\n{advice}"
        
        command = scan_commands[scan_type]
        
        print(f"[*] Ejecutando: {' '.join(command)}")
        print(f"[*] Esto puede tomar varios minutos dependiendo del objetivo...")
        
        # Ejecutar nmap
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # Timeout de 5 minutos
        )
        
        if result.returncode != 0:
            return f"❌ Error ejecutando nmap: {result.stderr}"
        
        output = result.stdout
        
        # Guardar en archivo si se especificó
        if output_file:
            with open(output_file, 'w') as f:
                f.write(f"Escaneo Nmap - Tipo: {scan_type}\n")
                f.write(f"Objetivo: {target}\n")
                f.write("=" * 70 + "\n\n")
                f.write(output)
            
            output += f"\n\n📄 Resultados guardados en: {output_file}"
        
        # Parsear información clave
        open_ports = re.findall(r'(\d+)/tcp\s+open\s+(\w+)', output)
        
        if open_ports:
            summary = f"\n\n🎯 RESUMEN: Se encontraron {len(open_ports)} puertos abiertos en {target}"
        else:
            summary = f"\n\n🎯 RESUMEN: No se encontraron puertos abiertos en {target}"
        
        return output + summary
    
    except subprocess.TimeoutExpired:
        return "❌ Error: El escaneo excedió el tiempo límite (5 minutos)"
    except PermissionError:
        return "❌ Error: Algunos tipos de escaneo requieren privilegios root/sudo"
    except Exception as e:
        return f"❌ Error durante el escaneo: {str(e)}"


@function_tool
def nmap_ping_sweep(network: str) -> str:
    """
    Realiza un barrido rápido para descubrir hosts activos en una red.
    
    Más rápido que un escaneo completo, útil para reconocimiento inicial.

    Args:
        network: Red a escanear en notación CIDR (ej: '192.168.1.0/24')
        
    Returns:
        Lista de hosts activos encontrados
    """
    try:
        print(f"[*] Buscando hosts activos en {network}...")
        
        result = subprocess.run(
            ["nmap", "-sn", network],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return f"❌ Error: {result.stderr}"
        
        # Extraer IPs de hosts activos
        active_hosts = re.findall(r'Nmap scan report for .*?\(?([\d.]+)\)?', result.stdout)
        
        if active_hosts:
            output = f"✅ Se encontraron {len(active_hosts)} hosts activos:\n\n"
            for ip in active_hosts:
                output += f"  • {ip}\n"
            return output
        else:
            return "ℹ️  No se encontraron hosts activos en la red especificada"
    
    except subprocess.TimeoutExpired:
        return "❌ Error: El barrido excedió el tiempo límite"
    except Exception as e:
        return f"❌ Error: {str(e)}"


# Exportar herramientas
__all__ = ['nmap_scan_tool', 'nmap_ping_sweep']
