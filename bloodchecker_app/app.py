from flask import Flask, render_template, jsonify, request, send_file
import json, os, datetime, csv, io, mimetypes, base64, tempfile

app = Flask(__name__)
SAVE_FILE = os.path.join(os.path.expanduser("~"), "saves.json")
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "image")

CELL_TYPES = [
    {"id": "seg",        "label": "SEG",        "normal_min": 50, "normal_max": 70,  "color": "#4f8ef7"},
    {"id": "band",       "label": "BAND",       "normal_min": 0,  "normal_max": 5,   "color": "#a78bfa"},
    {"id": "lymph",      "label": "LYMPH",      "normal_min": 20, "normal_max": 40,  "color": "#34d399"},
    {"id": "mono",       "label": "MONO",       "normal_min": 2,  "normal_max": 8,   "color": "#fb923c"},
    {"id": "eos",        "label": "EOS",        "normal_min": 1,  "normal_max": 4,   "color": "#f472b6"},
    {"id": "baso",       "label": "BASO",       "normal_min": 0,  "normal_max": 1,   "color": "#22d3ee"},
    {"id": "blast",      "label": "BLAST",      "normal_min": 0,  "normal_max": 0,   "color": "#f87171"},
    {"id": "nrbc",       "label": "NRBC",       "normal_min": 0,  "normal_max": 0,   "color": "#fbbf24"},
    {"id": "myelo",      "label": "MYELO",      "normal_min": 0,  "normal_max": 0,   "color": "#86efac"},
    {"id": "meta",       "label": "META",       "normal_min": 0,  "normal_max": 0,   "color": "#c084fc"},
    {"id": "atyp_lymph", "label": "ATYP LYMPH", "normal_min": 0,  "normal_max": 0,   "color": "#67e8f9"},
    {"id": "other",      "label": "OTHER",      "normal_min": 0,  "normal_max": 0,   "color": "#94a3b8"},
]

def find_cell_image(cell_id):
    if not os.path.isdir(IMAGE_DIR):
        return None
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        fname = cell_id + ext
        if os.path.exists(os.path.join(IMAGE_DIR, fname)):
            return fname
    try:
        for f in os.listdir(IMAGE_DIR):
            name, ext = os.path.splitext(f)
            if name.lower() == cell_id.lower() and ext.lower() in (".jpg",".jpeg",".png",".webp"):
                return f
    except Exception:
        pass
    return None

def load_saves():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE) as f: return json.load(f)
    return []

def write_saves(data):
    with open(SAVE_FILE, "w") as f: json.dump(data, f, indent=2)

@app.route("/")
def index():
    cells_with_images = []
    for c in CELL_TYPES:
        cell = dict(c)
        cell["image"] = find_cell_image(c["id"])
        cells_with_images.append(cell)
    return render_template("index.html", cell_types=cells_with_images)

@app.route("/image/<path:filename>")
def serve_image(filename):
    safe_name = os.path.basename(filename)
    filepath  = os.path.join(IMAGE_DIR, safe_name)
    if not os.path.isfile(filepath):
        return ("Not found", 404)
    mime = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
    return send_file(filepath, mimetype=mime)

@app.route("/api/cells")
def get_cells():
    return jsonify(CELL_TYPES)

@app.route("/api/save", methods=["POST"])
def save_count():
    data  = request.json
    saves = load_saves()
    entry = {
        "id":        len(saves) + 1,
        "timestamp": datetime.datetime.now().isoformat(),
        "patient":   data.get("patient", ""),
        "counts":    data.get("counts", {}),
        "total":     data.get("total", 0),
        "limit":     data.get("limit", 100),
        "notes":     data.get("notes", ""),
    }
    saves.append(entry)
    write_saves(saves)
    return jsonify({"ok": True, "id": entry["id"]})

@app.route("/api/saves")
def get_saves():
    return jsonify(load_saves())

@app.route("/api/saves/<int:save_id>", methods=["DELETE"])
def delete_save(save_id):
    saves = [s for s in load_saves() if s["id"] != save_id]
    write_saves(saves)
    return jsonify({"ok": True})

@app.route("/api/export/csv")
def export_csv():
    saves  = load_saves()
    output = io.StringIO()
    writer = csv.writer(output)
    header = ["ID","Timestamp","Patient","Total","Limit","Notes"] + [c["label"] for c in CELL_TYPES]
    writer.writerow(header)
    for s in saves:
        row = [s["id"],s["timestamp"],s["patient"],s["total"],s["limit"],s["notes"]]
        row += [s["counts"].get(c["id"],0) for c in CELL_TYPES]
        writer.writerow(row)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype="text/csv",
                     as_attachment=True, download_name="abc_cell_export.csv")

