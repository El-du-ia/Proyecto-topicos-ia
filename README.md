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

- **Gestión de Sesiones Persistentes**: Reanuda conversaciones desde donde las dejaste
  - Lista todas las sesiones guardadas
  - Carga el contexto completo de conversaciones anteriores
  - Busca sesiones por contenido
  - Mantiene el historial entre ejecuciones

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
sudo ./[nombre_entorno_virtual]/bin/python main.py
```

**Explicación:**
Cuando ejecutas `sudo python`, se usa el Python del sistema (root) que NO tiene instaladas las dependencias (CAI, Scapy, etc.). Ejecutar `sudo ./cai_env_sexo/bin/python main.py` resuelven esto automáticamente usando el Python del entorno virtual.

## 🚀 Instalación

1. **Clonar/ubicar el proyecto:**
```bash
cd /home/kali/topicos_IA
```

```bash
git clone https://github.com/El-du-ia/Proyecto-topicos-ia.git
```

2. **Crear y activar entorno virtual (si no existe):**

Crea el entorno:
```bash
python -m venv TAI_env

```

Activa el entorno:
```bash
source TAI_env/bin/activate

```

3. **Instalar dependencias:**

**Explicación:**
    Se usa uv como instalador de paquetes mas rapido que pip y menos tardado en la instalacion de dependencias

```bash
 pip install uv
```

```bash
 uv pip install cai-framework && pip install scapy
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
# Sin privilegios especiales (no recomendado)
python main.py

# Con privilegios sudo (para probar todo su potencial)
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

### Comandos Especiales en el Terminal

Durante el chat interactivo, puedes usar estos comandos:

**Gestión de Sesiones:**
- `/sessions` - Listar todas las sesiones guardadas
- `/load <id>` - Reanudar una sesión anterior
- `/search <texto>` - Buscar sesiones por contenido
- `/history` - Ver historial de la sesión actual
- `/info` - Información detallada de la sesión actual

**Información:**
- `/help` - Mostrar ayuda completa
- `/tools` - Listar herramientas disponibles
- `/examples` - Ver ejemplos de uso
- `/status` - Estado del sistema
- `/permisos` - Ver permisos del sistema
- `/cost` - Ver costos de API

**Otros:**
- `/clear` - Limpiar pantalla
- `/exit` o `/quit` - Salir

### Ejemplos de Uso

```bash
# En el modo interactivo, puedes escribir:

"Escanea la IP 192.168.1.1"
"Captura 100 paquetes en wlan0"
"Busca información WHOIS de google.com"
"Analiza el log /var/log/auth.log buscando errores"
"Muestra las últimas 50 líneas de /var/log/syslog"
```

### Reanudar Conversaciones Anteriores

```bash
# Listar sesiones guardadas
🤖 dui-IA > /sessions

# Cargar una sesión específica
🤖 dui-IA > /load 0a28b9e5

# El agente recordará toda la conversación anterior
🤖 dui-IA > continúa con el análisis de red que estábamos haciendo
```

Ver documentación completa: [docs/GESTION_SESIONES.md](docs/GESTION_SESIONES.md)

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
├── demo_sessions.py          # Demo de gestión de sesiones
├── requirements.txt          # Dependencias
├── .env                      # Configuración (API keys)
│
├── src/
│   ├── core/
│   │   ├── agent_controller.py    # Controlador principal
│   │   ├── tool_manager.py        # Gestor de herramientas
│   │   ├── interpreter.py         # Traductor de resultados
│   │   └── permissions.py         # Gestión de permisos
│   │
│   ├── tools/
│   │   ├── cai_tools_wrapper.py   # Herramientas CAI
│   │   ├── nmap_tool.py           # Escaneo de red
│   │   ├── whois_tool.py          # WHOIS y DNS
│   │   └── log_analyzer_tool.py   # Análisis de logs
│   │
│   ├── ui/
│   │   ├── cli_interface.py       # Interfaz de terminal
│   │   ├── custom_terminal.py     # Terminal personalizada (coordinador)
│   │   ├── terminal_display.py    # Funciones de visualización
│   │   ├── terminal_commands.py   # Manejador de comandos
│   │   ├── session_commands.py    # Comandos de gestión de sesiones
│   │   └── prompts.py             # Mensajes amigables
│   │
│   └── models/
│       ├── conversation_memory.py # Memoria de sesión
│       └── session_manager.py     # Gestión de sesiones persistentes
│
├── logs/                     # Logs de sesiones (JSONL)
├── reports/                  # Reportes generados (futuro)
├── memory/                   # Memoria persistente de conversaciones
└── docs/                     # Documentación adicional
    ├── GESTION_SESIONES.md   # Guía de gestión de sesiones
    ├── PERMISOS.md           # Documentación de permisos
    └── architecture.md       # Arquitectura del sistema
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
Ubicación: `logs/cai_*.jsonl` (formato JSONL)

Contiene:
- Todas las acciones ejecutadas
- Aprobaciones/rechazos del usuario
- Herramientas utilizadas
- Timestamps de cada operación
- Uso de tokens y costos de API

### Memoria Conversacional
Ubicación: `memory/{session_id}_memory.json`

Guarda:
- Historial completo de mensajes
- Contexto de la conversación
- Metadatos de sesión
- Puede ser recargado para reanudar conversaciones


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

###  Fase 2 - Reportes (Próximo)

#### ✅ Fase 2.1 Sistema de sesiones persistentes**
  - Guardar y cargar conversaciones completas
  - Búsqueda de sesiones por contenido
  - Reanudar desde donde se quedó

#### Fase 2.2
- Conexion con AWS para almacenaminto.
- Generación automática de reportes
- Exportación a PDF/Markdown
- Resumen ejecutivo
- Templates personalizablesvo
- Templates personalizables

### 📅 Fase 3 - UX Mejorada
- CLI con rich (colores avanzados)
- Menú interactivo mejorado
- Memoria persistente entre sesiones
- Sugerencias inteligentes

### 📅 Fase 4 - Características Avanzadas (futuro)
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
El dui-IA Team

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
