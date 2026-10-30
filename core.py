#!/usr/bin/env python3
"""
core.py - Núcleo de datos y sincronización para el Dashboard de Dante.
Maneja la base de datos JSON y la exportación automática a CLAUDE_INBOX.md.
"""
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "db.json"
INBOX_MD_PATH = BASE_DIR / "CLAUDE_INBOX.md"
RESUMEN_MD_PATH = BASE_DIR / "PROYECTOS_ESTADO.md"

_lock = Lock()

def extraer_youtube_id(url: str) -> str:
    """Extrae el ID de un video o short de YouTube."""
    if not url:
        return ""
    patrones = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"shorts\/([0-9A-Za-z_-]{11})"
    ]
    for p in patrones:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return ""

def datos_iniciales():
    """Datos semilla basados en el trabajo real de Dante."""
    now = datetime.now().isoformat()
    return [
        {
            "id": "DIR-001",
            "type": "directiva_claude",
            "project": "dos_mentes",
            "title": "Ajustar final del Video 08 (Batería social)",
            "url": "https://www.youtube.com/watch?v=example",
            "notes": "En la referencia original hay un fundido suave al final que empalma con el inicio para bucle infinito. El nuestro corta seco a los 10.5s. Ajustar curva de opacidad en escena.py de Blender.",
            "status": "pendiente",
            "priority": "alta",
            "created_at": now,
            "updated_at": now,
            "tags": ["blender", "bucle", "render-nube"]
        },
        {
            "id": "REF-001",
            "type": "referencia",
            "project": "dos_mentes",
            "title": "Referencia @neuronvisuals: Ritmo de cámara y glow",
            "url": "https://www.instagram.com/p/example_neuron/",
            "notes": "Fijarse cómo la cámara rota 15 grados en el eje Z cuando aparece el segundo personaje y el desenfoque de profundidad (DoF) en f/2.8 enfocado solo en el pecho del protagonista.",
            "status": "en_proceso",
            "priority": "alta",
            "created_at": now,
            "updated_at": now,
            "tags": ["camara", "dof", "estilo"]
        },
        {
            "id": "IDEA-001",
            "type": "idea",
            "project": "canal_neon",
            "title": "Video 11: Grooming y prevención digital",
            "url": "",
            "notes": "Tono serio y preventivo, sin morbo. Explicar el método del espejo (cómo operan perfiles falsos) y cómo detectar patrones con 3 señales claras. Voz Kore o Enzo.",
            "status": "pendiente",
            "priority": "media",
            "created_at": now,
            "updated_at": now,
            "tags": ["guion", "serio", "signo"]
        },
        {
            "id": "AVAN-001",
            "type": "avance",
            "project": "dos_mentes",
            "title": "Video 05 (Plata prestada) animado completo",
            "url": "",
            "notes": "36 segundos listos en Blender (los 7 momentos animados, pantalla dividida, puesto y choque de puño). Preview generado y revisado sin manos rotas.",
            "status": "listo",
            "priority": "media",
            "created_at": now,
            "updated_at": now,
            "tags": ["blender", "animacion", "36s"]
        },
        {
            "id": "DIR-002",
            "type": "directiva_claude",
            "project": "primer_brote",
            "title": "Configurar producto extra (Microverdes $5.990) en Shopify",
            "url": "https://admin.shopify.com/store/p0ex2r-iy/products",
            "notes": "Falta vincular el bump de compra para microverdes y verificar que el script order_bump.py no rompa el flujo de checkout.",
            "status": "pendiente",
            "priority": "media",
            "created_at": now,
            "updated_at": now,
            "tags": ["shopify", "upsell", "meta-ads"]
        }
    ]

def obtener_db():
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not DB_PATH.exists():
            items = datos_iniciales()
            guardar_db_internal(items)
            return items
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

def guardar_db_internal(items):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = DB_PATH.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    os.rename(tmp_path, DB_PATH)
    generar_markdowns(items)

def guardar_db(items):
    with _lock:
        guardar_db_internal(items)

def nuevo_id(tipo: str, items) -> str:
    prefijos = {
        "directiva_claude": "DIR",
        "referencia": "REF",
        "idea": "IDEA",
        "avance": "AVAN"
    }
    p = prefijos.get(tipo, "ITEM")
    num = 1
    for it in items:
        if it.get("id", "").startswith(p + "-"):
            try:
                val = int(it["id"].split("-")[1])
                if val >= num:
                    num = val + 1
            except Exception:
                pass
    return f"{p}-{num:03d}"

def agregar_item(item_dict: dict) -> dict:
    items = obtener_db()
    tipo = item_dict.get("type", "directiva_claude")
    if not item_dict.get("id"):
        item_dict["id"] = nuevo_id(tipo, items)
    now = datetime.now().isoformat()
    item_dict["created_at"] = now
    item_dict["updated_at"] = now
    if not item_dict.get("status"):
        item_dict["status"] = "pendiente"
    if not item_dict.get("priority"):
        item_dict["priority"] = "media"
    if not item_dict.get("tags"):
        item_dict["tags"] = []
    
    # Auto-detectar Youtube ID
    yt_id = extraer_youtube_id(item_dict.get("url", ""))
    if yt_id:
        if "metadata" not in item_dict:
            item_dict["metadata"] = {}
        item_dict["metadata"]["youtube_id"] = yt_id

    items.insert(0, item_dict)
    guardar_db(items)
    return item_dict

