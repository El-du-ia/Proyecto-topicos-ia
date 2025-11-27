# Agente Inteligente de Ciberseguridad 🛡️

Sistema de ciberseguridad basado en CAI (Cybersecurity AI) que permite ejecutar herramientas de seguridad, interpretar resultados técnicos en lenguaje simple y solicitar confirmación antes de acciones sensibles.

## 🎯 Características

### ✅ Implementado

- **Herramientas Personalizadas**: 8+ herramientas de ciberseguridad integradas
  - Escaneo de red (Nmap)
  - Captura de tráfico (Scapy)
  - Consultas WHOIS y DNS
  - Análisis de logs del sistema

- **Confirmación de Acciones**: Solicita aprobación antes de ejecutar comandos sensibles

- **Intérprete de Resultados**: Traduce salidas técnicas a explicaciones comprensibles

- **Registro Completo**: Todas las acciones quedan documentadas en logs JSON

- **Interfaz CLI Amigable**: Terminal con colores y mensajes claros

- **Memoria de Sesión**: Guarda el contexto de conversaciones

## 📋 Requisitos

- Python 3.8+
- Kali Linux o cualquier distribución Linux
- Privilegios sudo (para algunas herramientas)

### ⚠️ IMPORTANTE: Problema común con sudo

**❌ NO hagas esto:**
```bash
sudo python main.py  # Usará el Python del sistema, sin dependencias
```

**✅ Haz esto:**
```bash
sudo ./cai_env_sexo/bin/python main.py
```

**Explicación:**
Cuando ejecutas `sudo python`, se usa el Python del sistema (root) que NO tiene instaladas las dependencias (CAI, Scapy, etc.). Los scripts `run_as_root.sh` y `run.sh` resuelven esto automáticamente usando el Python del entorno virtual.

## 🚀 Instalación

1. **Clonar/ubicar el proyecto:**
```bash
cd /home/kali/topicos_IA
```

2. **Crear y activar entorno virtual (si no existe):**
```bash
python -m venv TAI_env
source TAI_env/bin/activate
```

3. **Instalar dependencias adicionales (si es necesario):**

se usa uv como instalador de paqutes mas rapido que pip 
```bash
 pip install uv
```

```bash
 uv pip install cai-framework
```

4. **Configurar variables de entorno:**
Asegúrate de que tu archivo `.env` tenga las API keys configuradas:
```
OPENAI_API_KEY="sk-1234"
ANTHROPIC_API_KEY=""
GEMINI_API_KEY="api?keyajsaojsoasoaosjoa"
OLLAMA=""
PROMPT_TOOLKIT_NO_CPR=1
CAI_STREAM=false
CAI_MODEL="gemini/gemini-2.5-flash"
```

## 💻 Uso

### Ejecución Básica

```bash
# Sin privilegios especiales
python main.py

# Con privilegios sudo (para captura de red)
sudo ./TAI_env/bin/python main.py
```

### Menú Principal

Al ejecutar, verás un menú con opciones:

1. **Chat interactivo** - Modo principal, conversación con el agente
2. **Ver herramientas** - Lista todas las herramientas disponibles
3. **Historial** - Muestra acciones de la sesión actual
4. **Comando rápido** - Ejecutar una acción específica
5. **Ayuda** - Documentación y ejemplos
6. **Salir** - Cerrar el programa

### Ejemplos de Uso

```bash
# En el modo interactivo, puedes escribir:

"Escanea la IP 192.168.1.1"
"Captura 100 paquetes en wlan0"
"Busca información WHOIS de google.com"
"Analiza el log /var/log/auth.log buscando errores"
"Muestra las últimas 50 líneas de /var/log/syslog"
```

## 🛠️ Herramientas Disponibles

### Red (Network)
- `network_sniffer_tool` - Captura paquetes de red ⚠️ Requiere sudo
- `nmap_scan_tool` - Escaneo de puertos con Nmap ⚠️ Sensible
- `nmap_ping_sweep` - Descubrimiento de hosts activos ⚠️ Sensible

### Reconocimiento (Reconnaissance)
- `whois_lookup_tool` - Consulta información de dominios
- `dns_lookup_tool` - Resolución DNS
- `reverse_dns_lookup_tool` - DNS inverso

### Análisis (Analysis)
- `analyze_log_tool` - Análisis inteligente de logs
- `tail_log_tool` - Visualización de logs

## 📁 Estructura del Proyecto

