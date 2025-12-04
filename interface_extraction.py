"""
Script python créé par S. ROULLET
Dernière modification le 26/03/2025

Ce script contient les fonctions pour la fenêtre d'extraction des couleurs d'une image.
"""

import math
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json
import csv

# === Paramètres par défaut ===
DEFAULT_VALUES = {
    "Longueur Réelle X": 1,
    "Longueur Pixels X": 1,
    "Valeur Offset X": 0,
    "Pixel Offset X": 0,
    "Longueur Réelle Y": 1,
    "Longueur Pixels Y": 1,
    "Valeur Offset Y": 0,
    "Pixel Offset Y": 0,
    "Pas Echantillonage": 1,
    "Coordonnées Sud-Est (°)": "",
    "Coordonnées Nord-Ouest (°)": "",
    "Coordonnées Sud-Ouest (°)": "",
    "Coordonnées Nord-Est (°)": "",
}

BG_1 = "#A6E3E9"
BG_2 = "#71C9CE"
FG = "#112D4E"

def show_credits():
    messagebox.showinfo("Crédits",
                'Conversion RGB\n\n'
        "Outil pour convertir des couleurs en valeurs à partir d'une palette.\n\n"
        "Développé par Sylvain Roullet\n\n"
        "Utilise :\n"
        "- Python\n"
        "- Tkinter\n"
        "- Numpy\n"
        "- Pandas\n"
        "- Matplotlib\n\n"
        "© mars 2025, tous droits réservés."
    )

def parse_coord(text):
    """Convertit 'lon, lat' en tuple (lon, lat) ou None."""
    text = text.strip()
    if "," not in text:
        return None
    try:
        lon, lat = [float(v.strip()) for v in text.split(",")]
        return lon, lat
    except:
        return None

def helmert_transform_from_points(src_pts, dst_pts):
    """
    Calcule les paramètres de transformation d’Helmert 2D
    à partir d'au moins 2 paires de points.
    src_pts : liste [(x1,y1), (x2,y2), ...]
    dst_pts : liste [(lon1,lat1), (lon2,lat2), ...]
    Retourne (s, cosθ, sinθ, tx, ty)
    """

    # On utilise seulement deux vecteurs principaux (NW->NE et NW->SW)
    (x1, y1), (x2, y2) = src_pts[:2]
    (X1, Y1), (X2, Y2) = dst_pts[:2]

    # Vecteurs sources et GPS
    dx_src = x2 - x1
    dy_src = y2 - y1
    dx_dst = X2 - X1
    dy_dst = Y2 - Y1

    # Échelle
    norm_src = math.sqrt(dx_src**2 + dy_src**2)
    norm_dst = math.sqrt(dx_dst**2 + dy_dst**2)
    s = norm_dst / norm_src if norm_src != 0 else 1

    # Angle rotation
    angle_src = math.atan2(dy_src, dx_src)
    angle_dst = math.atan2(dy_dst, dx_dst)
    theta = angle_dst - angle_src

    cosθ = math.cos(theta)
    sinθ = math.sin(theta)

    # Translation
    tx = X1 - s * (cosθ * x1 - sinθ * y1)
    ty = Y1 - s * (sinθ * x1 + cosθ * y1)

    return s, cosθ, sinθ, tx, ty

def bilinear_geo(x, y, width, height, nw, ne, sw, se):
    """Interpolation bilinéaire entre 4 coins géographiques."""
    tx = x / (width - 1)
    ty = y / (height - 1)

    # interpolation lon
    lon = (
        (1 - tx) * (1 - ty) * nw[0] +
        tx       * (1 - ty) * ne[0] +
        (1 - tx) * ty       * sw[0] +
        tx       * ty       * se[0]
    )

    # interpolation lat
    lat = (
        (1 - tx) * (1 - ty) * nw[1] +
        tx       * (1 - ty) * ne[1] +
        (1 - tx) * ty       * sw[1] +
        tx       * ty       * se[1]
    )

    return lon, lat


