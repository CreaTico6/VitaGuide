from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from .engine import analyze
from .pdf_export import export_analysis_to_pdf


class ScrollableCheckboxFrame(tk.Frame):
    def __init__(self, master: tk.Misc, *, height: int = 320) -> None:
        super().__init__(master)
        self._selected: set[str] = set()
        self._variables: dict[str, tk.BooleanVar] = {}

        self.canvas = tk.Canvas(self, height=height, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas)
        self.inner.bind("<Configure>", self._on_configure)

        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def set_items(self, names: list[str]) -> None:
        for widget in self.inner.winfo_children():
            widget.destroy()
        self._variables.clear()

        for name in names:
            var = tk.BooleanVar(value=name in self._selected)
            self._variables[name] = var
            tk.Checkbutton(
                self.inner,
                text=name,
                variable=var,
                anchor="w",
                command=lambda n=name, v=var: self._toggle(n, v.get()),
            ).pack(fill=tk.X, anchor="w")

    def _toggle(self, name: str, selected: bool) -> None:
        if selected:
            self._selected.add(name)
        else:
            self._selected.discard(name)

    def selected_values(self) -> list[str]:
        for name, var in self._variables.items():
            self._toggle(name, var.get())
        return sorted(self._selected, key=str.lower)


class VitaGuideApp:
    def __init__(self, root: tk.Tk, dataset_path: Path) -> None:
        self.root = root
        self.root.title("VitaGuide")
        self.root.geometry("980x680")

        self.dataset_path = dataset_path
        self.dataset = self._load_dataset()
        self.last_result = None

        self.supplement_names = sorted([item["name"] for item in self.dataset.get("items", [])], key=str.lower)
        self._build_ui()

    def _load_dataset(self) -> dict:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        with self.dataset_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _build_ui(self) -> None:
        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = tk.Frame(container, width=360)
        left.pack(side=tk.LEFT, fill=tk.Y)

        right = tk.Frame(container)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(left, text="Suplementos (multiselecao)", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.supp_filter_var = tk.StringVar()
        self.supp_filter_var.trace_add("write", self._refresh_supplement_list)
        tk.Entry(left, textvariable=self.supp_filter_var).pack(fill=tk.X, pady=(2, 5))

        self.supp_checkboxes = ScrollableCheckboxFrame(left, height=300)
        self.supp_checkboxes.pack(fill=tk.X)

        tk.Label(left, text="Externos em texto livre (separados por virgula)").pack(anchor="w", pady=(12, 0))
        self.free_text = tk.Entry(left)
        self.free_text.pack(fill=tk.X, pady=(2, 8))

        button_row = tk.Frame(left)
        button_row.pack(fill=tk.X, pady=(8, 0))
        tk.Button(button_row, text="Analisar", command=self._run_analysis).pack(side=tk.LEFT)
        tk.Button(button_row, text="Exportar PDF", command=self._export_pdf).pack(side=tk.LEFT, padx=8)

        tk.Label(right, text="Resultados", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.output = ScrolledText(right, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        self._refresh_supplement_list()

    def _refresh_supplement_list(self, *_args) -> None:
        filter_value = self.supp_filter_var.get().strip().lower()
        filtered_names = []
        for name in self.supplement_names:
            if filter_value and filter_value not in name.lower():
                continue
            filtered_names.append(name)
        self.supp_checkboxes.set_items(filtered_names)

    def _run_analysis(self) -> None:
        selected_supp = self.supp_checkboxes.selected_values()
        if not selected_supp:
            messagebox.showwarning("VitaGuide", "Selecione pelo menos um suplemento.")
            return

        free_text = self.free_text.get().strip()

        result = analyze(self.dataset, selected_supp, [], free_text)
        self.last_result = result
        self._render_result(result)

    def _render_result(self, result: dict) -> None:
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "Analise VitaGuide\n")
        self.output.insert(tk.END, "=" * 68 + "\n")
        self.output.insert(tk.END, f"Suplementos: {', '.join(result['selected_supplements'])}\n")
        externals = ", ".join(result.get("selected_externals", [])) or "(nenhum)"
        self.output.insert(tk.END, f"Externos: {externals}\n\n")

        findings = result.get("findings", [])
        if not findings:
            self.output.insert(tk.END, "Sem resultados para os filtros atuais.\n")
        else:
            for idx, item in enumerate(findings, start=1):
                self.output.insert(
                    tk.END,
                    f"{idx}. [{item['severity'].upper()}] {item['category']} - {item['supplement']}\n",
                )
                self.output.insert(tk.END, f"   {item['text']}\n")
                if item.get("matched_externals"):
                    self.output.insert(tk.END, f"   Externos correspondentes: {', '.join(item['matched_externals'])}\n")
                self.output.insert(tk.END, "\n")

        unknown = result.get("unknown_external_terms", [])
        if unknown:
            self.output.insert(tk.END, "Termos externos nao reconhecidos: " + ", ".join(unknown) + "\n")

    def _export_pdf(self) -> None:
        if not self.last_result:
            messagebox.showinfo("VitaGuide", "Execute uma analise antes de exportar.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Guardar PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="relatorio_vitaguide.pdf",
        )
        if not save_path:
            return

        try:
            export_analysis_to_pdf(self.last_result, Path(save_path))
            messagebox.showinfo("VitaGuide", f"PDF exportado para:\n{save_path}")
        except Exception as exc:
            messagebox.showerror("Erro", f"Falha ao exportar PDF: {exc}")


def main(dataset_path: Path) -> None:
    root = tk.Tk()
    app = VitaGuideApp(root, dataset_path)
    root.mainloop()
