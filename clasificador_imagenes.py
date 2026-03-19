import os
import shutil
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
from PIL import Image, ImageTk
import torch
from torchvision import models, transforms
from torchvision.models import ResNet50_Weights

thumb_size = (120, 120)


# ----- SELECCIÓN DE CARPETAS -----
def seleccionar_carpetas():
    root = tk.Tk()
    root.withdraw()

    messagebox.showinfo(
        "Paso 1 de 2",
        "Selecciona la carpeta RAÍZ que contiene tus imágenes.\n"
        "El script buscará automáticamente en todas sus subcarpetas."
    )
    input_folder = filedialog.askdirectory(title="Carpeta raíz con imágenes")
    if not input_folder:
        messagebox.showerror("Cancelado", "No se seleccionó carpeta de entrada.")
        root.destroy()
        return None, None

    messagebox.showinfo(
        "Paso 2 de 2",
        "Selecciona la carpeta donde se guardarán las imágenes clasificadas."
    )
    output_folder = filedialog.askdirectory(title="Carpeta de destino (clasificadas)")
    if not output_folder:
        messagebox.showerror("Cancelado", "No se seleccionó carpeta de destino.")
        root.destroy()
        return None, None

    root.destroy()
    return input_folder, output_folder


# ----- VENTANA DE PROGRESO -----
class VentanaProgreso:
    """Ventana con barra de progreso y log en tiempo real."""

    def __init__(self, total_imagenes):
        self.root = tk.Tk()
        self.root.title("Clasificando imágenes...")
        self.root.geometry("600x380")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)  # bloquear cierre manual

        # Título
        tk.Label(
            self.root, text="🔍 Clasificando imágenes con ResNet50",
            font=("Courier", 12, "bold"), fg="#ff4d00", bg="#1e1e1e"
        ).pack(pady=(18, 4))

        # Contador
        self.lbl_contador = tk.Label(
            self.root, text=f"0 / {total_imagenes} imágenes",
            font=("Courier", 10), fg="#aaaaaa", bg="#1e1e1e"
        )
        self.lbl_contador.pack()

        # Barra de progreso
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "naranja.Horizontal.TProgressbar",
            troughcolor="#2a2a2a",
            background="#ff4d00",
            thickness=18
        )
        self.barra = ttk.Progressbar(
            self.root, style="naranja.Horizontal.TProgressbar",
            length=540, maximum=total_imagenes, mode="determinate"
        )
        self.barra.pack(pady=10)

        # Archivo actual
        self.lbl_actual = tk.Label(
            self.root, text="Cargando modelo...",
            font=("Courier", 9), fg="#888888", bg="#1e1e1e", wraplength=560
        )
        self.lbl_actual.pack(pady=(0, 6))

        # Log scrollable
        frame_log = tk.Frame(self.root, bg="#1e1e1e")
        frame_log.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.log = tk.Text(
            frame_log, height=10, bg="#111111", fg="#cccccc",
            font=("Courier", 8), state="disabled", relief="flat",
            insertbackground="#ff4d00"
        )
        scroll_log = tk.Scrollbar(frame_log, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll_log.set)
        scroll_log.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

        self.total = total_imagenes
        self.procesadas = 0

    def actualizar(self, archivo, categoria):
        """Llamar desde el hilo de clasificación para actualizar la UI."""
        self.procesadas += 1
        self.root.after(0, self._actualizar_ui, archivo, categoria)

    def _actualizar_ui(self, archivo, categoria):
        self.barra["value"] = self.procesadas
        self.lbl_contador.config(text=f"{self.procesadas} / {self.total} imágenes")
        self.lbl_actual.config(text=f"→ {os.path.basename(archivo)}")

        self.log.config(state="normal")
        self.log.insert("end", f"[{self.procesadas:>4}] {os.path.basename(archivo):<35} → {categoria}\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def set_estado(self, texto):
        """Mostrar un mensaje de estado (ej: 'Cargando modelo...')"""
        self.root.after(0, self.lbl_actual.config, {"text": texto})

    def cerrar(self):
        self.root.after(0, self.root.destroy)

    def mainloop(self):
        self.root.mainloop()


# ----- CLASIFICACIÓN -----
def clasificar_imagenes(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    # Contar imágenes primero para la barra de progreso
    abs_output = os.path.abspath(output_folder)
    imagenes = []
    for dirpath, _, files in os.walk(input_folder):
        if os.path.abspath(dirpath).startswith(abs_output):
            continue
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                imagenes.append(os.path.join(dirpath, file))

    if not imagenes:
        messagebox.showwarning("Sin imágenes", "No se encontraron imágenes en la carpeta seleccionada.")
        return 0

    ventana = VentanaProgreso(len(imagenes))

    def tarea():
        ventana.set_estado("Cargando modelo ResNet50 (puede tardar unos segundos)...")

        weights = ResNet50_Weights.DEFAULT
        model = models.resnet50(weights=weights)
        model.eval()

        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])

        labels = weights.meta["categories"]
        ventana.set_estado("Modelo cargado. Procesando imágenes...")

        for path in imagenes:
            try:
                img = Image.open(path).convert("RGB")
            except Exception as e:
                print(f"No se pudo abrir: {path} ({e})")
                continue

            img_t = transform(img)
            batch = torch.unsqueeze(img_t, 0)

            with torch.no_grad():
                out = model(batch)

            _, index = torch.max(out, 1)
            label = labels[index.item()]
            label_safe = label.replace("/", "_").replace("\\", "_")

            target_folder = os.path.join(output_folder, label_safe)
            os.makedirs(target_folder, exist_ok=True)

            dest = os.path.join(target_folder, os.path.basename(path))
            if os.path.exists(dest):
                base, ext = os.path.splitext(os.path.basename(path))
                dest = os.path.join(target_folder, f"{base}_dup{ext}")

            shutil.copy2(path, dest)
            ventana.actualizar(path, label_safe)

        ventana.set_estado(f"✅ ¡Listo! {len(imagenes)} imágenes clasificadas.")
        ventana.root.after(1500, ventana.cerrar)  # cierra sola tras 1.5 seg

    hilo = threading.Thread(target=tarea, daemon=True)
    hilo.start()
    ventana.mainloop()
    hilo.join()

    return len(imagenes)


