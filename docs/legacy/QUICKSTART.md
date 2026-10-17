# 🚀 Guía de Inicio Rápido - Agente de Ciberseguridad

## ✅ Fase 1 Completada

Has creado exitosamente un **Agente Inteligente de Ciberseguridad** completo con todas las características de la Fase 1.

## 📦 ¿Qué se ha creado?

### 🏗️ Arquitectura Completa

```
✅ Core (Núcleo del sistema)
   ├── agent_controller.py    - Orquestador principal
   ├── tool_manager.py         - Gestor de herramientas
   └── interpreter.py          - Traductor de resultados técnicos

✅ Tools (8 herramientas personalizadas)
   ├── network_sniffer_tool    - Captura de paquetes
   ├── nmap_scan_tool          - Escaneo de puertos
   ├── nmap_ping_sweep         - Descubrimiento de hosts
   ├── whois_lookup_tool       - Información de dominios
   ├── dns_lookup_tool         - Resolución DNS
   ├── reverse_dns_lookup_tool - DNS inverso
   ├── analyze_log_tool        - Análisis de logs
   └── tail_log_tool           - Visualización de logs

✅ UI (Interfaz de usuario)
   ├── cli_interface.py        - CLI con colores y formato
   └── prompts.py              - Mensajes amigables

✅ Models (Persistencia)
   └── conversation_memory.py  - Memoria de sesiones

✅ Documentación
   ├── README.md               - Guía completa
   ├── architecture.md         - Arquitectura técnica
   └── QUICKSTART.md          - Esta guía
```

## 🎯 Características Implementadas

### ✅ Completado en Fase 1:

1. **Sistema de Confirmación**
   - Detecta automáticamente acciones sensibles
   - Solicita aprobación del usuario
   - Explica riesgos claramente

2. **Interpretación de Resultados**
   - Traduce outputs técnicos a lenguaje simple
   - Genera explicaciones comprensibles
   - Proporciona recomendaciones

3. **Registro Completo**
   - Todas las acciones se guardan en `logs/`
   - Memoria conversacional en `memory/`
   - Timestamps y metadatos

4. **Herramientas Integradas**
   - 8 herramientas de ciberseguridad
   - Integración con CAI framework
   - Validación de argumentos

5. **CLI Amigable**
   - Colores y formato visual
   - Mensajes claros para no expertos
   - Menú interactivo

## 🏃 Primeros Pasos

### 1. Verificar Instalación

```bash
cd /home/kali/topicos_Ia
python verify_setup.py
```

Deberías ver todos los checkmarks ✅ en verde.

### 2. Ejecutar el Agente

```bash
# Modo normal (la mayoría de herramientas)
python main.py

# Con privilegios sudo (para captura de paquetes)
sudo python main.py
```

### 3. Probar en Modo Interactivo

1. Selecciona opción `1` (Chat interactivo)
2. Prueba con comandos simples:

```
"Muestra las herramientas disponibles"
"Busca información WHOIS de google.com"
"Resuelve la IP de github.com"
```

### 4. Probar Herramientas Sensibles

```
"Escanea la IP 192.168.1.1"
```

El sistema:
1. Te explicará qué va a hacer
2. Mostrará riesgos potenciales
3. Pedirá tu confirmación
4. Ejecutará si apruebas
5. Traducirá los resultados a lenguaje simple

## 📝 Ejemplos de Uso

### Ejemplo 1: Escaneo Básico

```
Usuario: "Escanea mi router en 192.168.1.1"

Agente: 
⚠️  CONFIRMACIÓN REQUERIDA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Acción: Escanear puertos de 192.168.1.1

Riesgos potenciales:
  • Puede generar alertas en sistemas de detección
  • El escaneo puede ser detectado por el objetivo

¿Deseas continuar? [s/n]: s

[*] Ejecutando: nmap_scan_tool
[Resultados traducidos a lenguaje simple...]
```

### Ejemplo 2: Consulta WHOIS

```
Usuario: "¿Quién es el dueño de google.com?"

Agente: 
[*] Consultando información WHOIS...

📋 INFORMACIÓN CLAVE:
  • Registrador: MarkMonitor Inc.
  • Fecha de creación: 1997-09-15
  • Fecha de expiración: 2028-09-14

WHOIS proporciona información pública sobre quién 
registró un dominio web...
```

### Ejemplo 3: Análisis de Logs

