# 🔒 Sistema de Permisos del Agente de Ciberseguridad

## 📋 Índice

1. [¿Por qué se necesitan permisos especiales?](#por-qué-se-necesitan-permisos-especiales)
2. [Herramientas que requieren sudo](#herramientas-que-requieren-sudo)
3. [Herramientas que NO requieren sudo](#herramientas-que-no-requieren-sudo)
4. [Cómo ejecutar el agente](#cómo-ejecutar-el-agente)
5. [Alternativas sin sudo](#alternativas-sin-sudo)
6. [Explicación técnica](#explicación-técnica)

---

## ¿Por qué se necesitan permisos especiales?

El agente de ciberseguridad realiza operaciones que requieren acceso privilegiado al sistema operativo. Esto **NO es un bug**, es un requisito de seguridad del kernel de Linux.

### 🔐 Principio de seguridad

Linux protege ciertos recursos del sistema para evitar:
- Que cualquier programa pueda interceptar el tráfico de red
- Que aplicaciones maliciosas capturen datos sensibles
- Que usuarios sin privilegios accedan a logs del sistema

---

## Herramientas que requieren sudo

### 1. 📡 Captura de Paquetes de Red (`network_sniffer`)

**¿Por qué necesita sudo?**
- Requiere crear "raw sockets" (sockets en modo promiscuo)
- Necesita la capacidad `CAP_NET_RAW` del kernel
- Sin esto, el sistema operativo bloqueará el acceso a la interfaz de red

**Ejemplo de uso:**
```bash
# ✅ Correcto
sudo python main.py

# ❌ Sin sudo dará error
python main.py
```

**Cómo funciona internamente:**
```python
# Scapy intenta crear un socket RAW
socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
# Sin privilegios → PermissionError
```

**Alternativa sin sudo:**
- Agregar tu usuario al grupo `pcap`
- Darle capacidades específicas al ejecutable de Python:
  ```bash
  sudo setcap cap_net_raw=eip /usr/bin/python3
  ```
  ⚠️ Esto puede ser un riesgo de seguridad

---

### 2. 🔍 Escaneo Nmap Stealth (`nmap_scan` con tipo `stealth`)

**¿Por qué necesita sudo?**
- Los escaneos SYN (stealth) envían paquetes TCP sin completar el handshake
- Requiere manipular paquetes TCP a bajo nivel
- Usa raw sockets al igual que la captura de paquetes

**Ejemplo:**
```bash
# ✅ Escaneo stealth con sudo
sudo python main.py
# En el agente: "haz un escaneo stealth de 192.168.1.1"

# ✅ Escaneo básico SIN sudo (funciona)
python main.py
# En el agente: "haz un escaneo básico de 192.168.1.1"
```

**Tipos de escaneo:**
| Tipo | Requiere sudo | Descripción |
|------|--------------|-------------|
| `basic` | ❌ No | Escaneo normal de puertos |
| `full` | ❌ No | Escaneo completo de todos los puertos |
| `stealth` | ✅ Sí | Escaneo SYN sigiloso |
| `service` | ❌ No | Detección de versiones |

---

### 3. 📄 Análisis de Logs del Sistema (`analyze_log`, `tail_log`)

**¿Por qué necesita sudo?**
- Los archivos en `/var/log/` tienen permisos restrictivos
- Solo root y ciertos grupos pueden leerlos
- Protege información sensible del sistema

**Ejemplos:**

```bash
# ❌ Sin sudo (error)
python main.py
# "analiza el log /var/log/auth.log"
# → Error: Permiso denegado

# ✅ Con sudo (funciona)
sudo python main.py
# "analiza el log /var/log/auth.log"
# → Análisis exitoso

# ✅ Logs de usuario (NO requiere sudo)
python main.py
# "analiza el log /tmp/mi_app.log"
# → Funciona sin problemas
```

**Permisos típicos de logs:**
```bash
$ ls -la /var/log/
-rw-r----- 1 root adm  auth.log     # Solo root y grupo adm
-rw-r----- 1 root adm  syslog       # Solo root y grupo adm
-rw-r--r-- 1 root root wtmp         # Todos pueden leer
```

**Alternativa sin sudo:**
- Agregar tu usuario al grupo `adm`:
  ```bash
  sudo usermod -a -G adm $USER
  newgrp adm  # Activar el grupo
  ```

---

## Herramientas que NO requieren sudo

Estas herramientas funcionan perfectamente **sin privilegios especiales**:

### ✅ 1. Whois Lookup (`whois_lookup`)
```bash
python main.py
# "haz un whois de google.com"
```
Usa comandos de red estándar que no requieren permisos especiales.

### ✅ 2. DNS Lookup (`dns_lookup`, `reverse_dns_lookup`)
```bash
python main.py
# "busca la IP de google.com"
# "busca el dominio de 8.8.8.8"
```
Usa la biblioteca `socket` de Python en modo cliente.

### ✅ 3. Nmap básico (`nmap_scan` con tipos `basic`, `full`, `service`)
```bash
python main.py
# "escanea los puertos de 192.168.1.1"
```
Los escaneos TCP normales no requieren raw sockets.

---

## Cómo ejecutar el agente

### Opción 1: Con privilegios completos (recomendado)
```bash
sudo python main.py
```
✅ Todas las herramientas disponibles
✅ Captura de paquetes
✅ Escaneos stealth
✅ Lectura de logs del sistema

### Opción 2: Sin sudo (funcionalidad limitada)
```bash
python main.py
```
✅ Whois y DNS
✅ Escaneos nmap básicos
✅ Análisis de logs de usuario
❌ Captura de paquetes
❌ Escaneos stealth
❌ Logs del sistema

### Opción 3: Permisos granulares (avanzado)
```bash
# Agregar usuario a grupos necesarios
sudo usermod -a -G wireshark,adm $USER

# Dar capacidades específicas
sudo setcap cap_net_raw=eip $(which python3)
```
⚠️ Puede ser riesgo de seguridad - úsalo con cuidado

---

## Alternativas sin sudo

### 1. Usar tcpdump en lugar de Scapy
```bash
# tcpdump ya tiene permisos setcap por defecto en muchas distros
tcpdump -i eth0 -c 10 -w captura.pcap
```

### 2. Usar tshark (Wireshark CLI)
```bash
sudo apt install tshark
# Durante instalación, permite a usuarios sin privilegios capturar
tshark -i eth0 -c 10
```

### 3. Leer logs copiados
```bash
# Copia logs del sistema a tu directorio
sudo cp /var/log/syslog /tmp/syslog
sudo chown $USER /tmp/syslog

# Ahora el agente puede leerlos sin sudo
python main.py
# "analiza el log /tmp/syslog"
```

---

## Explicación técnica

### Capacidades de Linux (Capabilities)

Linux divide los privilegios de root en "capacidades" individuales:

| Capacidad | Descripción | Herramientas |
|-----------|-------------|--------------|
| `CAP_NET_RAW` | Crear raw sockets | Scapy, nmap stealth |
| `CAP_NET_ADMIN` | Configurar interfaces | No usado |
| `CAP_DAC_READ_SEARCH` | Leer cualquier archivo | Análisis de logs |

**Ver capacidades de un proceso:**
```bash
getpcaps $$
```

**Ver capacidades de un archivo:**
```bash
getcap /usr/bin/tcpdump
# /usr/bin/tcpdump cap_net_raw=eip
```

### Raw Sockets

Un "raw socket" permite:
- Construir paquetes desde cero
- Interceptar todo el tráfico de red
- Enviar paquetes sin pasar por el stack TCP/IP

**Creación de raw socket:**
```python
import socket

# Requiere CAP_NET_RAW
s = socket.socket(
    socket.AF_PACKET,      # Capa 2 (Ethernet)
    socket.SOCK_RAW,       # Modo raw
    socket.htons(0x0003)   # Todos los protocolos
)
```

Sin privilegios:
```
PermissionError: [Errno 1] Operation not permitted
```

### Permisos de archivos

```bash
# Ver permisos de logs
$ ls -la /var/log/auth.log
-rw-r----- 1 root adm 123456 Jan 1 12:00 auth.log
# │││ │ │
# │││ │ └─ Grupo: adm (lectura)
# │││ └─── Dueño: root (lectura/escritura)
# ││└───── Otros: sin acceso
# │└────── Permisos: rw-r-----
# └─────── Tipo: archivo regular
```

---

## Verificación del sistema

El agente incluye un script de demostración:

```bash
# Ver estado de permisos
python demo_permisos.py

# El script mostrará:
# - Si estás ejecutando como root
# - Qué herramientas están disponibles
# - Explicaciones detalladas
# - Sugerencias específicas
```

---

## Preguntas frecuentes

### ❓ ¿Es seguro usar sudo con el agente?
✅ Sí, el código es open source y puedes revisarlo. El agente:
- Pide confirmación antes de ejecutar acciones sensibles
- No hace conexiones externas no autorizadas
- No modifica archivos del sistema sin avisar

### ❓ ¿Puedo usar el agente sin ningún privilegio?
✅ Sí, muchas funciones funcionan sin sudo:
- Whois y DNS lookup
- Escaneos nmap básicos
- Análisis de tus propios logs

### ❓ ¿Por qué otros sniffers como Wireshark funcionan sin sudo?
Wireshark usa un truco: instala `dumpcap` con permisos setcap y separa la captura de la interfaz gráfica. Puedes hacer lo mismo con Python:

```bash
sudo setcap cap_net_raw=eip /usr/bin/python3
```

Pero esto da permisos de captura a **todos** los scripts Python del sistema.

### ❓ ¿Hay alguna alternativa más segura?
Sí, el patrón recomendado es:
1. Crear un script wrapper que capture paquetes (con permisos elevados)
2. El agente ejecuta ese script y lee los resultados
3. Separación de privilegios: solo una pequeña parte tiene sudo

---

## Recursos adicionales

- [Linux Capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html)
- [Scapy Security](https://scapy.readthedocs.io/en/latest/usage.html#interactive-tutorial)
- [Nmap Privileges](https://nmap.org/book/man-port-scanning-techniques.html)
- [Understanding Linux File Permissions](https://www.redhat.com/sysadmin/linux-file-permissions-explained)

---

## Resumen visual

```
┌─────────────────────────────────────────────────────────────┐
│              AGENTE DE CIBERSEGURIDAD                       │
│                                                             │
│  SIN SUDO           │  CON SUDO                             │
│  ─────────────────  │  ─────────────────────────            │
│  ✓ Whois            │  ✓ TODO lo de la izquierda           │
│  ✓ DNS              │  ✓ Captura de paquetes               │
│  ✓ Nmap básico      │  ✓ Escaneos stealth                  │
│  ✓ Logs propios     │  ✓ Logs del sistema                  │
│                     │                                       │
│  ✗ Captura red      │  sudo python main.py                 │
│  ✗ Nmap stealth     │                                       │
│  ✗ Logs /var/log    │                                       │
│                     │                                       │
│  python main.py     │                                       │
└─────────────────────────────────────────────────────────────┘
```

---

**Última actualización:** 2024-01-24  
**Versión del documento:** 1.0
