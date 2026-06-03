from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from .engine import analyze
from .pdf_export import export_analysis_to_pdf


class ScrollableCheckboxFrame(tk.Frame):
    """A scrollable frame containing checkboxes."""
    
    def __init__(self, parent: tk.Widget, items: list[str], **kwargs) -> None:
        super().__init__(parent, **kwargs)
        
        self.items = items
        self.var_dict: dict[str, tk.BooleanVar] = {}
        self.checkbox_widgets: dict[str, tk.Checkbutton] = {}
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel to scrollbar
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        
        self._populate_checkboxes(items)
    
    def _on_mousewheel(self, event) -> None:
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
    
    def _populate_checkboxes(self, items: list[str], selected_items: set[str] | None = None) -> None:
        selected_items = selected_items or set()
        for item in items:
            var = tk.BooleanVar(value=item in selected_items)
            self.var_dict[item] = var
            cb = tk.Checkbutton(self.scrollable_frame, text=item, variable=var)
            cb.pack(anchor="w")
            self.checkbox_widgets[item] = cb
    
    def set_items(self, items: list[str], selected_items: set[str] | None = None) -> None:
        """Update the list of items and refresh checkboxes."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.var_dict.clear()
        self.checkbox_widgets.clear()
        self._populate_checkboxes(items, selected_items)
    
    def get_selected(self) -> list[str]:
        """Return list of selected items."""
        return [item for item, var in self.var_dict.items() if var.get()]
    
    def clear_selection(self) -> None:
        """Clear all selections."""
        for var in self.var_dict.values():
            var.set(False)


class VitaGuideApp:
    def __init__(self, root: tk.Tk, dataset_path: Path) -> None:
        self.root = root
        self.root.title("VitaGuide")
        self.root.geometry("1020x640")
        self.root.minsize(920, 560)

        self.dataset_path = dataset_path
        self.dataset = self._load_dataset()
        self.last_result = None

        self.supplement_names = sorted([item["name"] for item in self.dataset.get("items", [])], key=str.lower)
        self.external_names = sorted(self.dataset.get("external_catalog", []), key=str.lower)

        self._build_ui()

    def _load_dataset(self) -> dict:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        with self.dataset_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _build_ui(self) -> None:
        header = tk.Frame(self.root)
        header.pack(fill=tk.X, padx=12, pady=(10, 0))
        tk.Label(header, text="VitaGuide", font=("Segoe UI", 15, "bold")).pack(side=tk.LEFT)
        tk.Label(header, text="by TiSoft", font=("Segoe UI", 10), fg="#5b6470").pack(side=tk.LEFT, padx=(8, 0), pady=(3, 0))

        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        left = tk.Frame(container, width=380)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right = tk.Frame(container)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Supplements with checkboxes
        tk.Label(left, text="Suplementos", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.supp_filter_var = tk.StringVar()
        self.supp_filter_var.trace_add("write", self._refresh_supplement_list)
        tk.Entry(left, textvariable=self.supp_filter_var).pack(fill=tk.X, pady=(2, 5))

        checkbox_frame = tk.Frame(left, height=170)
        checkbox_frame.pack(fill=tk.X, pady=(0, 8))
        checkbox_frame.pack_propagate(False)
        
        self.supp_checkbox_frame = ScrollableCheckboxFrame(checkbox_frame, self.supplement_names)
        self.supp_checkbox_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(left, text="Externos (catalogo)", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(2, 0))
        self.external_filter_var = tk.StringVar()
        self.external_filter_var.trace_add("write", self._refresh_external_list)
        tk.Entry(left, textvariable=self.external_filter_var).pack(fill=tk.X, pady=(2, 5))

        external_checkbox_frame = tk.Frame(left, height=130)
        external_checkbox_frame.pack(fill=tk.X, pady=(0, 8))
        external_checkbox_frame.pack_propagate(False)

        self.external_checkbox_frame = ScrollableCheckboxFrame(external_checkbox_frame, self.external_names)
        self.external_checkbox_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(left, text="Externos em texto livre", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(2, 0))
        tk.Label(
            left,
            text="Insira termos livres (1 por linha ou separados por virgula/;).",
            font=("Segoe UI", 8),
            fg="#5b6470",
        ).pack(anchor="w", pady=(1, 2))
        self.free_text = ScrolledText(left, wrap=tk.WORD, height=4)
        self.free_text.pack(fill=tk.X, pady=(0, 8))

        button_row = tk.Frame(left)
        button_row.pack(fill=tk.X, pady=(0, 0))
        tk.Button(button_row, text="Analisar", command=self._run_analysis).pack(side=tk.LEFT)
        tk.Button(button_row, text="Exportar PDF", command=self._export_pdf).pack(side=tk.LEFT, padx=8)
        tk.Button(button_row, text="Limpar externos", command=self._clear_externals).pack(side=tk.LEFT)

        tk.Label(right, text="Resultados", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.output = ScrolledText(right, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    def _refresh_supplement_list(self, *_args) -> None:
        filter_value = self.supp_filter_var.get().strip().lower()
        selected = set(self.supp_checkbox_frame.get_selected())
        filtered_items = []
        for name in self.supplement_names:
            if not filter_value or filter_value in name.lower():
                filtered_items.append(name)
        self.supp_checkbox_frame.set_items(filtered_items, selected)

    def _refresh_external_list(self, *_args) -> None:
        filter_value = self.external_filter_var.get().strip().lower()
        selected = set(self.external_checkbox_frame.get_selected())
        filtered_items = []
        for name in self.external_names:
            if not filter_value or filter_value in name.lower():
                filtered_items.append(name)
        self.external_checkbox_frame.set_items(filtered_items, selected)

    def _clear_externals(self) -> None:
        self.external_filter_var.set("")
        self.external_checkbox_frame.clear_selection()
        self.free_text.delete("1.0", tk.END)

    def _run_analysis(self) -> None:
        selected_supp = self.supp_checkbox_frame.get_selected()
        if not selected_supp:
            messagebox.showwarning("VitaGuide", "Selecione pelo menos um suplemento.")
            return

        selected_externals = self.external_checkbox_frame.get_selected()
        free_text = self.free_text.get("1.0", tk.END).strip()

        result = analyze(self.dataset, selected_supp, selected_externals, free_text)
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