class ExtractionWindow:
    def __init__(self, root):
        self.window = Toplevel(root)
        self.window.title("Extraction des couleurs")
        self.window.config(bg=BG_1)

        self.image_path = None
        self.image = None
        self.tk_image = None
        self.points = []
        self.select_offset_x = False
        self.select_offset_y = False
        self.select_value_x = False
        self.select_value_y = False
        self.previous_click = None
        self.is_saved = False
        self.ask_open = False
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.colors = []  # Liste des couleurs ajoutées depuis la palette

        self.create_menu()
        self.create_widgets()

    from tkinter import Menu

    def create_menu(self):
        """Crée la barre de menu avec des raccourcis clavier."""
        self.menu = Menu(self.window)
        self.window.config(menu=self.menu)

        file_menu = Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Ouvrir Image", command=self.open_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Exporter CSV", command=self.export_csv, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Charger Paramètres", command=self.load_parameters, accelerator="Ctrl+L")
        file_menu.add_command(label="Sauvegarder Paramètres", command=self.save_parameters, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.on_close, accelerator="Ctrl+Q")

        self.menu.add_cascade(label="Extraction des couleurs", menu=file_menu)

        # Ajout des raccourcis clavier
        self.window.bind_all("<Control-o>", lambda event: self.open_image())
        self.window.bind_all("<Control-e>", lambda event: self.export_csv())
        self.window.bind_all("<Control-s>", lambda event: self.save_parameters())
        self.window.bind_all("<Control-l>", lambda event: self.load_parameters())
        self.window.bind_all("<Control-q>", lambda event: self.on_close())

        aide_menu = Menu(self.menu, tearoff=0)
        aide_menu.add_command(label="Crédits", command=show_credits)
        self.menu.add_cascade(label="Aide", menu=aide_menu)

    def create_widgets(self):
        """Crée les boutons, entrées et canvas."""
        # Chargement d'une image
        Button(self.window, text="Charger une image", command=self.open_image, width=20, height=2, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=0, column=1, pady=10)

        # Frame pour les entrées
        self.frame_entries = Frame(self.window, bg=BG_2, padx=10, pady=10, relief="solid", bd=2)
        self.frame_entries.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.entries = {}
        for i, (nom, valeur) in enumerate(DEFAULT_VALUES.items()):
            self.create_entry(nom, valeur, i)

        # Canvas pour l'affichage de l'image
        frame_canvas = Frame(self.window, bg=BG_1)
        frame_canvas.grid(row=0, column=0, rowspan=5, padx=10, pady=10, sticky="nsew")


        Label(frame_canvas, text="\u2191", font=("Arial", 20, "bold"), bg=BG_1).grid(row=0, column=0, pady=5, sticky="S")
        Label(frame_canvas, text="Y", font=("Arial", 20, "bold"), bg=BG_1).grid(row=1, column=0, pady=5, sticky="N")
        Label(frame_canvas, text="X   \u2192", font=("Arial", 20, "bold"), bg=BG_1).grid(row=2, column=1, pady=5)

        self.canvas = Canvas(frame_canvas, width=800, height=600, bg="white", relief="solid", bd=2, highlightbackground=BG_1)
        self.canvas.grid(row=0, column=1, rowspan=2, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.get_coords)
        self.canvas.bind("<Motion>", self.update_coords)

        # Frame pour les boutons
        frame_buttons = Frame(self.window, padx=10, pady=10, bg=BG_1)
        frame_buttons.grid(row=2, column=1, sticky="nsew")

        Button(frame_buttons, text="Charger des param.", command=self.load_parameters, width=20, height=2,
               relief="solid", bg=BG_1, highlightbackground=BG_1, highlightcolor=FG).grid(row=0, column=0, padx=5, pady=5)
        Button(frame_buttons, text="Sauvegarder les param.", command=self.save_parameters, width=20, height=2,
               relief="solid", bg=BG_1, highlightbackground=BG_1, highlightcolor=FG).grid(row=0, column=1, padx=5, pady=5)

        Button(frame_buttons, text="Extraire les couleurs", command=self.export_csv, width=20, height=2,
               relief="solid", bg=BG_1, highlightbackground=BG_1, highlightcolor=FG).grid(row=1, column=0, columnspan=2, pady=10)

        # Label pour afficher les coordonnées
        self.coord_label = Label(self.window, text="Coordonnées : X=0.00, Y=0.00", font=("Arial", 15, "italic"),
                                 bg="lightyellow", relief="solid", bd=1)
        self.coord_label.grid(row=3, column=1)

    def create_entry(self, nom, default_value, n):
        """Crée une entrée avec un label et un bouton de sélection si applicable."""

        # Détermine colonne et rangée en fonction de n
        col = 0 if n < 8 else 2  # 1ère colonne pour n<10, 2ème colonne pour n>=10
        row_shift = 0 if n < 8 else -8  # Décale l’index pour garder le même espacement vertical
        row = 2 * (n + row_shift)  # Deux lignes par entrée (label + entry)

        # ---- Label ----
        label = Label(self.frame_entries, text=nom, bg=BG_2, font=("Arial", 12, "bold"))
        label.grid(row=row, column=col, sticky="w", padx=5, pady=2)

        # ---- Entry ----
        entry = Entry(self.frame_entries, width=10, relief="solid", highlightbackground=BG_2)
        entry.insert(0, str(default_value))
        entry.grid(row=row + 1, column=col, padx=5, pady=2)

        self.entries[nom] = entry

        # ---- Bouton ----
        btn_col = col + 1  # Le bouton va dans la colonne juste à droite

        if "Pixel Offset X" in nom:
            cmd = self.select_offset_x_action
        elif "Pixel Offset Y" in nom:
            cmd = self.select_offset_y_action
        elif "Longueur Pixels X" in nom:
            cmd = self.select_value_x_action
        elif "Longueur Pixels Y" in nom:
            cmd = self.select_value_y_action
        else:
            cmd = None

        if cmd:
            Button(self.frame_entries, text="Sélectionner", command=cmd, bg=BG_2, highlightbackground=BG_2, highlightcolor=FG).grid(row=row + 1, column=btn_col)

    def open_image(self):
        """Ouvre une image et l'affiche sur le canvas."""
        file_path = filedialog.askopenfilename(filetypes=[("PNG", "*.png"), ("JPG", "*.jpg"), ("JPEG", "*.jpeg")])
        if file_path:
            self.image_path = file_path
            self.image = Image.open(file_path)
            max_size = (800, 600)
            self.image.thumbnail(max_size)
            self.tk_image = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor=NW, image=self.tk_image)

    def get_coords(self, event):
        """Récupère les coordonnées du clic et applique les actions en cours."""
        x, y = event.x, event.y
        if self.image is None:
            if not self.ask_open:
                self.ask_open = True
                response = messagebox.askyesno("Erreur",
                                               "Aucune image chargée. Voulez-vous en charger une maintenant ?")
                if response:  # Si l'utilisateur choisit 'Oui'
                    self.open_image()  # Charge l'image
            return

        if self.image and 0 <= x < self.image.width and 0 <= y < self.image.height:
            if self.select_offset_x:
                self.entries["Pixel Offset X"].delete(0, END)
                self.entries["Pixel Offset X"].insert(0, x)
                self.select_offset_x = False
            elif self.select_offset_y:
                self.entries["Pixel Offset Y"].delete(0, END)
                self.entries["Pixel Offset Y"].insert(0, self.image.height - y)
                self.select_offset_y = False
            elif self.select_value_x or self.select_value_y:
                if self.previous_click is None:
                    self.previous_click = (x, y)
                else:
                    if self.select_value_x:
                        self.entries["Longueur Pixels X"].delete(0, END)
                        self.entries["Longueur Pixels X"].insert(0, abs(x - self.previous_click[0]))
                        self.select_value_x = False
                    if self.select_value_y:
                        self.entries["Longueur Pixels Y"].delete(0, END)
                        self.entries["Longueur Pixels Y"].insert(0, abs(y - self.previous_click[1]))
                        self.select_value_y = False
                    self.previous_click = None

    def update_coords(self, event):
        """Actualise l'affichage des coordonnées en temps réel."""
        x, y = event.x, event.y
        if self.image is None:
            if not self.ask_open:
                self.ask_open = True
                response = messagebox.askyesno("Erreur", "Aucune image chargée. Voulez-vous en charger une maintenant ?")
                if response:  # Si l'utilisateur choisit 'Oui'
                    self.open_image()  # Charge l'image
            return

        if self.image and 0 <= x < self.image.width and 0 <= y < self.image.height:
            real_x, real_y = self.convert_coords(x, self.image.height - y)
            self.coord_label.config(text=f"Coordonnées : X={real_x:.2f}, Y={real_y:.2f}")

    def select_offset_x_action(self):
        self.select_offset_x = True

    def select_offset_y_action(self):
        self.select_offset_y = True

    def select_value_x_action(self):
        self.select_value_x = True
        self.previous_click = None

    def select_value_y_action(self):
        self.select_value_y = True
        self.previous_click = None

    def convert_coords(self, x, y):
        """Convertit les pixels en unités réelles selon les paramètres."""
        try:
            # Récupération et conversion des valeurs d'échelle
            pixels_x = float(self.entries["Longueur Pixels X"].get())
            pixels_y = float(self.entries["Longueur Pixels Y"].get())

            if pixels_x == 0 or pixels_y == 0:
                messagebox.showerror("Erreur", "Longueur pixels ne peut pas être nulle.")
                return None, None

            echelle_pixels_x = float(self.entries["Longueur Réelle X"].get()) / pixels_x
            echelle_pixels_y = float(self.entries["Longueur Réelle Y"].get()) / pixels_y

            real_x = float(self.entries["Valeur Offset X"].get()) + (x - float(self.entries["Pixel Offset X"].get())) * echelle_pixels_x
            real_y = float(self.entries["Valeur Offset Y"].get()) + (y - float(self.entries["Pixel Offset Y"].get())) * echelle_pixels_y

        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides dans les champs.")
            return None, None

        return real_x, real_y

    def save_parameters(self):
        """Sauvegarde les paramètres dans un fichier JSON."""
        params = {key: entry.get() for key, entry in self.entries.items()}
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not file_path:
            return

        try:
            with open(file_path, "w") as f:
                json.dump(params, f, indent=4)
            messagebox.showinfo("Sauvegarde", "Paramètres sauvegardés avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde des paramètres : {e}")

    def load_parameters(self):
        """Charge les paramètres depuis un fichier JSON."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                params = json.load(f)
                for key, value in params.items():
                    if key in self.entries:
                        self.entries[key].delete(0, END)
                        self.entries[key].insert(0, value)
            messagebox.showinfo("Chargement", "Paramètres chargés avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des paramètres : {e}")

    def export_csv(self):
        if self.image is None:
            response = messagebox.askyesno("Erreur", "Aucune image chargée. Voulez-vous en charger une maintenant ?")
            if response:
                self.open_image()
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Fichiers CSV", "*.csv")])
        if not file_path:
            return

        try:
            pixels = self.image.load()
            pas = self.entries["Pas Echantillonage"].get()

            if not pas.isdigit() or int(pas) <= 0:
                messagebox.showerror("Erreur", "Le pas d'échantillonnage doit être un entier positif.")
                return
            pas = int(pas)

            # ---------------------------------------------------
            # Lecture des coordonnées GPS (2 ou 4 coins)
            # ---------------------------------------------------
            nw = parse_coord(self.entries["Coordonnées Nord-Ouest (°)"].get()) # Inversion car l'axe y est descendant
            ne = parse_coord(self.entries["Coordonnées Nord-Est (°)"].get())
            sw = parse_coord(self.entries["Coordonnées Sud-Ouest (°)"].get())
            se = parse_coord(self.entries["Coordonnées Sud-Est (°)"].get())

            width = self.image.width
            height = self.image.height

            # Initialisation
            use_four_points = False
            use_bilinear = False
            lon_min = lon_max = lat_min = lat_max = None

            # Mode HELMERT si 4 coins donnés
            if nw and ne and sw and se:
                use_four_points = True

            # Mode INTERPOLATION si seulement 2 coins donnés
            elif nw and se:
                use_bilinear = True
                lon_min = nw[0]
                lat_min = se[1]
                lon_max = se[0]
                lat_max = nw[1]

            elif ne and sw:
                use_bilinear = True
                lon_min = sw[0]
                lat_min = sw[1]
                lon_max = ne[0]
                lat_max = ne[1]

            # ---------------------------------------------------
            #   ÉCRITURE CSV
            # ---------------------------------------------------
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['X', 'Y', 'R', 'G', 'B'])
                for x in range(0, width, pas):
                    for y in range(0, height, pas):
                        color = pixels[x, y]

                        # use_four_points
                        if use_four_points:
                            lon, lat = bilinear_geo(x, y, self.image.width, self.image.height, nw, ne, sw, se)
                            writer.writerow([lon, lat, color[0], color[1], color[2]])

                        # INTERPOLATION
                        elif use_bilinear:
                            nx = x / (width - 1)
                            ny = y / (height - 1)
                            lon = lon_min + nx * (lon_max - lon_min)
                            lat = lat_max - ny * (lat_max - lat_min)
                            writer.writerow([lon, lat, color[0], color[1], color[2]])

                        # Conversion normale coords réelles
                        else:
                            real_x, real_y = self.convert_coords(x, height - y)
                            if real_x is None or real_y is None:
                                return
                            writer.writerow([real_x, real_y, color[0], color[1], color[2]])

            self.is_saved = True
            messagebox.showinfo("Exportation", f"Données exportées vers {file_path}")

        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'exportation : {e}")

    def on_close(self):
        """Vérifie si la palette a été sauvegardée avant de fermer la fenêtre."""
        if not self.is_saved and self.image:
            if messagebox.askyesno("Quitter",
                                   "L'extraction n'a pas été sauvegardée. Voulez-vous la sauvegarder avant de quitter ?"):
                self.export_csv()
        self.window.destroy()