import requests
import tkinter as tk
from tkinter import messagebox, filedialog
import time

# Configuración: actualiza BASE_URL si cambias el puerto o subes el backend
BASE_URL = "http://localhost:3000/admin"
ADMIN_KEY = "tu_clave_secreta"

entries_list = []
selected_id = None

def add_entry():
    titulo = new_title_entry.get()
    contenido = new_content_text.get("1.0", tk.END).strip()
    if not titulo or not contenido:
        messagebox.showwarning("Error", "Título y contenido no pueden estar vacíos.")
        return
    res = requests.post(f"{BASE_URL}/nueva",
                        json={"titulo": titulo, "contenido": contenido},
                        headers={"x-admin-key": ADMIN_KEY})
    if res.status_code == 200:
        messagebox.showinfo("Éxito", "Entrada agregada con éxito.")
        new_title_entry.delete(0, tk.END)
        new_content_text.delete("1.0", tk.END)
        load_entries()
    else:
        try:
            error_details = res.json()
        except Exception:
            error_details = res.text
        messagebox.showerror("Error", f"Error agregando entrada:\n{error_details}")

def load_entries():
    global entries_list, selected_id
    try:
        res = requests.get("http://localhost:3000/todas", params={"_": str(time.time())})
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar entradas: {e}")
        return
    if res.status_code != 200:
        messagebox.showerror("Error", f"No se pudieron cargar las entradas. Código: {res.status_code}")
        return
    try:
        entries_list = res.json()
    except Exception as e:
        messagebox.showerror("Error", f"Error al decodificar entradas: {e}")
        return
    listbox.delete(0, tk.END)
    for entry in entries_list:
        listbox.insert(tk.END, f"[{entry['id']}] {entry['titulo']}")
    selected_id = None
    edit_title_entry.delete(0, tk.END)
    edit_content_text.config(state=tk.NORMAL)
    edit_content_text.delete("1.0", tk.END)
    edit_content_text.config(state=tk.DISABLED)
    print(f"Se cargaron {len(entries_list)} entradas.")

def on_select(event):
    global selected_id
    if not listbox.curselection():
        return
    index = listbox.curselection()[0]
    entry = entries_list[index]
    selected_id = entry['id']
    edit_title_entry.delete(0, tk.END)
    edit_title_entry.insert(0, entry['titulo'])
    edit_content_text.config(state=tk.NORMAL)
    edit_content_text.delete("1.0", tk.END)
    edit_content_text.insert(tk.END, entry['contenido'])

def update_entry():
    if not listbox.curselection():
        messagebox.showwarning("Error", "Selecciona una entrada para actualizar.")
        return
    new_title = edit_title_entry.get()
    new_content = edit_content_text.get("1.0", tk.END).strip()
    if not new_title or not new_content:
        messagebox.showwarning("Error", "Título y contenido no pueden estar vacíos.")
        return
    res = requests.put(f"{BASE_URL}/modificar/{selected_id}",
                       json={"titulo": new_title, "contenido": new_content},
                       headers={"x-admin-key": ADMIN_KEY})
    if res.status_code == 200:
        messagebox.showinfo("Éxito", "Entrada actualizada.")
        load_entries()
    else:
        try:
            error_details = res.json()
        except Exception:
            error_details = res.text
        messagebox.showerror("Error", f"Error actualizando entrada:\n{error_details}")

def delete_entry():
    if not listbox.curselection():
        messagebox.showwarning("Error", "Selecciona una entrada para eliminar.")
        return
    res = requests.delete(f"{BASE_URL}/borrar/{selected_id}",
                          headers={"x-admin-key": ADMIN_KEY})
    if res.status_code == 200:
        messagebox.showinfo("Éxito", "Entrada eliminada.")
        load_entries()
    else:
        try:
            error_details = res.json()
        except Exception:
            error_details = res.text
        messagebox.showerror("Error", f"Error eliminando entrada:\n{error_details}")

def upload_photo():
    file_path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg;*.png;*.jpeg")])
    if not file_path:
        return
    with open(file_path, "rb") as file:
        res = requests.post(f"{BASE_URL}/subir-foto",
                            files={"foto": file},
                            headers={"x-admin-key": ADMIN_KEY})
    if res.status_code == 200:
        messagebox.showinfo("Éxito", "Foto subida con éxito.")
    else:
        try:
            error_details = res.json()
        except Exception:
            error_details = res.text
        messagebox.showerror("Error", f"Error subiendo foto:\n{error_details}")

root = tk.Tk()
root.title("Administrador del Diario")
root.geometry("800x600")

frame_new = tk.LabelFrame(root, text="Agregar Nueva Entrada", padx=10, pady=10)
frame_new.pack(padx=10, pady=10, fill="x")

tk.Label(frame_new, text="Título:").grid(row=0, column=0, sticky="w")
new_title_entry = tk.Entry(frame_new, width=50)
new_title_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Label(frame_new, text="Contenido:").grid(row=1, column=0, sticky="nw")
new_content_text = tk.Text(frame_new, height=5, width=50)
new_content_text.grid(row=1, column=1, padx=5, pady=5)
tk.Button(frame_new, text="Agregar Entrada", command=add_entry).grid(row=2, column=1, pady=5, sticky="e")

frame_list = tk.LabelFrame(root, text="Entradas Publicadas", padx=10, pady=10)
frame_list.pack(padx=10, pady=10, fill="both", expand=True)

listbox = tk.Listbox(frame_list, width=80)
listbox.pack(side="left", fill="both", expand=True)
listbox.bind("<<ListboxSelect>>", on_select)

scrollbar = tk.Scrollbar(frame_list)
scrollbar.pack(side="right", fill="y")
listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=listbox.yview)

frame_edit = tk.LabelFrame(root, text="Editar Entrada Seleccionada", padx=10, pady=10)
frame_edit.pack(padx=10, pady=10, fill="x")

tk.Label(frame_edit, text="Título:").grid(row=0, column=0, sticky="w")
edit_title_entry = tk.Entry(frame_edit, width=50)
edit_title_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Label(frame_edit, text="Contenido:").grid(row=1, column=0, sticky="nw")
edit_content_text = tk.Text(frame_edit, height=5, width=50)
edit_content_text.grid(row=1, column=1, padx=5, pady=5)
edit_content_text.config(state=tk.DISABLED)

button_frame = tk.Frame(frame_edit)
button_frame.grid(row=2, column=1, pady=5, sticky="e")
tk.Button(button_frame, text="Actualizar Entrada", command=update_entry).grid(row=0, column=0, padx=5)
tk.Button(button_frame, text="Eliminar Entrada", command=delete_entry).grid(row=0, column=1, padx=5)

frame_photo = tk.LabelFrame(root, text="Subir Nueva Foto", padx=10, pady=10)
frame_photo.pack(padx=10, pady=10, fill="x")
tk.Button(frame_photo, text="Seleccionar Imagen", command=upload_photo).pack()

load_entries()

root.mainloop()