def actualizar_item(item_id: str, updates: dict) -> dict:
    items = obtener_db()
    actualizado = None
    for it in items:
        if it["id"] == item_id:
            for k, v in updates.items():
                if k not in ("id", "created_at"):
                    it[k] = v
            it["updated_at"] = datetime.now().isoformat()
            if "url" in updates:
                yt_id = extraer_youtube_id(updates["url"])
                if yt_id:
                    if "metadata" not in it:
                        it["metadata"] = {}
                    it["metadata"]["youtube_id"] = yt_id
            actualizado = it
            break
    if actualizado:
        guardar_db(items)
    return actualizado

def eliminar_item(item_id: str) -> bool:
    items = obtener_db()
    nuevos = [it for it in items if it["id"] != item_id]
    if len(nuevos) != len(items):
        guardar_db(nuevos)
        return True
    return False

def generar_markdowns(items):
    """Genera CLAUDE_INBOX.md para que Claude Code lo lea directamente por CLI."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Separar por tipo y estado
    directivas_pendientes = [it for it in items if it.get("type") == "directiva_claude" and it.get("status") in ("pendiente", "en_proceso")]
    referencias = [it for it in items if it.get("type") == "referencia" and it.get("status") != "listo"]
    ideas = [it for it in items if it.get("type") == "idea" and it.get("status") != "listo"]
    avances_recientes = [it for it in items if it.get("status") == "listo"][:5]

    proyectos_nombres = {
        "dos_mentes": "Dos Mentes (@dosmentes.3d)",
        "canal_neon": "Canal Neón (Motion explicativo)",
        "primer_brote": "Primer Brote (Kit huerta)",
        "general": "General / Nuevas ideas"
    }

    iconos_prioridad = {
        "alta": "[ALTA]",
        "media": "[MEDIA]",
        "baja": "[BAJA]"
    }

    md = []
    md.append(f"# INBOX DE DANTE PARA CLAUDE CODE")
    md.append(f"> Actualizado automáticamente el {now_str} desde el Dashboard de Dante.")
    md.append(f"> **Uso desde Claude Code CLI:** `python dash.py` para ver el menú rápido, o `python dash.py estado <ID> listo --nota '...'` al resolver algo.\n")

    # Sección 1: DIRECTIVAS URGENTES / TAREAS DIRECTAS
    md.append(f"## 1. Tareas y Directivas para Claude ({len(directivas_pendientes)} activas)")
    if not directivas_pendientes:
        md.append("_No hay directivas pendientes en este momento._\n")
    else:
        for it in directivas_pendientes:
            proj = proyectos_nombres.get(it.get("project"), it.get("project"))
            prio = iconos_prioridad.get(it.get("priority"), "[MEDIA]")
            st = it.get("status", "pendiente").upper()
            md.append(f"### `[{it['id']}]` {it['title']} — `{st}` | Prioridad: {prio}")
            md.append(f"- **Proyecto:** {proj}")
            if it.get("url"):
                md.append(f"- **Link / Recurso:** {it['url']}")
            if it.get("tags"):
                md.append(f"- **Tags:** {', '.join('#' + t for t in it['tags'])}")
            md.append(f"- **Instrucciones de Dante:**\n  {it.get('notes', 'Sin notas adicionales.')}\n")

    # Sección 2: REFERENCIAS Y VIDEOS A ANALIZAR
    md.append(f"## 2. Referencias y Links para Analizar / Replicar ({len(referencias)})")
    if not referencias:
        md.append("_No hay referencias pendientes de análisis._\n")
    else:
        for it in referencias:
            proj = proyectos_nombres.get(it.get("project"), it.get("project"))
            md.append(f"- **`[{it['id']}]` {it['title']}** ({proj})")
            md.append(f"  - **URL:** {it.get('url', 'Sin URL')}")
            md.append(f"  - **Qué mirar / replicar:** {it.get('notes', 'Ver referencia completa')}")
            md.append(f"  - **Estado:** `{it.get('status')}`\n")

    # Sección 3: IDEAS DE CONTENIDO Y GUIONES
    md.append(f"## 3. Banco de Ideas y Guiones Nuevos ({len(ideas)})")
    if not ideas:
        md.append("_No hay ideas pendientes._\n")
    else:
        for it in ideas:
            proj = proyectos_nombres.get(it.get("project"), it.get("project"))
            md.append(f"- **`[{it['id']}]` {it['title']}** ({proj})")
            if it.get("notes"):
                md.append(f"  - {it['notes']}")
        md.append("")

    # Sección 4: ÚLTIMOS AVANCES Y COMPLETADOS
    md.append(f"## 4. Últimos Avances y Tareas Listas")
    if not avances_recientes:
        md.append("_Aún no se marcaron tareas como completadas._\n")
    else:
        for it in avances_recientes:
            proj = proyectos_nombres.get(it.get("project"), it.get("project"))
            md.append(f"- **`[{it['id']}]` {it['title']}** ({proj}) — Completado el {it.get('updated_at', '')[:10]}")
            if it.get("notes"):
                md.append(f"  _{it['notes']}_\n")

    md_content = "\n".join(md)
    with open(INBOX_MD_PATH, "w", encoding="utf-8") as f:
        f.write(md_content)