```
Usuario: "Revisa el log de autenticación buscando problemas"

Agente:
[*] Analizando /var/log/auth.log...

📊 ANÁLISIS COMPLETADO

Se encontraron 15 eventos relevantes:
  • 12 intentos de login fallidos
  • 3 accesos exitosos

⚠️ RECOMENDACIÓN: Múltiples fallos de autenticación 
pueden indicar un ataque de fuerza bruta.
```

## 🛠️ Comandos Útiles

### Gestión del Sistema

```bash
# Ver estructura del proyecto
tree -L 3 -I '__pycache__|*.pyc|cai_env'

# Ver logs de sesiones
ls -lh logs/

# Ver memoria conversacional
ls -lh memory/

# Limpiar logs antiguos
rm logs/*.jsonl
```

### Durante el Uso

En el modo interactivo, puedes usar:

- `help` - Mostrar ayuda
- `tools` - Listar herramientas
- `history` - Ver historial
- `exit` - Salir

## 🔧 Solución de Problemas Comunes

### ❌ "Permission denied" en captura de paquetes

```bash
# Ejecutar con sudo
sudo python main.py
```

### ❌ "nmap: command not found"

```bash
sudo apt update
sudo apt install nmap
```

### ❌ Error de importación

```bash
# Activar entorno virtual
source cai_env/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### ❌ API Key no configurada

Edita el archivo `.env`:
```bash
nano .env
```

Asegúrate de tener:
```
GEMINI_API_KEY="tu_api_key_aqui"
CAI_MODEL="gemini/gemini-2.5-flash"
```

## 📊 Entendiendo los Logs

### logs/session_*.json

```json
{
  "timestamp": "2024-11-25T10:30:00",
  "session_id": "session_20241125_103000",
  "action_type": "tool_execution",
  "data": {
    "tool": "nmap_scan_tool",
    "args": {"target": "192.168.1.1"},
    "approved": true
  }
}
```

### memory/session_*_memory.json

```json
{
  "metadata": {
    "session_id": "session_20241125_103000",
    "created_at": "2024-11-25T10:30:00"
  },
  "messages": [
    {
      "role": "user",
      "content": "Escanea 192.168.1.1",
      "timestamp": "2024-11-25T10:30:15"
    }
  ]
}
```

## 🎓 Conceptos Clave para Usuarios

### ¿Qué hace cada herramienta?

**Escaneo de Red (Nmap)**
- Como "tocar las puertas" de un dispositivo
- Descubre qué servicios están activos
- Identifica posibles vulnerabilidades

**Captura de Paquetes**
- "Escucha" el tráfico de red
- Detecta comunicaciones sospechosas
- Monitorea actividad de dispositivos

**WHOIS/DNS**
- "Cédula de identidad" de sitios web
- Verifica legitimidad de dominios
- Identifica propietarios

**Análisis de Logs**
- Revisa el "diario" del sistema
- Detecta errores y problemas
- Identifica intentos de intrusión

## 🚀 Próximos Pasos

### Fase 2 - Reportes (Próxima)

- [ ] Generación automática de reportes
- [ ] Exportación a PDF
- [ ] Templates personalizables
- [ ] Resumen ejecutivo

### Cómo Contribuir

1. **Agregar nueva herramienta**:
   - Crear archivo en `src/tools/`
   - Usar decorador `@function_tool`
   - Registrar en `main.py`

2. **Mejorar interpretaciones**:
   - Editar `src/core/interpreter.py`
   - Agregar nuevos métodos `interpret_*`

3. **Personalizar mensajes**:
   - Modificar `src/ui/prompts.py`
   - Agregar explicaciones para usuarios

## 📚 Recursos Adicionales

- **README.md** - Documentación completa
- **docs/architecture.md** - Detalles técnicos
- **toolTest.py** - Versión original (referencia)

## ✨ Consejos Pro

1. **Usa confirmaciones sabiamente**: Las acciones sensibles siempre piden aprobación
2. **Revisa los logs**: Toda actividad queda registrada
3. **Explora herramientas**: Usa opción "2" del menú para ver todas
4. **Pide explicaciones**: El agente puede explicar conceptos técnicos
5. **Experimenta seguro**: Usa VM o entorno de pruebas

## 🎉 ¡Listo para Usar!

Tu agente está completamente configurado y listo para proteger tu red.

**Comando para empezar:**
```bash
python main.py
```

**Primer comando recomendado:**
```
"Muestra todas las herramientas disponibles"
```

