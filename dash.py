#!/usr/bin/env python3
"""
dash.py - Interfaz CLI para Claude Code y para Dante desde la terminal.
Permite consultar tareas, referencias, ideas y marcar avances sin abrir el navegador.
"""
import argparse
import sys
from pathlib import Path

# Configurar encoding seguro para consola de Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Asegurar importación de core
sys.path.insert(0, str(Path(__file__).resolve().parent))
import core

PROYECTOS_MAP = {
    "dos_mentes": "Dos Mentes",
    "canal_neon": "Canal Neón",
    "primer_brote": "Primer Brote",
    "general": "General"
}

ESTILOS_COLOR = {
    "alta": "\033[91m",      # Rojo
    "media": "\033[93m",     # Amarillo
    "baja": "\033[92m",      # Verde
    "azul": "\033[94m",      # Azul
    "cyan": "\033[96m",      # Cyan
    "negrita": "\033[1m",
    "reset": "\033[0m"
}

def color(texto: str, estilo: str) -> str:
    c = ESTILOS_COLOR.get(estilo, "")
    r = ESTILOS_COLOR["reset"]
    return f"{c}{texto}{r}" if sys.stdout.isatty() else texto

def cmd_resumen(args):
    items = core.obtener_db()
    pendientes = [i for i in items if i.get("type") == "directiva_claude" and i.get("status") in ("pendiente", "en_proceso")]
    referencias = [i for i in items if i.get("type") == "referencia" and i.get("status") != "listo"]
    ideas = [i for i in items if i.get("type") == "idea" and i.get("status") != "listo"]
    avances = [i for i in items if i.get("status") == "listo"]

    print("\n" + "=" * 65)
    print(color(" 🚀 DASHBOARD DE DANTE — VISTA RÁPIDA PARA CLAUDE CODE", "cyan"))
    print("=" * 65)
    print(f" • Tareas para Claude pendientes: {color(str(len(pendientes)), 'alta')}")
    print(f" • Referencias/Videos a analizar: {color(str(len(referencias)), 'azul')}")
    print(f" • Ideas de contenido / guiones: {color(str(len(ideas)), 'media')}")
    print(f" • Tareas listas / completadas:  {color(str(len(avances)), 'baja')}")
    print("-" * 65)

    if pendientes:
        print(color("\n[⚡ TAREAS ACTIVAS PARA CLAUDE]:", "negrita"))
        for it in pendientes:
            prio = color(it.get("priority", "").upper(), it.get("priority", "media"))
            proj = PROYECTOS_MAP.get(it.get("project"), it.get("project"))
            print(f"  • {color(it['id'], 'negrita')} [{proj}] ({prio}): {it['title']}")
            if it.get("notes"):
                primera_linea = it["notes"].splitlines()[0]
                print(f"    ↳ {primera_linea[:80]}{'...' if len(primera_linea) > 80 else ''}")

    if referencias:
        print(color("\n[🎥 REFERENCIAS / LINKS RECIENTES]:", "negrita"))
        for it in referencias[:3]:
            proj = PROYECTOS_MAP.get(it.get("project"), it.get("project"))
            print(f"  • {color(it['id'], 'azul')} [{proj}]: {it['title']}")
            if it.get("url"):
                print(f"    URL: {it['url']}")

    print("\n" + "-" * 65)
    print("Comandos útiles:")
    print("  python dash.py ver <ID>            -> Ver detalle completo de una tarea o link")
    print("  python dash.py estado <ID> listo   -> Marcar tarea como completada")
    print("  python dash.py agregar             -> Añadir nuevo avance, idea o directiva")
    print("  python dash.py md                  -> Ver todo el contenido de CLAUDE_INBOX.md")
    print("=" * 65 + "\n")

def cmd_ver(args):
    items = core.obtener_db()
    encontrado = next((i for i in items if i["id"].upper() == args.id.upper()), None)
    if not encontrado:
        print(color(f"\n❌ Error: No se encontró el item con ID '{args.id}'\n", "alta"))
        return

    print("\n" + "=" * 60)
    print(f"  ID:          {color(encontrado['id'], 'negrita')}")
    print(f"  Tipo:        {encontrado.get('type')}")
    print(f"  Proyecto:    {PROYECTOS_MAP.get(encontrado.get('project'), encontrado.get('project'))}")
    print(f"  Título:      {color(encontrado.get('title'), 'cyan')}")
    print(f"  Estado:      {color(encontrado.get('status'), 'media')}")
    print(f"  Prioridad:   {color(encontrado.get('priority'), encontrado.get('priority', 'media'))}")
    if encontrado.get("url"):
        print(f"  URL:         {encontrado.get('url')}")
    if encontrado.get("tags"):
        print(f"  Tags:        {', '.join('#' + t for t in encontrado['tags'])}")
    print(f"  Actualizado: {encontrado.get('updated_at', '')[:19]}")
    print("-" * 60)
    print("  Notas / Instrucciones:")
    print(f"  {encontrado.get('notes', 'Sin notas.')}")
    print("=" * 60 + "\n")

