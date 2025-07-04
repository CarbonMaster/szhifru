import hashlib
import random
import sys
import os
import io
import zipfile
import struct
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import datetime
import shutil

# --- Twoje funkcje generowania permutacji, scramble_data itp. bez zmian ---


def save_encrypted_file_gui(suggested_name):
    filename = filedialog.asksaveasfilename(
        initialfile=suggested_name,
        defaultextension="",
        filetypes=[("All files", "*.*"), ("Encrypted files", "*.enc")],
        title="Zapisz zaszyfrowany plik"
    )
    return filename


def generate_permutation(length, password):
    seed = int(hashlib.sha256(password.encode()).hexdigest(), 16)
    indices = list(range(length))
    rng = random.Random(seed)
    rng.shuffle(indices)
    return indices


def apply_permutation(data, permutation):
    return bytes(data[i] for i in permutation)


def reverse_permutation(permutation):
    reversed_perm = [0] * len(permutation)
    for i, p in enumerate(permutation):
        reversed_perm[p] = i
    return reversed_perm


def scramble_data(data, password, mode="scramble"):
    permutation = generate_permutation(len(data), password)
    if mode == "scramble":
        return apply_permutation(data, permutation)
    elif mode == "unscramble":
        reversed_perm = reverse_permutation(permutation)
        return apply_permutation(data, reversed_perm)
    else:
        raise ValueError("Tryb musi być 'scramble' lub 'unscramble'")

# --- ZIP folderów (bez zmian) ---


def zip_folder_to_bytes(folder_path):
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=folder_path)
                zf.write(full_path, arcname)
    return mem_zip.getvalue()


def unzip_bytes_to_folder(data, output_folder):
    mem_zip = io.BytesIO(data)
    with zipfile.ZipFile(mem_zip, 'r') as zf:
        zf.extractall(output_folder)

# --- Zapis i odczyt pliku zaszyfrowanego z nagłówkiem ---


def save_encrypted_file(data, original_name, output_path):
    magic = b'MYEF'
    name_bytes = original_name.encode('utf-8')
    header = magic + struct.pack('>H', len(name_bytes)) + name_bytes
    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(data)


def load_encrypted_file(input_path):
    with open(input_path, 'rb') as f:
        magic = f.read(4)
        if magic != b'MYEF':
            raise ValueError("Niepoprawny plik szyfrowany")
        name_len = struct.unpack('>H', f.read(2))[0]
        name = f.read(name_len).decode('utf-8')
        encrypted_data = f.read()
    return name, encrypted_data

# --- Funkcje folderów (bez zmian) ---


class PasswordDialog(simpledialog.Dialog):
    def __init__(self, parent, prompt="Wprowadź hasło"):
        self.prompt = prompt
        super().__init__(parent)

    def body(self, master):
        self.title("Hasło")
        self.geometry("300x150")

        tk.Label(master, text=self.prompt).pack(pady=5)

        self.entry = tk.Entry(master, font=("Arial", 14), show="*")
        self.entry.pack(pady=5, padx=10, fill='x')

        self.show_var = tk.BooleanVar(value=False)
        self.checkbox = tk.Checkbutton(
            master, text="Pokaż hasło", variable=self.show_var, command=self.toggle_show)
        self.checkbox.pack()

        return self.entry  # focus

    def toggle_show(self):
        if self.show_var.get():
            self.entry.config(show="")
        else:
            self.entry.config(show="*")

    def apply(self):
        self.result = self.entry.get()


def ask_password(parent, prompt="Wprowadź hasło"):
    dialog = PasswordDialog(parent, prompt)
    return dialog.result


def encrypt_folder_gui():
    folder = filedialog.askdirectory(title="Wybierz folder do zaszyfrowania")
    if not folder:
        return

    password = ask_password(root, "Wprowadź hasło do szyfrowania")
    if not password:
        messagebox.showwarning("Brak hasła", "Nie podano hasła!")
        return

    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = save_encrypted_file_gui(now_str)
    if not output_file:
        return

    try:
        zipped = zip_folder_to_bytes(folder)
        scrambled = scramble_data(zipped, password, "scramble")
        save_encrypted_file(scrambled, os.path.basename(
            folder.rstrip(os.sep)) + ".zip", output_file)
        messagebox.showinfo(
            "Sukces", f"Folder zaszyfrowany i zapisany do:\n{output_file}")
    except Exception as e:
        messagebox.showerror("Błąd", str(e))


