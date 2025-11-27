"""
ResultInterpreter: Traduce resultados técnicos a lenguaje simple para usuarios no expertos
"""

from typing import Dict, Any, List
import re


class ResultInterpreter:
    """
    Interpreta y traduce resultados técnicos de herramientas de seguridad
    a explicaciones comprensibles para usuarios sin conocimientos técnicos.
    """
    
    def __init__(self):
        """Inicializa el intérprete de resultados"""
        self.severity_levels = {
            "critical": "🔴 CRÍTICO",
            "high": "🟠 ALTO",
            "medium": "🟡 MEDIO",
            "low": "🟢 BAJO",
            "info": "🔵 INFORMATIVO"
        }
        
        print("[*] ResultInterpreter inicializado")
    
    def interpret_nmap_output(self, raw_output: str) -> Dict[str, Any]:
        """
        Interpreta resultados de escaneo nmap.
        
        Args:
            raw_output: Output crudo de nmap
            
        Returns:
            Diccionario con interpretación simplificada
        """
        interpretation = {
            "summary": "",
            "findings": [],
            "severity": "info",
            "recommendations": [],
            "simple_explanation": ""
        }
        
        # Detectar puertos abiertos
        open_ports = re.findall(r'(\d+)/tcp\s+open\s+(\w+)', raw_output)
        
        if open_ports:
            port_count = len(open_ports)
            port_list = [f"{port} ({service})" for port, service in open_ports]
            
            interpretation["summary"] = f"Se encontraron {port_count} puertos abiertos"
            interpretation["findings"] = port_list
            
            # Evaluar severidad
            dangerous_ports = ['21', '23', '3389', '445', '135']
            has_dangerous = any(port in dangerous_ports for port, _ in open_ports)
            
            if has_dangerous:
                interpretation["severity"] = "high"
                interpretation["recommendations"].append(
                    "Se detectaron puertos potencialmente peligrosos. Considera cerrarlos si no son necesarios."
                )
            elif port_count > 10:
                interpretation["severity"] = "medium"
                interpretation["recommendations"].append(
                    "Muchos puertos abiertos aumentan la superficie de ataque. Revisa cuáles son realmente necesarios."
                )
            else:
                interpretation["severity"] = "low"
            
            # Explicación simple
            interpretation["simple_explanation"] = self._generate_port_explanation(open_ports)
        else:
            interpretation["summary"] = "No se encontraron puertos abiertos o el host no está accesible"
            interpretation["severity"] = "info"
            interpretation["simple_explanation"] = (
                "El dispositivo analizado no tiene servicios accesibles desde la red, "
                "lo cual puede ser bueno para la seguridad (menos puntos de entrada para atacantes) "
                "o puede significar que el dispositivo está apagado o protegido por un firewall."
            )
        
        return interpretation
    
    def interpret_packet_capture(self, raw_output: str, packet_count: int) -> Dict[str, Any]:
        """
        Interpreta resultados de captura de paquetes.
        
        Args:
            raw_output: Output de captura (Scapy, tcpdump, etc.)
            packet_count: Número de paquetes capturados
            
        Returns:
            Diccionario con interpretación simplificada
        """
        interpretation = {
            "summary": f"Se capturaron {packet_count} paquetes de red",
            "findings": [],
            "severity": "info",
            "recommendations": [],
            "simple_explanation": ""
        }
        
        # Analizar protocolos
        protocols = {
            "TCP": raw_output.count("TCP"),
            "UDP": raw_output.count("UDP"),
            "ICMP": raw_output.count("ICMP"),
            "DNS": raw_output.count("DNS"),
            "HTTP": raw_output.count("HTTP"),
            "HTTPS": raw_output.count("https")
        }
        
        # Filtrar protocolos presentes
        active_protocols = {k: v for k, v in protocols.items() if v > 0}
        
        interpretation["findings"] = [
            f"{proto}: {count} paquetes" for proto, count in active_protocols.items()
        ]
        
        # Detectar tráfico sospechoso
        suspicious = []
        
        if protocols["HTTP"] > protocols["HTTPS"] * 2:
            suspicious.append("Alto tráfico HTTP no cifrado detectado")
            interpretation["severity"] = "medium"
        
        if "IRC" in raw_output or "6667" in raw_output:
            suspicious.append("Tráfico IRC detectado (común en botnets)")
            interpretation["severity"] = "high"
        
        if suspicious:
            interpretation["recommendations"].extend(suspicious)
        
        # Explicación simple
        interpretation["simple_explanation"] = (
            f"Se monitoreó el tráfico de red y se capturaron {packet_count} paquetes de datos. "
            f"Los protocolos más activos fueron: {', '.join(active_protocols.keys())}. "
        )
        
        if protocols["HTTPS"] > protocols["HTTP"]:
            interpretation["simple_explanation"] += (
                "La mayoría del tráfico está cifrado (HTTPS), lo cual es bueno para la privacidad."
            )
        else:
            interpretation["simple_explanation"] += (
                "⚠️ Hay bastante tráfico sin cifrar (HTTP), lo que podría exponer información sensible."
            )
        
        return interpretation
    
    def interpret_whois(self, raw_output: str) -> Dict[str, Any]:
        """
        Interpreta resultados de consulta WHOIS.
        
        Args:
            raw_output: Output de whois
            
        Returns:
            Diccionario con interpretación simplificada
        """
        interpretation = {
            "summary": "Información de registro de dominio",
            "findings": [],
            "severity": "info",
            "recommendations": [],
            "simple_explanation": ""
        }
        
        # Extraer información clave
        registrar = re.search(r'Registrar:\s*(.+)', raw_output)
        creation_date = re.search(r'Creation Date:\s*(.+)', raw_output)
        expiration_date = re.search(r'Expiration Date:\s*(.+)', raw_output)
        
        if registrar:
            interpretation["findings"].append(f"Registrador: {registrar.group(1)}")
        if creation_date:
            interpretation["findings"].append(f"Fecha de creación: {creation_date.group(1)}")
        if expiration_date:
            interpretation["findings"].append(f"Fecha de expiración: {expiration_date.group(1)}")
        
        interpretation["simple_explanation"] = (
            "WHOIS proporciona información pública sobre quién registró un dominio web. "
            "Es útil para verificar la legitimidad de un sitio o identificar al propietario de un dominio sospechoso."
        )
        
        return interpretation
    
    def interpret_log_analysis(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Interpreta resultados de análisis de logs.
        
        Args:
            findings: Lista de hallazgos del análisis
            
        Returns:
            Diccionario con interpretación simplificada
        """
        interpretation = {
            "summary": f"Se analizaron logs y se encontraron {len(findings)} eventos relevantes",
            "findings": [],
            "severity": "info",
            "recommendations": [],
            "simple_explanation": ""
        }
        
        # Categorizar hallazgos
        errors = [f for f in findings if f.get("type") == "error"]
        warnings = [f for f in findings if f.get("type") == "warning"]
        suspicious = [f for f in findings if f.get("type") == "suspicious"]
        
        interpretation["findings"] = [
            f"Errores: {len(errors)}",
            f"Advertencias: {len(warnings)}",
            f"Eventos sospechosos: {len(suspicious)}"
        ]
        
        # Determinar severidad
        if len(suspicious) > 5:
            interpretation["severity"] = "high"
            interpretation["recommendations"].append(
                "Múltiples eventos sospechosos detectados. Requiere investigación inmediata."
            )
        elif len(errors) > 10:
            interpretation["severity"] = "medium"
            interpretation["recommendations"].append(
                "Muchos errores en los logs. Puede indicar problemas de sistema o intentos de ataque."
            )
        
        # Explicación simple
        interpretation["simple_explanation"] = (
            "Los logs (registros) son como el 'diario' del sistema, donde se guardan todos los eventos. "
            f"Se revisaron los registros y se encontraron {len(findings)} eventos que requieren atención. "
        )
        
        if suspicious:
            interpretation["simple_explanation"] += (
                f"⚠️ {len(suspicious)} de estos eventos parecen sospechosos y podrían indicar "
                "intentos de acceso no autorizado o comportamiento anómalo."
            )
        
        return interpretation
    
    def _generate_port_explanation(self, open_ports: List[tuple]) -> str:
        """Genera explicación simple sobre puertos abiertos"""
        port_explanations = {
            "21": "FTP (transferencia de archivos, protocolo antiguo e inseguro)",
            "22": "SSH (acceso remoto seguro al servidor)",
            "23": "Telnet (acceso remoto sin cifrar, muy inseguro)",
            "80": "HTTP (servidor web sin cifrado)",
            "443": "HTTPS (servidor web cifrado)",
            "3306": "MySQL (base de datos)",
            "3389": "RDP (escritorio remoto de Windows)",
            "5432": "PostgreSQL (base de datos)",
            "8080": "HTTP alternativo (servidor web de prueba)",
        }
        
        explanation = "Los puertos abiertos son como 'puertas' por las que los programas se comunican:\n\n"
        
        for port, service in open_ports[:5]:  # Máximo 5 para no saturar
            port_desc = port_explanations.get(port, f"{service} (servicio en el puerto {port})")
            explanation += f"  • Puerto {port}: {port_desc}\n"
        
        if len(open_ports) > 5:
            explanation += f"\n  ... y {len(open_ports) - 5} puertos más."
        
        return explanation
    
    def format_interpretation(self, interpretation: Dict[str, Any]) -> str:
        """
        Formatea una interpretación para mostrarla en consola.
        
        Args:
            interpretation: Diccionario de interpretación
            
        Returns:
            String formateado para imprimir
        """
        severity = self.severity_levels.get(interpretation.get("severity", "info"), "ℹ️  INFO")
        
        output = "\n" + "="*80 + "\n"
        output += f"{severity} - {interpretation['summary']}\n"
        output += "="*80 + "\n\n"
        
        output += "📋 EXPLICACIÓN:\n"
        output += interpretation['simple_explanation'] + "\n\n"
        
        if interpretation['findings']:
            output += "🔍 DETALLES TÉCNICOS:\n"
            for finding in interpretation['findings']:
                output += f"  • {finding}\n"
            output += "\n"
        
        if interpretation['recommendations']:
            output += "💡 RECOMENDACIONES:\n"
            for rec in interpretation['recommendations']:
                output += f"  ➜ {rec}\n"
            output += "\n"
        
        output += "="*80 + "\n"
        
        return output