def cmd_estado(args):
    nuevo_estado = args.nuevo_estado.lower()
    estados_validos = ["pendiente", "en_proceso", "revisar", "listo"]
    if nuevo_estado not in estados_validos:
        print(color(f"❌ Estado inválido. Opciones: {', '.join(estados_validos)}", "alta"))
        return

    updates = {"status": nuevo_estado}
    if args.nota:
        # Añadir al historial de notas
        items = core.obtener_db()
        item = next((i for i in items if i["id"].upper() == args.id.upper()), None)
        if item:
            nota_actual = item.get("notes", "")
            agregado = f"\n\n[Nota de Claude Code ({nuevo_estado})]: {args.nota}"
            updates["notes"] = nota_actual + agregado

    actualizado = core.actualizar_item(args.id.upper(), updates)
    if actualizado:
        print(color(f"\n✅ Item {actualizado['id']} actualizado a estado '{nuevo_estado}' con éxito.", "baja"))
        print(f"Sincronizado con CLAUDE_INBOX.md y el Dashboard web.\n")
    else:
        print(color(f"\n❌ Error: No se encontró el item {args.id}\n", "alta"))

def cmd_agregar(args):
    item = {
        "type": args.tipo,
        "project": args.proyecto,
        "title": args.titulo,
        "url": args.url or "",
        "notes": args.nota or "",
        "priority": args.prioridad,
        "status": "pendiente",
        "tags": [t.strip() for t in args.tags.split(",")] if args.tags else []
    }
    creado = core.agregar_item(item)
    print(color(f"\n✅ Creado correctamente con ID: {creado['id']}", "baja"))
    print(f"Título: {creado['title']}")
    print(f"Sincronizado con CLAUDE_INBOX.md\n")

def cmd_md(args):
    items = core.obtener_db()
    core.generar_markdowns(items)
    if core.INBOX_MD_PATH.exists():
        with open(core.INBOX_MD_PATH, "r", encoding="utf-8") as f:
            print(f.read())

def cmd_json(args):
    items = core.obtener_db()
    import json
    print(json.dumps(items, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="CLI para interactuar con el Dashboard de Dante")
    subparsers = parser.add_subparsers(dest="comando")

    # Resumen / default
    subparsers.add_parser("resumen", help="Ver resumen de tareas y referencias")
    subparsers.add_parser("inbox", help="Ver resumen de tareas pendientes")

    # Ver detalle
    p_ver = subparsers.add_parser("ver", help="Ver detalle de un item")
    p_ver.add_argument("id", help="ID del item (ej: DIR-001, REF-001)")

    # Cambiar estado
    p_estado = subparsers.add_parser("estado", help="Actualizar estado de un item")
    p_estado.add_argument("id", help="ID del item")
    p_estado.add_argument("nuevo_estado", choices=["pendiente", "en_proceso", "revisar", "listo"], help="Nuevo estado")
    p_estado.add_argument("--nota", help="Nota opcional que agrega Claude al cambiar el estado")

    # Agregar item
    p_add = subparsers.add_parser("agregar", help="Agregar un nuevo elemento")
    p_add.add_argument("--tipo", choices=["directiva_claude", "referencia", "idea", "avance"], default="directiva_claude")
    p_add.add_argument("--proyecto", choices=["dos_mentes", "canal_neon", "primer_brote", "general"], default="dos_mentes")
    p_add.add_argument("--titulo", required=True, help="Título del item")
    p_add.add_argument("--url", default="", help="Link de video o web")
    p_add.add_argument("--nota", default="", help="Descripción detallada o consigna")
    p_add.add_argument("--prioridad", choices=["alta", "media", "baja"], default="media")
    p_add.add_argument("--tags", default="", help="Tags separados por coma")

    # Exportar / Ver md
    subparsers.add_parser("md", help="Ver contenido de CLAUDE_INBOX.md")
    subparsers.add_parser("json", help="Exportar base en JSON")

    args = parser.parse_args()

    if not args.comando or args.comando in ("resumen", "inbox"):
        cmd_resumen(args)
    elif args.comando == "ver":
        cmd_ver(args)
    elif args.comando == "estado":
        cmd_estado(args)
    elif args.comando == "agregar":
        cmd_agregar(args)
    elif args.comando == "md":
        cmd_md(args)
    elif args.comando == "json":
        cmd_json(args)

if __name__ == "__main__":
    main()