```
topicos_Ia_sexo/
├── main.py                    # Punto de entrada
├── toolTest.py               # Versión original (referencia)
├── requirements.txt          # Dependencias
├── .env                      # Configuración (API keys)
│
├── src/
│   ├── core/
│   │   ├── agent_controller.py    # Controlador principal
│   │   ├── tool_manager.py        # Gestor de herramientas
│   │   └── interpreter.py         # Traductor de resultados
│   │
│   ├── tools/
│   │   ├── cai_tools_wrapper.py   # Herramientas CAI
│   │   ├── nmap_tool.py           # Escaneo de red
│   │   ├── whois_tool.py          # WHOIS y DNS
│   │   └── log_analyzer_tool.py   # Análisis de logs
│   │
│   ├── ui/
│   │   ├── cli_interface.py       # Interfaz de terminal
│   │   └── prompts.py             # Mensajes amigables
│   │
│   └── models/
│       └── conversation_memory.py # Memoria de sesión
│
├── logs/                     # Logs de sesiones
├── reports/                  # Reportes generados (futuro)
├── memory/                   # Memoria persistente
└── docs/                     # Documentación adicional
```

## 🔒 Seguridad y Permisos

### Herramientas que requieren sudo:
- Captura de paquetes (`network_sniffer_tool`)
- Algunos logs del sistema (`/var/log/auth.log`, etc.)

### Herramientas sensibles (piden confirmación):
- Escaneos de red (Nmap)
- Captura de tráfico
- Cualquier comando que pueda afectar la red

## 📊 Logs y Reportes

### Logs de Sesión
Ubicación: `logs/session_YYYYMMDD_HHMMSS.json`

Contiene:
- Todas las acciones ejecutadas
- Aprobaciones/rechazos del usuario
- Herramientas utilizadas
- Timestamps de cada operación

### Memoria Conversacional
Ubicación: `memory/session_YYYYMMDD_HHMMSS_memory.json`

Guarda:
- Historial de mensajes
- Contexto de la conversación
- Metadatos de sesión


#### El agente no responde
- Verifica API key en `.env`
- Comprueba conexión a Internet
- Ejecuta: `python test_setup.py`
- Revisa logs en `logs/`


## 🗺️ Roadmap

### ✅ Fase 1 - MVP (Completada)
- Estructura modular del proyecto
- Herramientas personalizadas integradas
- Sistema de confirmación de acciones
- Intérprete básico de resultados
- CLI funcional

### 📅 Fase 2 - Reportes (Próximo)
- Generación automática de reportes
- Exportación a PDF/Markdown
- Templates personalizables
- Resumen ejecutivo

### 📅 Fase 3 - UX Mejorada
- CLI con rich (colores avanzados)
- Menú interactivo mejorado
- Memoria persistente entre sesiones
- Sugerencias inteligentes

### 📅 Fase 4 - Características Avanzadas
- Múltiples agentes especializados
- Integración con APIs externas (VirusTotal, Shodan)
- Dashboard web (FastAPI)
- Análisis automatizado de vulnerabilidades

## 🤝 Contribuciones

Este es un proyecto educativo para el curso de Topicos_IA. 

### Cómo agregar nuevas herramientas:

1. Crear un nuevo archivo en `src/tools/`
2. Decorar la función con `@function_tool`
3. Documentar parámetros y funcionalidad
4. Registrar en `main.py` con metadatos
5. Probar en modo interactivo

Ejemplo:
```python
from cai.sdk.agents import function_tool

@function_tool
def mi_herramienta(parametro: str) -> str:
    """
    Descripción de qué hace la herramienta.
    
    Args:
        parametro: Qué hace este parámetro
        
    Returns:
        Resultado de la operación
    """
    # Tu código aquí
    return "Resultado"
```

## 📝 Licencia

Proyecto educativo - Universidad/Institución

## 👤 Autor

El dui y el malcom tambien el break dance y tambien el manuelangas

## 🙏 Agradecimientos

- CAI Framework por la infraestructura base
- Comunidad de Kali Linux
- Herramientas open source: Nmap, Scapy, Wireshark
- La chona 
- MI apa y mi ama
- El departamento de fotrografia de NEW YORK
- Alguin mas pero no recuendo como se llama pero simon tambien el

---

**Nota**: Este software está diseñado para uso educativo y pruebas en entornos autorizados. 
El uso de herramientas de seguridad en redes sin autorización puede ser ilegal.
No no hcemos responsables del mal uso de esta herraminta tome sus precuaciones.
