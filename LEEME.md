# Dante Hub — Dashboard de Investigación & Puente Claude Code

Este proyecto es tu centro de comando visual y puente de comunicación directo para **Claude Code**.
Vive en una carpeta 100% independiente para no tocar ni alterar tu carpeta de trabajo `editor clau`.

---

## 🚀 Cómo se usa

### 1. Para vos (Dante) desde el navegador
- Hacé doble clic en **`INICIAR_DASHBOARD.bat`** (o corré `python server.py`).
- Se abre automáticamente en tu navegador: **`http://localhost:5050`**.
- Podés:
  - **Pegar links de YouTube / Instagram / TikTok:** detecta la miniatura automáticamente.
  - **Cargar directivas y tareas para Claude:** "Ajustar cámara en segundo 5", "Hacer fundido en el video 08", etc.
  - **Guardar ideas de guiones y temas** clasificados por proyecto (*Dos Mentes*, *Canal Neón*, *Primer Brote*, *General*).
  - **Marcar avances con un solo clic.**

---

### 2. Para Claude Code desde la Terminal (CLI)
Cada vez que guardás o modificás algo en el dashboard, se regenera al instante el archivo:
📄 **`CLAUDE_INBOX.md`**

Claude Code puede leer ese archivo o ejecutar los comandos CLI con `dash.py`:

```bash
# Ver el resumen de todo lo que Dante dejó pendiente
python dash.py

# Ver el detalle de una tarea o link específico (con notas completas)
python dash.py ver DIR-001

# Cambiar de estado una tarea cuando Claude termine el render o el guion
python dash.py estado DIR-001 listo --nota "Render completado a 1080p con fundido de 1s"

# Agregar una nueva idea o avance desde la terminal
python dash.py agregar --tipo avance --proyecto dos_mentes --titulo "Video 08 finalizado"
```

---

## 📁 Estructura del proyecto
- `server.py`: Servidor HTTP nativo de Python (corre en 0.1s, sin dependencias pesadas).
- `core.py`: Gestor de base de datos JSON y generador automático de Markdown.
- `dash.py`: Herramienta CLI para Claude Code.
- `data/db.json`: Base de datos de registros.
- `public/index.html`: Dashboard web moderno en modo oscuro con Tailwind CSS.
- `CLAUDE_INBOX.md`: Archivo Markdown estructurado para lectura directa de IAs.
- `INICIAR_DASHBOARD.bat`: Acceso directo para levantar todo con un clic.