# ----- REVISIÓN VISUAL -----
def mostrar_revision(output_folder):
    root = tk.Tk()
    root.title("Revisión de imágenes clasificadas  |  Clic derecho para reclasificar")
    root.geometry("960x640")

    canvas = tk.Canvas(root, bg="#1e1e1e")
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    frame = tk.Frame(canvas, bg="#1e1e1e")
    canvas.create_window((0, 0), window=frame, anchor="nw")

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", on_mousewheel)

    image_refs = []
    row, col = 0, 0
    max_col = 6

    def mover_imagen(widget, path):
        nueva = simpledialog.askstring(
            "Reclasificar",
            f"Nueva categoría para:\n{os.path.basename(path)}",
            parent=root
        )
        if not nueva:
            return
        nueva_safe = nueva.strip().replace("/", "_").replace("\\", "_")
        destino_dir = os.path.join(output_folder, nueva_safe)
        os.makedirs(destino_dir, exist_ok=True)
        destino = os.path.join(destino_dir, os.path.basename(path))
        try:
            shutil.move(path, destino)
            widget.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    for folder in sorted(os.listdir(output_folder)):
        folder_path = os.path.join(output_folder, folder)
        if not os.path.isdir(folder_path):
            continue
        for file in sorted(os.listdir(folder_path)):
            path = os.path.join(folder_path, file)
            try:
                img = Image.open(path)
            except Exception:
                continue

            img.thumbnail(thumb_size)
            img_tk = ImageTk.PhotoImage(img)
            image_refs.append(img_tk)

            cell = tk.Frame(frame, bd=1, relief="solid", bg="#2a2a2a")
            cell.grid(row=row, column=col, padx=4, pady=4)

            lbl_img = tk.Label(cell, image=img_tk, bg="#2a2a2a")
            lbl_img.pack()

            lbl_nombre = tk.Label(
                cell,
                text=f"{folder}\n{file}",
                font=("Courier", 7),
                fg="#aaaaaa",
                bg="#2a2a2a",
                wraplength=120
            )
            lbl_nombre.pack()

            def on_right_click(event, w=cell, p=path):
                mover_imagen(w, p)

            lbl_img.bind("<Button-3>", on_right_click)
            lbl_nombre.bind("<Button-3>", on_right_click)

            col += 1
            if col > max_col:
                col = 0
                row += 1

    frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))
    root.mainloop()


# ----- EJECUCIÓN -----
if __name__ == "__main__":
    input_folder, output_folder = seleccionar_carpetas()

    if input_folder and output_folder:
        total = clasificar_imagenes(input_folder, output_folder)
        if total > 0:
            mostrar_revision(output_folder)