def safe_create_folder(base_folder, desired_name):
    folder_path = os.path.join(base_folder, desired_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return folder_path
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{desired_name}_{timestamp}"
        new_folder_path = os.path.join(base_folder, new_name)
        os.makedirs(new_folder_path)
        return new_folder_path


def decrypt_folder_gui():
    input_file = filedialog.askopenfilename(
        title="Wybierz plik zaszyfrowany",
        filetypes=[("All files", "*.*"), ("Encrypted files", "*.enc")]
    )
    if not input_file:
        return

    password = ask_password(root, "Wprowadź hasło do odszyfrowania")
    if not password:
        messagebox.showwarning("Brak hasła", "Nie podano hasła!")
        return

    output_base_folder = filedialog.askdirectory(
        title="Wybierz folder do rozpakowania")
    if not output_base_folder:
        return

    try:
        original_name, encrypted_data = load_encrypted_file(input_file)
        unscrambled = scramble_data(encrypted_data, password, "unscramble")

        folder_name = os.path.splitext(os.path.basename(input_file))[0]
        target_folder = safe_create_folder(output_base_folder, folder_name)

        temp_zip_path = os.path.join(target_folder, "temp_archive.zip")
        with open(temp_zip_path, "wb") as f:
            f.write(unscrambled)

        import zipfile
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_folder)

        os.remove(temp_zip_path)

        messagebox.showinfo(
            "Sukces", f"Folder odszyfrowany i wypakowany do:\n{target_folder}")
    except Exception as e:
        messagebox.showerror("Błąd", str(e))

# --- NOWE: szyfrowanie i deszyfrowanie PLIKÓW ---


def encrypt_file_gui():
    input_file = filedialog.askopenfilename(
        title="Wybierz plik do zaszyfrowania")
    if not input_file:
        return

    password = ask_password(root, "Wprowadź hasło do szyfrowania")
    if not password:
        messagebox.showwarning("Brak hasła", "Nie podano hasła!")
        return

    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    suggested_name = now_str

    output_file = save_encrypted_file_gui(suggested_name)
    if not output_file:
        return

    try:
        with open(input_file, "rb") as f:
            data = f.read()

        scrambled = scramble_data(data, password, "scramble")
        save_encrypted_file(
            scrambled, os.path.basename(input_file), output_file)
        messagebox.showinfo(
            "Sukces", f"Plik zaszyfrowany i zapisany do:\n{output_file}")
    except Exception as e:
        messagebox.showerror("Błąd", str(e))


def decrypt_file_gui():
    input_file = filedialog.askopenfilename(
        title="Wybierz plik zaszyfrowany",
        filetypes=[("All files", "*.*"), ("Encrypted files", "*.enc")]
    )
    if not input_file:
        return

    password = ask_password(root, "Wprowadź hasło do odszyfrowania")
    if not password:
        messagebox.showwarning("Brak hasła", "Nie podano hasła!")
        return

    output_folder = filedialog.askdirectory(
        title="Wybierz folder do zapisania odszyfrowanego pliku")
    if not output_folder:
        return

    try:
        original_name, encrypted_data = load_encrypted_file(input_file)
        unscrambled = scramble_data(encrypted_data, password, "unscramble")

        # Jeśli plik o tej nazwie istnieje w folderze, dopisz timestamp
        output_path = os.path.join(output_folder, original_name)
        if os.path.exists(output_path):
            base, ext = os.path.splitext(original_name)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                output_folder, f"{base}_{timestamp}{ext}")

        with open(output_path, "wb") as f:
            f.write(unscrambled)

        messagebox.showinfo(
            "Sukces", f"Plik odszyfrowany i zapisany do:\n{output_path}")
    except Exception as e:
        messagebox.showerror("Błąd", str(e))

# --- GUI główne ---


root = tk.Tk()
root.title("Folder & File Encryptor")
root.geometry("350x180")

btn_encrypt_folder = tk.Button(
    root, text="Zaszyfruj folder", command=encrypt_folder_gui)
btn_encrypt_folder.pack(padx=20, pady=5, fill='x')

btn_decrypt_folder = tk.Button(
    root, text="Odszyfruj folder", command=decrypt_folder_gui)
btn_decrypt_folder.pack(padx=20, pady=5, fill='x')

btn_encrypt_file = tk.Button(
    root, text="Zaszyfruj plik", command=encrypt_file_gui)
btn_encrypt_file.pack(padx=20, pady=5, fill='x')

btn_decrypt_file = tk.Button(
    root, text="Odszyfruj plik", command=decrypt_file_gui)
btn_decrypt_file.pack(padx=20, pady=5, fill='x')

root.mainloop()
