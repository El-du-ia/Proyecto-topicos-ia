# 🚀 Guía Rápida de Ejecución

## TL;DR - Comandos Esenciales

```bash
# Funcionalidad COMPLETA (captura de paquetes, escaneos stealth, logs del sistema)
sudo ./run_as_root.sh

# Funcionalidad BÁSICA (whois, DNS, nmap básico)
./run.sh
```

---

## ⚠️ Problema Común: ModuleNotFoundError con sudo

### ❌ INCORRECTO:
```bash
sudo python main.py
```
**Error:** `ModuleNotFoundError: No module named 'cai'`

**Por qué falla:**
- `sudo python` usa el Python del sistema (root)
- Las dependencias están en `cai_env_sexo/` (entorno virtual)
- Root no tiene acceso a ese entorno virtual

### ✅ CORRECTO:

#### Opción 1: Script wrapper (más fácil)
```bash
sudo ./run_as_root.sh
```

#### Opción 2: Ruta completa al Python del venv
```bash
sudo ./cai_env_sexo/bin/python main.py
```

#### Opción 3: Usar $(which python) después de activar
```bash
source cai_env_sexo/bin/activate
sudo $(which python) main.py
```

---

## 📊 Comparación de Métodos

| Método | ¿Funciona? | Facilidad | Notas |
|--------|-----------|-----------|-------|
| `sudo python main.py` | ❌ | Fácil | No encuentra dependencias |
| `sudo ./run_as_root.sh` | ✅ | Muy fácil | **RECOMENDADO** |
| `sudo ./cai_env_sexo/bin/python main.py` | ✅ | Medio | Funciona siempre |
| `sudo $(which python)` | ✅ | Medio | Requiere activar venv primero |
| `sudo -E python` | ⚠️ | Difícil | Puede tener problemas de seguridad |

---

## 🔍 Verificar que todo está bien

### 1. Verificar el entorno virtual
```bash
ls -la cai_env_sexo/bin/python
# Debe existir
```

### 2. Verificar dependencias instaladas
```bash
./cai_env_sexo/bin/python -c "import cai; print('CAI instalado')"
# Debe imprimir: CAI instalado
```

### 3. Probar sin sudo (modo limitado)
```bash
./run.sh
```

### 4. Probar con sudo (modo completo)
```bash
sudo ./run_as_root.sh
```

---

## 🛠️ Solución si aún falla

### Si `run_as_root.sh` no existe o no es ejecutable:
```bash
chmod +x run_as_root.sh run.sh
```

### Si el entorno virtual está corrupto:
```bash
# Recrear entorno virtual
rm -rf cai_env_sexo
python -m venv cai_env_sexo
source cai_env_sexo/bin/activate
pip install -r requirements.txt
```

### Si faltan dependencias del sistema:
```bash
sudo apt update
sudo apt install python3 python3-venv nmap whois
```

---

## 📚 Más Información

- **Documentación completa:** `README.md`
- **Solución de problemas:** `docs/TROUBLESHOOTING.md`
- **Sistema de permisos:** `docs/PERMISOS.md`
- **Demostración de permisos:** `python demo_permisos.py`

---

## 💡 Entendiendo el problema

```
┌─────────────────────────────────────────────────────────────┐
│  sudo python main.py                                        │
│    │                                                         │
│    └─→ Python del SISTEMA (/usr/bin/python)                │
│        └─→ NO tiene acceso a cai_env_sexo/                 │
│            └─→ ModuleNotFoundError: No module named 'cai'  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  sudo ./cai_env_sexo/bin/python main.py                     │
│    │                                                         │
│    └─→ Python del VENV (./cai_env_sexo/bin/python)         │
│        └─→ SÍ tiene todas las dependencias                 │
│            └─→ ✅ Funciona correctamente                    │
└─────────────────────────────────────────────────────────────┘
```

---

**Última actualización:** 2025-11-25
