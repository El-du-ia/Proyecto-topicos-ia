"""
Herramienta de consulta WHOIS
"""

from cai.sdk.agents import function_tool
import subprocess
import socket


@function_tool
def whois_lookup_tool(domain: str, save_to_file: str = None) -> str:
    """
    Consulta información WHOIS de un dominio o dirección IP.
    
    WHOIS proporciona información sobre el registro de dominios, incluyendo:
    - Propietario del dominio
    - Fechas de registro y expiración
    - Servidores DNS
    - Información de contacto

    Args:
        domain: Dominio o IP a consultar (ej: 'google.com' o '8.8.8.8')
        save_to_file: Archivo donde guardar los resultados (opcional)
        
    Returns:
        Información WHOIS del dominio/IP
    """
    try:
        # Verificar que whois está instalado
        try:
            subprocess.run(['which', 'whois'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            return "❌ Error: whois no está instalado. Instálalo con: sudo apt install whois"
        
        print(f"[*] Consultando información WHOIS de: {domain}")
        
        # Ejecutar whois
        result = subprocess.run(
            ["whois", domain],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return f"❌ Error ejecutando whois: {result.stderr}"
        
        output = result.stdout
        
        if not output or "No match" in output or "NOT FOUND" in output:
            return f"ℹ️  No se encontró información WHOIS para: {domain}"
        
        # Extraer información clave
        key_info = []
        
        for line in output.split('\n'):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in [
                'registrar:', 'creation date:', 'expiration date:', 
                'updated date:', 'name server:', 'status:'
            ]):
                key_info.append(line.strip())
        
        # Guardar en archivo si se especificó
        if save_to_file:
            with open(save_to_file, 'w') as f:
                f.write(f"Consulta WHOIS para: {domain}\n")
                f.write("=" * 70 + "\n\n")
                f.write(output)
            
            output += f"\n\n📄 Resultados guardados en: {save_to_file}"
        
        # Agregar resumen
        if key_info:
            summary = "\n\n📋 INFORMACIÓN CLAVE:\n" + "\n".join(f"  • {info}" for info in key_info[:10])
            output = summary + "\n\n" + "─" * 70 + "\n\n" + output
        
        return output
    
    except subprocess.TimeoutExpired:
        return "❌ Error: La consulta WHOIS excedió el tiempo límite"
    except Exception as e:
        return f"❌ Error durante la consulta: {str(e)}"


@function_tool
def dns_lookup_tool(domain: str) -> str:
    """
    Realiza una consulta DNS para obtener la dirección IP de un dominio.
    
    Útil para verificar la resolución de nombres y detectar problemas de DNS.

    Args:
        domain: Dominio a resolver (ej: 'google.com')
        
    Returns:
        Dirección IP asociada al dominio
    """
    try:
        print(f"[*] Resolviendo DNS para: {domain}")
        
        # Resolver el dominio
        ip_address = socket.gethostbyname(domain)
        
        # Intentar obtener el nombre completo (FQDN)
        try:
            fqdn = socket.getfqdn(domain)
        except:
            fqdn = domain
        
        output = f"✅ Resolución DNS exitosa:\n\n"
        output += f"  🌐 Dominio: {domain}\n"
        output += f"  📍 IP: {ip_address}\n"
        output += f"  🔗 FQDN: {fqdn}\n"
        
        return output
    
    except socket.gaierror:
        return f"❌ Error: No se pudo resolver el dominio '{domain}'. Verifica que existe y que tienes conexión a Internet."
    except Exception as e:
        return f"❌ Error durante la consulta DNS: {str(e)}"


@function_tool
def reverse_dns_lookup_tool(ip_address: str) -> str:
    """
    Realiza una consulta DNS inversa para obtener el nombre de dominio de una IP.

    Args:
        ip_address: Dirección IP a consultar (ej: '8.8.8.8')
        
    Returns:
        Nombre de dominio asociado a la IP
    """
    try:
        print(f"[*] Consultando DNS inverso para: {ip_address}")
        
        # Validar formato de IP básico
        parts = ip_address.split('.')
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            return f"❌ Error: '{ip_address}' no es una dirección IP válida"
        
        # Realizar consulta inversa
        hostname = socket.gethostbyaddr(ip_address)
        
        output = f"✅ DNS inverso encontrado:\n\n"
        output += f"  📍 IP: {ip_address}\n"
        output += f"  🌐 Hostname: {hostname[0]}\n"
        
        if hostname[1]:  # Aliases
            output += f"  🔗 Aliases: {', '.join(hostname[1])}\n"
        
        return output
    
    except socket.herror:
        return f"ℹ️  No se encontró registro DNS inverso para: {ip_address}"
    except socket.gaierror:
        return f"❌ Error: '{ip_address}' no es válida o no hay conexión"
    except Exception as e:
        return f"❌ Error: {str(e)}"


# Exportar herramientas
__all__ = ['whois_lookup_tool', 'dns_lookup_tool', 'reverse_dns_lookup_tool']
