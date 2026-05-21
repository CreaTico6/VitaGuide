from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def export_analysis_to_pdf(result: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    y = height - 50

    def write_line(text: str, step: int = 16) -> None:
        nonlocal y
        if y < 60:
            c.showPage()
            y = height - 50
        c.drawString(40, y, text)
        y -= step

    c.setFont("Helvetica-Bold", 14)
    write_line("Relatorio VitaGuide")
    c.setFont("Helvetica", 10)
    write_line(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    write_line("")

    supplements = ", ".join(result.get("selected_supplements", [])) or "(nenhum)"
    externals = ", ".join(result.get("selected_externals", [])) or "(nenhum)"
    write_line(f"Suplementos selecionados: {supplements}")
    write_line(f"Externos considerados: {externals}")
    write_line("")

    c.setFont("Helvetica-Bold", 12)
    write_line("Resultados")
    c.setFont("Helvetica", 10)

    findings = result.get("findings", [])
    if not findings:
        write_line("Sem resultados para os filtros atuais.")
    else:
        for idx, finding in enumerate(findings, start=1):
            header = f"{idx}. [{finding['severity'].upper()}] {finding['category']} - {finding['supplement']}"
            write_line(header)
            text = finding.get("text", "")
            for chunk in _wrap_text(text, 110):
                write_line(f"   {chunk}")
            matched = finding.get("matched_externals", [])
            if matched:
                write_line(f"   Externos correspondentes: {', '.join(matched)}")
            write_line("")

    unknown = result.get("unknown_external_terms", [])
    if unknown:
        c.setFont("Helvetica-Bold", 11)
        write_line("Termos externos nao reconhecidos")
        c.setFont("Helvetica", 10)
        write_line(", ".join(unknown))

    c.save()


def _wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines = []
    current = []
    size = 0
    for word in words:
        if size + len(word) + (1 if current else 0) <= max_chars:
            current.append(word)
            size += len(word) + (1 if current[:-1] else 0)
        else:
            lines.append(" ".join(current))
            current = [word]
            size = len(word)
    if current:
        lines.append(" ".join(current))
    return lines
