# Especificación de Herramientas - Agente de Ciberseguridad

## Índice
- [Herramientas de Red](#herramientas-de-red)
- [Herramientas de Reconocimiento](#herramientas-de-reconocimiento)
- [Herramientas de Análisis](#herramientas-de-análisis)
- [Metadatos y Clasificación](#metadatos-y-clasificación)

---

## Herramientas de Red

### 1. network_sniffer_tool

**Propósito**: Captura de paquetes de red usando Scapy

**Categoría**: `network`

**Sensibilidad**: ⚠️ Alta (requiere confirmación + root)

**Firma**:
```python
def network_sniffer_tool(interface: str, count: int, filename: str) -> str
```

**Parámetros**:
- `interface` (str): Interfaz de red (ej: "eth0", "wlan0")
- `count` (int): Número de paquetes a capturar
- `filename` (str): Archivo donde guardar resultados

**Ejemplo de uso**:
```
"Captura 100 paquetes en wlan0 y guárdalos en capture.txt"
```

**Output esperado**:
```
✅ Captura exitosa: 100 paquetes guardados en 'capture.txt'
```

**Casos de error**:
- `PermissionError`: No ejecutado con sudo
- `Exception`: Interfaz no existe o no está activa

---

### 2. nmap_scan_tool

**Propósito**: Escaneo de puertos y servicios con Nmap

**Categoría**: `network`

**Sensibilidad**: ⚠️ Alta (requiere confirmación)

**Firma**:
```python
def nmap_scan_tool(target: str, scan_type: str = "basic", 
                   output_file: str = None) -> str
```

**Parámetros**:
- `target` (str): IP, rango o dominio (ej: "192.168.1.1", "192.168.1.0/24")
- `scan_type` (str): Tipo de escaneo
  - `"basic"`: Escaneo básico de puertos comunes
  - `"full"`: Todos los puertos (1-65535)
  - `"stealth"`: SYN scan sigiloso
  - `"service"`: Detección de versiones
- `output_file` (str, opcional): Guardar resultados en archivo

**Ejemplo de uso**:
```
"Escanea 192.168.1.1 tipo basic"
"Escanea la red 192.168.1.0/24 tipo stealth y guarda en scan.txt"
```

**Output esperado**:
```
Starting Nmap scan...
Host is up (0.0010s latency).
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http

🎯 RESUMEN: Se encontraron 2 puertos abiertos en 192.168.1.1
```

**Interpretación automática**:
- Puertos peligrosos detectados → Severidad HIGH
- Más de 10 puertos abiertos → Severidad MEDIUM
- Normal → Severidad LOW

---

### 3. nmap_ping_sweep

**Propósito**: Descubrimiento rápido de hosts activos

**Categoría**: `network`

**Sensibilidad**: ⚠️ Media (requiere confirmación)

**Firma**:
```python
def nmap_ping_sweep(network: str) -> str
```

**Parámetros**:
- `network` (str): Red en notación CIDR (ej: "192.168.1.0/24")

**Ejemplo de uso**:
```
"Encuentra hosts activos en la red 192.168.1.0/24"
```

**Output esperado**:
```
✅ Se encontraron 5 hosts activos:
  • 192.168.1.1
  • 192.168.1.10
  • 192.168.1.20
  • 192.168.1.100
  • 192.168.1.254
```

---

## Herramientas de Reconocimiento

### 4. whois_lookup_tool

**Propósito**: Consulta información de registro de dominios

**Categoría**: `reconnaissance`

**Sensibilidad**: ✅ Baja (sin confirmación)

**Firma**:
```python
def whois_lookup_tool(domain: str, save_to_file: str = None) -> str
```

**Parámetros**:
- `domain` (str): Dominio o IP (ej: "google.com", "8.8.8.8")
- `save_to_file` (str, opcional): Guardar en archivo

**Ejemplo de uso**:
```
"Busca información WHOIS de google.com"
"¿Quién es el dueño de example.org?"
```

**Output esperado**:
```
📋 INFORMACIÓN CLAVE:
  • Registrador: MarkMonitor Inc.
  • Fecha de creación: 1997-09-15
  • Fecha de expiración: 2028-09-14
  • Servidores DNS: ns1.google.com, ns2.google.com
```

---

### 5. dns_lookup_tool

**Propósito**: Resolución DNS (dominio → IP)

**Categoría**: `reconnaissance`

**Sensibilidad**: ✅ Baja

**Firma**:
```python
def dns_lookup_tool(domain: str) -> str
```

**Parámetros**:
- `domain` (str): Dominio a resolver

**Ejemplo de uso**:
```
"¿Cuál es la IP de github.com?"
"Resuelve google.com"
```

**Output esperado**:
```
✅ Resolución DNS exitosa:
  🌐 Dominio: github.com
  📍 IP: 140.82.121.4
```

---

### 6. reverse_dns_lookup_tool

**Propósito**: DNS inverso (IP → dominio)

**Categoría**: `reconnaissance`

**Sensibilidad**: ✅ Baja

**Firma**:
```python
def reverse_dns_lookup_tool(ip_address: str) -> str
```

**Parámetros**:
- `ip_address` (str): IP a consultar

**Ejemplo de uso**:
```
"¿A qué dominio pertenece la IP 8.8.8.8?"
"DNS inverso de 1.1.1.1"
```

**Output esperado**:
```
✅ DNS inverso encontrado:
  📍 IP: 8.8.8.8
  🌐 Hostname: dns.google
```

---

## Herramientas de Análisis

### 7. analyze_log_tool

**Propósito**: Análisis inteligente de archivos de log

**Categoría**: `analysis`

**Sensibilidad**: ✅ Media (puede requerir sudo para ciertos logs)

**Firma**:
```python
def analyze_log_tool(log_file_path: str, patterns: str = "errors", 
                     max_lines: int = 1000) -> str
```

**Parámetros**:
- `log_file_path` (str): Ruta al archivo (ej: "/var/log/syslog")
- `patterns` (str): Tipo de análisis
  - `"errors"`: Busca errores y fallos
  - `"auth"`: Analiza autenticación
  - `"suspicious"`: Busca actividad sospechosa
  - `"all"`: Análisis completo
- `max_lines` (int): Máximo de líneas a procesar

**Ejemplo de uso**:
```
"Analiza /var/log/auth.log buscando errores"
"Revisa el syslog completo buscando actividad sospechosa"
```

**Output esperado**:
```
📊 ANÁLISIS DE LOG: auth.log
══════════════════════════════════════

📁 Archivo: /var/log/auth.log
📏 Líneas analizadas: 1000
🔍 Hallazgos: 15

📋 RESUMEN POR CATEGORÍA:

🔹 Autenticación: 15 eventos
   Línea 850: Failed password for invalid user admin
   Línea 851: Failed password for root
   ... y 13 eventos más

💡 RECOMENDACIONES:
  ⚠️  Múltiples fallos de autenticación. Posible ataque.
```

**Patrones detectados**:

**Errores**: `error`, `fail`, `crash`, `exception`, `warning`, `critical`

**Autenticación**: `Failed password`, `authentication failure`, `Invalid user`

**Sospechoso**: `brute force`, `attack`, `exploit`, `malware`, `unauthorized`

---

### 8. tail_log_tool

**Propósito**: Visualización de últimas líneas de log

**Categoría**: `analysis`

**Sensibilidad**: ✅ Baja

**Firma**:
```python
def tail_log_tool(log_file_path: str, lines: int = 20) -> str
```

**Parámetros**:
- `log_file_path` (str): Ruta al archivo
- `lines` (int): Número de líneas a mostrar

**Ejemplo de uso**:
```
"Muestra las últimas 50 líneas de /var/log/syslog"
"Cola del archivo messages"
```

**Output esperado**:
```
📄 Últimas 20 líneas de: syslog
══════════════════════════════════════

Nov 25 10:30:01 hostname CRON[12345]: (root) CMD (...)
Nov 25 10:30:15 hostname systemd[1]: Started session
...
```

---

## Metadatos y Clasificación

### Estructura de Metadatos

Cada herramienta se registra con:

```python
{
    "name": "tool_name",
    "description": "Qué hace la herramienta",
    "category": "network|reconnaissance|analysis",
    "is_sensitive": bool,
    "requires_root": bool
}
```

### Categorías

**network**: Herramientas que interactúan directamente con la red
- Escaneos
- Capturas de paquetes
- Pruebas de conectividad

**reconnaissance**: Recopilación de información sin impacto
- WHOIS
- DNS
- Consultas públicas

**analysis**: Procesamiento y análisis de datos
- Logs
- Archivos
- Resultados de otras herramientas

### Niveles de Sensibilidad

**is_sensitive = True**: Requiere confirmación del usuario
- Puede generar alertas
- Puede afectar el rendimiento
- Puede ser detectado por IDS/IPS

**requires_root = True**: Necesita privilegios elevados
- Acceso a interfaces de red
- Lectura de logs protegidos
- Operaciones a nivel de kernel

### Matriz de Herramientas

| Herramienta | Categoría | Sensible | Root | Confirmación |
|-------------|-----------|----------|------|--------------|
| network_sniffer_tool | network | ✅ | ✅ | Sí |
| nmap_scan_tool | network | ✅ | ❌ | Sí |
| nmap_ping_sweep | network | ✅ | ❌ | Sí |
| whois_lookup_tool | reconnaissance | ❌ | ❌ | No |
| dns_lookup_tool | reconnaissance | ❌ | ❌ | No |
| reverse_dns_lookup_tool | reconnaissance | ❌ | ❌ | No |
| analyze_log_tool | analysis | ❌ | ⚠️* | No |
| tail_log_tool | analysis | ❌ | ⚠️* | No |

*Puede requerir root dependiendo del archivo

---

## Flujo de Ejecución

### Herramienta No Sensible

```
Usuario → "Resuelve google.com"
    ↓
Agente identifica: dns_lookup_tool
    ↓
Validar argumentos
    ↓
Ejecutar directamente (no sensible)
    ↓
Retornar resultado
    ↓
Mostrar al usuario
```

### Herramienta Sensible

```
Usuario → "Escanea 192.168.1.1"
    ↓
Agente identifica: nmap_scan_tool
    ↓
Validar argumentos
    ↓
¿Es sensible? → SÍ
    ↓
Mostrar confirmación con riesgos
    ↓
Usuario aprueba → SÍ
    ↓
Ejecutar herramienta
    ↓
Registrar en logs
    ↓
Interpretar resultado
    ↓
Mostrar explicación simple
```

---

## Agregar Nueva Herramienta

### Plantilla

```python
from cai.sdk.agents import function_tool

@function_tool
def mi_nueva_herramienta(param1: str, param2: int) -> str:
    """
    Descripción breve de qué hace la herramienta.
    
    Esta herramienta [explicación en lenguaje simple].

    Args:
        param1: Descripción del parámetro 1
        param2: Descripción del parámetro 2
        
    Returns:
        Descripción del valor de retorno
    """
    try:
        # Tu lógica aquí
        result = hacer_algo(param1, param2)
        
        return f"✅ Operación exitosa: {result}"
    
    except PermissionError:
        return "❌ Error: Permisos insuficientes"
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

### Registro en main.py

```python
from src.tools.mi_modulo import mi_nueva_herramienta

tool_manager.register_tool(mi_nueva_herramienta, {
    "category": "custom",
    "is_sensitive": False,
    "requires_root": False
})
```

---

## Convenciones de Output

### Formato de Mensajes

**Éxito**: `✅ Operación exitosa`
**Error**: `❌ Error: descripción`
**Advertencia**: `⚠️  Advertencia: descripción`
**Info**: `ℹ️  Información: descripción`

### Estructura de Respuesta

```
[Emoji] TÍTULO
═══════════════════════════

📋 Sección 1
  • Dato 1
  • Dato 2

🔍 Sección 2
  • Hallazgo 1
  • Hallazgo 2

💡 RECOMENDACIONES
  ➜ Acción sugerida 1
  ➜ Acción sugerida 2
```

---

## Testing de Herramientas

### Checklist

- [ ] Función documentada con docstring
- [ ] Parámetros con type hints
- [ ] Manejo de errores con try/except
- [ ] Mensajes de salida formateados
- [ ] Validación de entrada
- [ ] Registrada en tool_manager
- [ ] Metadatos correctos
- [ ] Probada manualmente
- [ ] Output interpretable por ResultInterpreter

---

Esta especificación debe mantenerse actualizada con cada nueva herramienta agregada al sistema.
