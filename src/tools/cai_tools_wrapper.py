"""
Wrapper para herramientas oficiales de CAI
"""

from cai.agents.network_traffic_analyzer import network_security_analyzer_agent
from scapy.all import sniff
from cai.sdk.agents import function_tool
from ..core.permissions import PermissionChecker


@function_tool
def network_sniffer_tool(interface: str, count: int, filename: str) -> str:
    """
    Captura paquetes de red en una interfaz específica y guarda el resumen en un archivo de texto.
    
    Esta es la herramienta original de tu proyecto, adaptada al nuevo sistema.

    Args:
        interface: Interfaz de red a monitorear (ej: 'eth0', 'wlan0')
        count: Número de paquetes a capturar
        filename: Archivo donde guardar el resumen de la captura
        
    Returns:
        Mensaje de éxito o error
    """
    # Verificar permisos primero
    can_capture, message = PermissionChecker.can_capture_packets()
    if not can_capture:
        advice = PermissionChecker.get_permission_advice("network_sniffer")
        return f"{message}\n\n{advice}"
    
    try:
        print(f"[*] Iniciando captura en {interface} para {count} paquetes...")

        # Ejecutar captura con Scapy
        packets = sniff(iface=interface, count=count)

        # Procesar paquetes a formato de texto
        output_data = []
        for pkt in packets:
            output_data.append(pkt.summary())

        full_content = "\n".join(output_data)

        # Guardar en archivo
        with open(filename, "w") as f:
            f.write(f"Captura de Red - Interfaz: {interface}\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total de paquetes: {count}\n")
            f.write("=" * 50 + "\n\n")
            f.write(full_content)

        return f"✅ Captura exitosa: {count} paquetes guardados en '{filename}'"

    except PermissionError:
        advice = PermissionChecker.get_permission_advice("network_sniffer")
        return f"❌ Error de permisos al capturar paquetes\n\n{advice}"
    except Exception as e:
        return f"❌ Error durante la captura: {str(e)}"


# Exportar herramientas disponibles
__all__ = ['network_sniffer_tool']
