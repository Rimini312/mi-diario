import requests
import tkinter as tk
from tkinter import messagebox, filedialog
import time

# Rutas base para el backend
BASE_URL_PUBLIC = "https://mi-diario.onrender.com"
BASE_URL_ADMIN  = "https://mi-diario.onrender.com/admin"

# Clave de administrador
ADMIN_KEY = "Grabador5_"

entries_list = []
selected_id = None
prev_index = None  # Índice previo en la lista (para preservar cambios no guardados)

def load_entries():
    global entries_list, selected_id, prev_index
    try:
        res = requests.get(f"{BASE_URL_PUBLIC}/todas", params={"_": str(time.time())})
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar entradas: {e}")
        return

    if res.status_code != 200:
        messagebox.showerror("Error", f"No se pudieron cargar las entradas. Código: {res.status_code}")
        return

    try:
        entries_list = res.json()
    except Exception as e:
        messagebox.showerror("Error", f"Error al decodificar la lista de entradas: {e}")
        return

    listbox.delete(0, tk.END)
    for i, entry in enumerate(entries_list):
        listbox.insert(tk.END, f"[{entry['id']}] {entry['titulo']}")
    selected_id = None
    prev_index = None
    edit_title_entry.delete(0, tk.END)
    edit_content_text.config(state=tk.NORMAL)
    edit_content_text.delete("1.0", tk.END)
    edit_content_text.config(state=tk.DISABLED)

def add_entry():
    titulo = new_title_entry.get()
    contenido = new_content_text.get("1.0", tk.END).strip()
    if not titulo or not contenido:
        messagebox.showwarning("Error", "Título y contenido no pueden estar vacíos.")
        return

    try:
        res = requests.post(
            f"{BASE_URL_ADMIN}/nueva",
            json={"titulo": titulo, "contenido": contenido},
            headers={"x-admin-key": ADMIN_KEY}
        )
    except Exception as e:
        messagebox.showerror("Error", f"Error agregando entrada: {e}")
        return

    if res.status_code == 200:
        messagebox.showinfo("Éxito", "Entrada agregada con éxito.")
        new_title_entry.delete(0, tk.END)
        new_content_text.delete("1.0", tk.END)
        load_entries()
    else:
        try:
            error_details = res.json()
        except:
            error_details = res.text
        messagebox.showerror("Error", f"No se pudo agregar la entrada.\n{error_details}")

def on_select(event):
    global selected_id, prev_index
    if not listbox.curselection():
        return
    new_index = listbox.curselection()[0]
    entry = entries_list[new_index]
    
    # Si ya hay un índice previo, y el contenido en el área de edición difiere del contenido guardado de esa entrada,
    # se pregunta si desea sobrescribir los cambios.
    if prev_index is not None:
        # Obtén el contenido actual en el área de edición
        current_text = edit_content_text.get("1.0", tk.END).strip()
        # Si hay cambios y el nuevo índice es diferente al previo
        if current_text and new_index != prev_index:
            # Compara el contenido actual con el de la entrada que estaba seleccionada previamente
            if current_text != entries_list[prev_index]['contenido']:
                sobrescribir = messagebox.askyesno("Confirmar", "Hay cambios sin guardar. ¿Deseas sobrescribirlos con la entrada seleccionada?")
                if not sobrescribir:
                    # Revertir la selección al índice previo
                    listbox.selection_clear(0, tk.END)
                    listbox.selection_set(prev_index)
                    listbox.activate(prev_index)
                    return

    # Actualiza la selección
    selected_id = entry['id']
    prev_index = new_index
    edit_title_entry.delete(0, tk.END)
    edit_title_entry.insert(0, entry['titulo'])
    edit_content_text.config(state=tk.NORMAL)
    edit_content_text.delete("1.0", tk.END)
    edit_content_text.insert(tk.END, entry['contenido'])