@app.route("/api/export/pdf", methods=["POST"])
def export_pdf():
    """Generate a PDF report for the current count session."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        data    = request.json or {}
        patient = data.get("patient", "—")
        notes   = data.get("notes", "")
        counts  = data.get("counts", {})
        total   = data.get("total", 0)
        limit   = data.get("limit", 100)
        ts      = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M")

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=18*mm, rightMargin=18*mm,
                                topMargin=18*mm, bottomMargin=18*mm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("title", parent=styles["Normal"],
                                     fontSize=18, fontName="Helvetica-Bold",
                                     textColor=colors.HexColor("#3b82f6"),
                                     alignment=TA_CENTER, spaceAfter=2)
        sub_style   = ParagraphStyle("sub", parent=styles["Normal"],
                                     fontSize=9, textColor=colors.HexColor("#7d8590"),
                                     alignment=TA_CENTER, spaceAfter=10)
        label_style = ParagraphStyle("label", parent=styles["Normal"],
                                     fontSize=9, textColor=colors.HexColor("#7d8590"))
        value_style = ParagraphStyle("value", parent=styles["Normal"],
                                     fontSize=11, fontName="Helvetica-Bold")

        story = []

        # Header
        story.append(Paragraph("🔬 ABC Cell Counter", title_style))
        story.append(Paragraph("Hematology Differential Report", sub_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1c2130")))
        story.append(Spacer(1, 8))

        # Meta info table
        meta_data = [
            ["Patient", patient,  "Date / Time", ts],
            ["Total Counted", str(total), "Target Limit", str(limit)],
        ]
        if notes:
            meta_data.append(["Notes", notes, "", ""])

        meta_table = Table(meta_data, colWidths=[35*mm, 65*mm, 35*mm, 42*mm])
        meta_table.setStyle(TableStyle([
            ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE",  (0,0), (-1,-1), 9),
            ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#7d8590")),
            ("TEXTCOLOR", (2,0), (2,-1), colors.HexColor("#7d8590")),
            ("TEXTCOLOR", (1,0), (1,-1), colors.HexColor("#e6edf3")),
            ("TEXTCOLOR", (3,0), (3,-1), colors.HexColor("#e6edf3")),
            ("BACKGROUND",(0,0), (-1,-1), colors.HexColor("#161b22")),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#161b22"), colors.HexColor("#1c2130")]),
            ("TOPPADDING", (0,0),(-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("LEFTPADDING",(0,0),(-1,-1), 7),
            ("RIGHTPADDING",(0,0),(-1,-1), 7),
            ("ROUNDEDCORNERS",[4]),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # Differential table
        story.append(Paragraph("Differential Count Results", ParagraphStyle("sh", parent=styles["Normal"],
                                fontName="Helvetica-Bold", fontSize=11,
                                textColor=colors.HexColor("#e6edf3"), spaceAfter=6)))

        header_row = ["Cell Type", "Count", "Percentage", "Normal Range", "Status"]
        rows = [header_row]
        for cell in CELL_TYPES:
            cnt  = counts.get(cell["id"], 0)
            pct  = round(cnt / total * 100) if total else 0
            lo, hi = cell["normal_min"], cell["normal_max"]
            if hi == 0:
                in_range = cnt == 0
                norm_str = "0%"
            else:
                in_range = lo <= pct <= hi
                norm_str = f"{lo}–{hi}%"
            status = "✔ Normal" if in_range else "⚠ Abnormal"
            rows.append([cell["label"], str(cnt), f"{pct}%", norm_str, status])

        # Totals row
        rows.append(["TOTAL", str(total), "100%", "—", ""])

        col_w = [38*mm, 22*mm, 28*mm, 32*mm, 30*mm]
        diff_table = Table(rows, colWidths=col_w, repeatRows=1)

        ts_style = [
            # Header
            ("BACKGROUND",   (0,0), (-1,0), colors.HexColor("#1c2130")),
            ("TEXTCOLOR",    (0,0), (-1,0), colors.HexColor("#a5b4fc")),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS",(0,1),(-1,-2),[colors.HexColor("#0d1117"), colors.HexColor("#161b22")]),
            # Totals row
            ("BACKGROUND",   (0,-1), (-1,-1), colors.HexColor("#1c2130")),
            ("FONTNAME",     (0,-1), (-1,-1), "Helvetica-Bold"),
            ("TEXTCOLOR",    (0,-1), (-1,-1), colors.HexColor("#60a5fa")),
            # Text
            ("TEXTCOLOR",    (0,1), (0,-2), colors.HexColor("#e6edf3")),
            ("TEXTCOLOR",    (1,1), (3,-2), colors.HexColor("#e6edf3")),
            ("ALIGN",        (1,0), (-1,-1), "CENTER"),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",   (0,0), (-1,-1), 5),
            ("BOTTOMPADDING",(0,0), (-1,-1), 5),
            ("LEFTPADDING",  (0,0), (-1,-1), 7),
            ("GRID",         (0,0), (-1,-1), 0.4, colors.HexColor("#1c2130")),
        ]
        # Color status column
        for i, cell in enumerate(CELL_TYPES, start=1):
            cnt = counts.get(cell["id"], 0)
            pct = round(cnt / total * 100) if total else 0
            lo, hi = cell["normal_min"], cell["normal_max"]
            in_range = cnt == 0 if hi == 0 else (lo <= pct <= hi)
            color = colors.HexColor("#10b981") if in_range else colors.HexColor("#f87171")
            ts_style.append(("TEXTCOLOR", (4, i), (4, i), color))

        diff_table.setStyle(TableStyle(ts_style))
        story.append(diff_table)

        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#1c2130")))
        story.append(Spacer(1, 5))
        story.append(Paragraph(
            "This report is generated by ABC Cell Counter and is intended for reference purposes only. "
            "Results must be verified by a qualified healthcare professional.",
            ParagraphStyle("disc", parent=styles["Normal"], fontSize=7,
                           textColor=colors.HexColor("#7d8590"), alignment=TA_CENTER)
        ))

        doc.build(story)
        buf.seek(0)

        fname = f"DiffCount_{patient.replace(' ','_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        return send_file(buf, mimetype="application/pdf",
                         as_attachment=True, download_name=fname)

    except ImportError:
        return jsonify({"ok": False, "error": "reportlab not installed. Run: pip install reportlab"}), 500
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": traceback.format_exc()}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5050)