def update_entry():
    if selected_id is None:
        messagebox.showwarning("Error", "Selecciona una entrada para actualizar.")
        return
    new_title = edit_title_entry.get()
    new_content = edit_content_text.get("1.0", tk.END).strip()
    if not new_title or not new_content:
        messagebox.showwarning("Error", "Título y contenido no pueden estar vacíos.")
        return

    try:
        res = requests.put(
            f"{BASE_URL_ADMIN}/modificar/{selected_id}",
            json={"titulo": new_title, "contenido": new_content},
            headers={"x-admin-key": ADMIN_KEY}
        )
    except Exception as e:
        messagebox.showerror("Error", f"Error actualizando entrada: {e}")
        return

    if res.status_code == 200:
        messagebox.showinfo("Éxito", "Entrada actualizada.")
        load_entries()
    else:
        try:
            error_details = res.json()
        except:
            error_details = res.text
        messagebox.showerror("Error", f"No se pudo actualizar la entrada.\n{error_details}")

def delete_entry():
    if selected_id is None:
        messagebox.showwarning("Error", "Selecciona una entrada para eliminar.")
        return

    try:
        res = requests.delete(
            f"{BASE_URL_ADMIN}/borrar/{selected_id}",
            headers={"x-admin-key": ADMIN_KEY}
        )
    except Exception as e:
        messagebox.showerror("Error", f"Error eliminando entrada: {e}")
        return

    if res.status_code == 200:
        messagebox.showinfo("Éxito", "Entrada eliminada.")
        load_entries()
    else:
        try:
            error_details = res.json()
        except:
            error_details = res.text
        messagebox.showerror("Error", f"No se pudo eliminar la entrada.\n{error_details}")

def upload_photo():
    file_path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg;*.png;*.jpeg")])
    if not file_path:
        return

    try:
        with open(file_path, "rb") as file:
            res = requests.post(
                f"{BASE_URL_ADMIN}/subir-foto",
                files={"foto": file},
                headers={"x-admin-key": ADMIN_KEY}
            )
    except Exception as e:
        messagebox.showerror("Error", f"Error subiendo foto: {e}")
        return

    if res.status_code == 200:
        messagebox.showinfo("Éxito", "Foto subida con éxito.")
    else:
        try:
            error_details = res.json()
        except:
            error_details = res.text
        messagebox.showerror("Error", f"No se pudo subir la foto.\n{error_details}")

########################
# Interfaz con Tkinter
########################

root = tk.Tk()
root.title("Administrador del Diario")
root.geometry("800x600")

# Frame: Agregar nueva entrada
frame_new = tk.LabelFrame(root, text="Agregar Nueva Entrada", padx=10, pady=10)
frame_new.pack(padx=10, pady=10, fill="x")

tk.Label(frame_new, text="Título:").grid(row=0, column=0, sticky="w")
new_title_entry = tk.Entry(frame_new, width=50)
new_title_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame_new, text="Contenido:").grid(row=1, column=0, sticky="nw")
new_content_text = tk.Text(frame_new, height=5, width=50)
new_content_text.grid(row=1, column=1, padx=5, pady=5)

tk.Button(frame_new, text="Agregar Entrada", command=add_entry).grid(row=2, column=1, pady=5, sticky="e")

# Frame: Lista de entradas
frame_list = tk.LabelFrame(root, text="Entradas Publicadas", padx=10, pady=10)
frame_list.pack(padx=10, pady=10, fill="both", expand=True)

listbox = tk.Listbox(frame_list, width=80)
listbox.pack(side="left", fill="both", expand=True)
listbox.bind("<<ListboxSelect>>", on_select)

scrollbar = tk.Scrollbar(frame_list)
scrollbar.pack(side="right", fill="y")
listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=listbox.yview)

# Frame: Editar la entrada seleccionada
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

# Frame: Subir foto
frame_photo = tk.LabelFrame(root, text="Subir Nueva Foto", padx=10, pady=10)
frame_photo.pack(padx=10, pady=10, fill="x")
tk.Button(frame_photo, text="Seleccionar Imagen", command=upload_photo).pack()

# Cargar entradas al iniciar
load_entries()

root.mainloop()
