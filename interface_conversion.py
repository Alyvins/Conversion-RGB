"""
Script python créé par S. ROULLET
Dernière modification le 28/03/2025

Ce script contient les fonctions pour la fenêtre de conversion des couleurs en valeurs.
"""

import pandas as pd
import numpy as np
import json
import time
import os
import csv
import queue
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.interpolate import interp1d
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
import threading


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

# === Fonctions de traitement ===
def load_reference_palette(file):
    data = []
    with open(file, 'r') as f:
        for line in f:
            if line.startswith('#'):  # Ignorer les lignes commentées
                continue
            parts = line.strip().split(',')
            value = float(parts[0])
            r, g, b = map(int, parts[1:4])
            data.append((value, r, g, b))
    return pd.DataFrame(data, columns=['value', 'r', 'g', 'b'])


def interpolate_palette(ref_palette, n_points):
    if n_points <= len(ref_palette):
        return ref_palette

    x = ref_palette['value']
    r = ref_palette['r']
    g = ref_palette['g']
    b = ref_palette['b']

    new_x = np.linspace(x.min(), x.max(), n_points)
    r_interp = np.zeros_like(new_x)
    g_interp = np.zeros_like(new_x)
    b_interp = np.zeros_like(new_x)

    # Interpolation en plusieurs étapes pour afficher la progression
    for i in range(n_points):
        r_interp[i] = interp1d(x, r, kind='linear')(new_x[i])
        g_interp[i] = interp1d(x, g, kind='linear')(new_x[i])
        b_interp[i] = interp1d(x, b, kind='linear')(new_x[i])

    return pd.DataFrame({
        'value': new_x,
        'r': r_interp.astype(int),
        'g': g_interp.astype(int),
        'b': b_interp.astype(int)
    })


def plot_palette_vertical(palette, output_file, n_ticks):
    fig, ax = plt.subplots(figsize=(2, 10))

    palette = palette.sort_values(by="value", ascending=True).reset_index(drop=True)

    for i in range(len(palette) - 1):
        ax.add_patch(plt.Rectangle((0, i), 1, 1, color=np.array([palette.iloc[i, 1:4]]) / 255))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, len(palette))
    ax.set_xticks([])

    tick_positions = np.linspace(0, len(palette) - 1, n_ticks).astype(int)
    ax.set_yticks(tick_positions)
    ax.set_yticklabels([palette.loc[i, 'value'].round(2) for i in tick_positions])

    plt.savefig(output_file, bbox_inches='tight', dpi=300)


def create_custom_cmap(palette_df):
    # Tri ascendant pour correspondre à plot_palette_vertical
    palette_sorted = palette_df.sort_values(by="value", ascending=True).reset_index(drop=True)
    colors = palette_sorted[['r','g','b']].values / 255.0

    cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", colors)
    return cmap


def plot_scatter(dataframe, x_col, y_col, z_col, palette, output_file):
    x_data = dataframe[x_col]
    y_data = dataframe[y_col]
    z_data = dataframe[z_col]

    cmap = create_custom_cmap(palette)

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(x_data, y_data, c=z_data, cmap=cmap, s=5, edgecolors='none')

    ax.set_title(f'Nuage de points ({x_col}, {y_col}, {z_col})', fontsize=16)
    ax.set_xlabel(x_col, fontsize=12)
    ax.set_ylabel(y_col, fontsize=12)

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label(z_col, fontsize=12)

    plt.savefig(output_file, bbox_inches='tight', dpi=600)


def color_distance(c1, c2):
    return np.sqrt(np.sum((np.array(c1) - np.array(c2)) ** 2))


def match_color_to_value(r, g, b, reference, update_progress=None):
    distances = np.sqrt(
        (reference['r'] - r) ** 2 +
        (reference['g'] - g) ** 2 +
        (reference['b'] - b) ** 2
    )

    if update_progress:
        update_progress()

    closest_idx = np.argmin(distances)
    return reference.loc[closest_idx, 'value'], distances[closest_idx]

class ConversionWindow:
    def __init__(self, root):
        self.window = Toplevel(root)
        self.window.title("Convertir couleurs en valeurs")
        self.queue = queue.Queue()
        self.window.config(bg=BG_1)

        # Variables de configuration
        self.fichier_extraction = StringVar()
        self.fichier_palette = StringVar()
        self.dossier_sortie = StringVar()
        self.fichier_sortie_image_palette = StringVar(value="Palette_interpolée")
        self.fichier_sortie_image_csv = StringVar(value="Nuage_points")
        self.fichier_sortie_csv = StringVar(value="Extraction_convertie")

        self.n_points_interpolation = StringVar(value="1000")
        self.n_ticks_yticks = StringVar(value="10")
        self.seuil_distance_couleur = StringVar(value="80")

        # Variables pour les indices de colonne
        self.colonne_X = StringVar(value="0")
        self.colonne_Y = StringVar(value="1")
        self.colonne_R = StringVar(value="2")
        self.colonne_G = StringVar(value="3")
        self.colonne_B = StringVar(value="4")

        self.nom_X = StringVar(value="X")
        self.nom_Y = StringVar(value="Y")
        self.nom_Z = StringVar(value="Z")

        self.is_processing = False
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Interface graphique
        self.create_widgets()
        self.create_menu()

    def create_menu(self):
        """Crée la barre de menu avec des raccourcis clavier."""
        self.menu = Menu(self.window)
        self.window.config(menu=self.menu)

        file_menu = Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Sélectionner CSV", command=self.browse_extraction_file, accelerator="Ctrl+E")
        file_menu.add_command(label="Sélectionner Palette", command=self.browse_palette_file, accelerator="Ctrl+P")
        file_menu.add_command(label="Sélectionner Dossier", command=self.browse_folder, accelerator="Ctrl+D")
        file_menu.add_separator()
        file_menu.add_command(label="Charger Paramètres", command=self.load_parameters, accelerator="Ctrl+L")
        file_menu.add_command(label="Sauvegarder Paramètres", command=self.save_parameters, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.on_close, accelerator="Ctrl+Q")

        self.menu.add_cascade(label="Convertir couleurs en valeurs", menu=file_menu)

        aide_menu = Menu(self.menu, tearoff=0)
        aide_menu.add_command(label="Crédits", command=show_credits)
        self.menu.add_cascade(label="Aide", menu=aide_menu)

        # Ajout des raccourcis clavier
        self.window.bind_all("<Control-e>", lambda event: self.browse_extraction_file())
        self.window.bind_all("<Control-p>", lambda event: self.browse_palette_file())
        self.window.bind_all("<Control-d>", lambda event: self.browse_folder())
        self.window.bind_all("<Control-s>", lambda event: self.save_parameters())
        self.window.bind_all("<Control-l>", lambda event: self.load_parameters())
        self.window.bind_all("<Control-q>", lambda event: self.on_close())

    def on_close(self):
        """Vérifie si la palette a été sauvegardée avant de fermer la fenêtre."""
        if self.is_processing:
            messagebox.showwarning("Fermeture", "Le calcul est en cours. Impossible de fermer la fenêtre.")
        else:
            self.window.destroy()

    def create_widgets(self):
        # Fichier d'extraction
        Label(self.window, text="Fichier d'extraction", font=("Arial", 12, "bold"), bg=BG_1).grid(row=0, column=0, padx=10,
                                                                                         pady=10, sticky="w")
        Entry(self.window, textvariable=self.fichier_extraction, width=30, relief="solid",highlightbackground=BG_1).grid(row=0, column=1,
                                                                                                padx=10, pady=10)
        Button(self.window, text="Parcourir", command=self.browse_extraction_file, width=15, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=0, column=2, padx=10, pady=10)

        # Fichier palette
        Label(self.window, text="Fichier palette", font=("Arial", 12, "bold"), bg=BG_1).grid(row=1, column=0, padx=10, pady=10,
                                                                                    sticky="w")
        Entry(self.window, textvariable=self.fichier_palette, width=30, relief="solid", highlightbackground=BG_1).grid(row=1, column=1, padx=10,
                                                                                             pady=10)
        Button(self.window, text="Parcourir", command=self.browse_palette_file, width=15, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=1, column=2, padx=10, pady=10)
        # Dosier sortie
        Label(self.window, text="Dossier sortie", font=("Arial", 12, "bold"), bg=BG_1).grid(row=2, column=0, padx=10, pady=10,
                                                                                    sticky="w")
        Entry(self.window, textvariable=self.dossier_sortie, width=30, relief="solid", highlightbackground=BG_1).grid(row=2, column=1, padx=10,
                                                                                             pady=10)
        Button(self.window, text="Parcourir", command=self.browse_folder, width=15, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=2, column=2, padx=10, pady=10)
        # Fichier de sortie image (palette)
        Label(self.window, text="Nom Fichier sortie Image Palette", font=("Arial", 12, "bold"), bg=BG_1).grid(row=3, column=0,
                                                                                                 padx=10, pady=10, sticky="w")
        Entry(self.window, textvariable=self.fichier_sortie_image_palette, width=30, relief="solid", highlightbackground=BG_1).grid(row=3,
                                                                                                          column=1, padx=10, pady=10)

        # Fichier de sortie image (CSV)
        Label(self.window, text="Nom Fichier sortie Nuage de Points", font=("Arial", 12, "bold"), bg=BG_1).grid(row=4, column=0, padx=10,
                                                                                             pady=10, sticky="w")
        Entry(self.window, textvariable=self.fichier_sortie_image_csv, width=30, relief="solid", highlightbackground=BG_1).grid(row=4, column=1,
                                                                                                      padx=10, pady=10)

        # Fichier de sortie CSV
        Label(self.window, text="Nom Fichier sortie CSV", font=("Arial", 12, "bold"), bg=BG_1).grid(row=5, column=0, padx=10,
                                                                                       pady=10, sticky="w")
        Entry(self.window, textvariable=self.fichier_sortie_csv, width=30, relief="solid", highlightbackground=BG_1).grid(row=5, column=1,
                                                                                                padx=10, pady=10)

        # Nombre de points d'interpolation
        Label(self.window, text="Nombre de points d'interpolation de la palette", font=("Arial", 12, "bold"), bg=BG_1).grid(row=6, column=0,
                                                                                                     padx=10, pady=10,
                                                                                                     sticky="w")
        Entry(self.window, textvariable=self.n_points_interpolation, width=10, relief="solid", highlightbackground=BG_1).grid(row=6, column=1,
                                                                                                    padx=10, pady=10)

        # Nombre de ticks Y
        Label(self.window, text="Nombre d'étiquettes pour la palette", font=("Arial", 12, "bold"), bg=BG_1).grid(row=7, column=0, padx=10, pady=10,
                                                                                      sticky="w")
        Entry(self.window, textvariable=self.n_ticks_yticks, width=10, relief="solid", highlightbackground=BG_1).grid(row=7, column=1, padx=10,
                                                                                            pady=10)

        # Seuil distance couleur
        Label(self.window, text="Seuil du filtre des couleurs hors de la palette", font=("Arial", 12, "bold"), bg=BG_1).grid(row=8, column=0, padx=10,
                                                                                           pady=10, sticky="w")
        Entry(self.window, textvariable=self.seuil_distance_couleur, width=10, relief="solid", highlightbackground=BG_1).grid(row=8, column=1,
                                                                                                    padx=10, pady=10)

        # Indices des colonnes dans un frame avec columnspan=5
        self.frame_indices = Frame(self.window, bg=BG_2, relief="solid", bd=2)
        self.frame_indices.grid(row=9, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        self.label_colonnes = Label(self.frame_indices, text="", bg=BG_2)

        # Indices X, Y, R, G, B sur la même ligne
        Label(self.frame_indices, text="Index X", font=("Arial", 12, "bold"), bg=BG_2).grid(row=0, column=0, padx=5, pady=5,
                                                                                       sticky="w")
        Entry(self.frame_indices, textvariable=self.colonne_X, width=10, relief="solid", highlightbackground=BG_2).grid(row=1, column=0, padx=5,
                                                                                         pady=5)

        Label(self.frame_indices, text="Index Y", font=("Arial", 12, "bold"), bg=BG_2).grid(row=0, column=1, padx=5, pady=5,
                                                                                       sticky="w")
        Entry(self.frame_indices, textvariable=self.colonne_Y, width=10, relief="solid", highlightbackground=BG_2).grid(row=1, column=1, padx=5,
                                                                                         pady=5)

        Label(self.frame_indices, text="Index R", font=("Arial", 12, "bold"), bg=BG_2).grid(row=0, column=2, padx=5, pady=5,
                                                                                       sticky="w")
        Entry(self.frame_indices, textvariable=self.colonne_R, width=10, relief="solid", highlightbackground=BG_2).grid(row=1, column=2, padx=5,
                                                                                         pady=5)

        Label(self.frame_indices, text="Index G", font=("Arial", 12, "bold"), bg=BG_2).grid(row=0, column=3, padx=5, pady=5,
                                                                                       sticky="w")
        Entry(self.frame_indices, textvariable=self.colonne_G, width=10, relief="solid", highlightbackground=BG_2).grid(row=1, column=3, padx=5,
                                                                                         pady=5)

        Label(self.frame_indices, text="Index B", font=("Arial", 12, "bold"), bg=BG_2).grid(row=0, column=4, padx=5, pady=5,
                                                                                       sticky="w")
        Entry(self.frame_indices, textvariable=self.colonne_B, width=10, relief="solid", highlightbackground=BG_2).grid(row=1, column=4, padx=5,
                                                                                         pady=5)

        # Si un fichier d'extraction est chargé, afficher les colonnes et leurs indices
        if self.fichier_extraction.get():  # Vérifiez si un fichier a été chargé
            # Cette partie suppose que le fichier est chargé et contient des données
            self.show_column_names_and_indices()

        # Indices des colonnes dans un frame avec columnspan=5
        self.frame_noms = Frame(self.window, bg=BG_2, relief="solid", bd=2)
        self.frame_noms.grid(row=10, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        Label(self.frame_noms, text="Nom X", font=("Arial", 12, "bold"), bg=BG_2).grid(row=0, column=0, padx=5,
                                                                                            pady=5,
                                                                                            sticky="w")
        Entry(self.frame_noms, textvariable=self.nom_X, width=10, relief="solid", highlightbackground=BG_2).grid(
            row=1, column=0, padx=5,
            pady=5)

        Label(self.frame_noms, text="Nom Y", font=("Arial", 12, "bold"), bg=BG_2).grid(row=0, column=1, padx=5,
                                                                                            pady=5,
                                                                                            sticky="w")
        Entry(self.frame_noms, textvariable=self.nom_Y, width=10, relief="solid", highlightbackground=BG_2).grid(
            row=1, column=1, padx=5,
            pady=5)

        Label(self.frame_noms, text="Nom Z", font=("Arial", 12, "bold"), bg=BG_2).grid(row=0, column=2, padx=5,
                                                                                            pady=5,
                                                                                            sticky="w")
        Entry(self.frame_noms, textvariable=self.nom_Z, width=10, relief="solid", highlightbackground=BG_2).grid(
            row=1, column=2, padx=5,pady=5)

            # Bouton de traitement
        Button(self.window, text="Charger les param.", command=self.load_parameters, width=20, height=2, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=11, column=0, padx=10, pady=20)
        Button(self.window, text="Sauvegarder les param.", command=self.save_parameters, width=20, height=2, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=11, column=1, padx=10, pady=20)
        Button(self.window, text="Lancer le traitement", command=self.process, width=20, height=2, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=11, column=2, padx=10, pady=20)

    def save_parameters(self):
        """Sauvegarde les paramètres dans un fichier JSON."""
        params = {
            "fichier_extraction": self.fichier_extraction.get(),
            "fichier_palette": self.fichier_palette.get(),
            "dossier_sortie": self.dossier_sortie.get(),
            "fichier_sortie_image_palette": self.fichier_sortie_image_palette.get(),
            "fichier_sortie_image_csv": self.fichier_sortie_image_csv.get(),
            "fichier_sortie_csv": self.fichier_sortie_csv.get(),
            "n_points_interpolation": self.n_points_interpolation.get(),
            "n_ticks_yticks": self.n_ticks_yticks.get(),
            "seuil_distance_couleur": self.seuil_distance_couleur.get(),
            "colonne_X": self.colonne_X.get(),
            "colonne_Y": self.colonne_Y.get(),
            "colonne_R": self.colonne_R.get(),
            "colonne_G": self.colonne_G.get(),
            "colonne_B": self.colonne_B.get(),
            "nom_X": self.nom_X.get(),
            "nom_Y": self.nom_Y.get(),
            "nom_Z": self.nom_Z.get()
        }
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
                self.fichier_extraction.set(params.get("fichier_extraction", ""))
                self.fichier_palette.set(params.get("fichier_palette", ""))
                self.dossier_sortie.set(params.get("dossier_sortie", ""))
                self.fichier_sortie_image_palette.set(params.get("fichier_sortie_image_palette", "Palette_interpolée"))
                self.fichier_sortie_image_csv.set(params.get("fichier_sortie_image_csv", "Nuage_points"))
                self.fichier_sortie_csv.set(params.get("fichier_sortie_csv", "Extraction_convertie"))
                self.n_points_interpolation.set(params.get("n_points_interpolation", "1000"))
                self.n_ticks_yticks.set(params.get("n_ticks_yticks", "10"))
                self.seuil_distance_couleur.set(params.get("seuil_distance_couleur", "80"))
                self.colonne_X.set(params.get("colonne_X", "0"))
                self.colonne_Y.set(params.get("colonne_Y", "1"))
                self.colonne_R.set(params.get("colonne_R", "2"))
                self.colonne_G.set(params.get("colonne_G", "3"))
                self.colonne_B.set(params.get("colonne_B", "4"))
                self.nom_X.set(params.get("nom_X","X"))
                self.nom_Y.set(params.get("nom_Y","Y"))
                self.nom_Z.set(params.get("nom_Z","Z"))
            messagebox.showinfo("Chargement", "Paramètres chargés avec succès.")
            self.show_column_names_and_indices()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des paramètres : {e}")

    def show_column_names_and_indices(self):
        # Charger les noms de colonnes du fichier d'extraction
        file_path = self.fichier_extraction.get()

        if file_path:
            try:
                self.label_colonnes.destroy()
                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    # Lire la première ligne du fichier CSV pour obtenir les noms des colonnes
                    headers = next(reader)

                # Créer un texte avec les noms des colonnes et leur indice
                column_names_text = "\t".join(f"{name}: {index}" for index, name in enumerate(headers))


                # Ajouter l'affichage des noms des colonnes et de leurs indices sous les entrées d'indices
                Label(self.frame_indices, text="Colonnes et Index du Fichier Extraction :",
                      font=("Arial", 12, "bold"), bg=BG_2).grid(row=2, column=0, columnspan=5)
                self.label_colonnes = Label(self.frame_indices, text=column_names_text, font=("Arial", 12), bg=BG_2)
                self.label_colonnes.grid(row=3, column=0, columnspan=5)
            except Exception as e:
                # Si une erreur se produit, afficher un message d'erreur
                self.label_colonnes.destroy()
                self.label_colonnes = Label(self.frame_indices, text=f"Erreur lors de la lecture du fichier: {e}", font=("Arial", 12, "bold"),
                      fg="red", bg=BG_2)
                self.label_colonnes.grid(row=2, column=0, columnspan=5)

    def browse_extraction_file(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            self.fichier_extraction.set(filename)
            self.show_column_names_and_indices()

    def browse_palette_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if filename:
            self.fichier_palette.set(filename)

    def browse_folder(self):
        # Ouvre la boîte de dialogue pour sélectionner un dossier
        dossier = filedialog.askdirectory(title="Sélectionner un dossier de sortie")

        # Vérifie si un dossier a été sélectionné
        if dossier:
            # Mise à jour de la variable StringVar avec le chemin du dossier sélectionné
            self.dossier_sortie.set(dossier)

    def update_progress(self, current, total, elapsed_time=None):
        # Mettre à jour la barre de progression
        self.progress['value'] = (current / total) * 100

        # Calculer le temps restant si le temps écoulé est disponible
        if elapsed_time:
            time_per_row = elapsed_time / current
            remaining_time = time_per_row * (total - current)
            remaining_minutes = remaining_time // 60
            remaining_seconds = remaining_time % 60
            self.progress_label.config(text=f"Ligne {current}/{total} ({self.progress['value']:.2f}%) - "
                                            f"Temps restant: {int(remaining_minutes)}m {int(remaining_seconds)}s")
        else:
            self.progress_label.config(text=f"Ligne {current}/{total} ({self.progress['value']:.2f}%)")

        if current == total and elapsed_time:
            total_minutes = elapsed_time // 60
            total_seconds = elapsed_time % 60
            self.is_processing = False
            self.progress_label.config(text=f"Calcul terminé en {int(total_minutes)}m {int(total_seconds)}s")

    def start_thread(self, df_filtre):
        # Lancer le long calcul dans un thread séparé
        thread = threading.Thread(target=self.long_calcul, args=(df_filtre,))
        thread.start()

    def long_calcul(self, df_filtre):
        total_rows = len(df_filtre)
        start_time = time.time()  # Enregistrer l'heure de départ

        # Appliquer la fonction pour chaque ligne et calculer 'Z' et 'distance'
        def update_progress_in_lambda(row_idx):
            elapsed_time = time.time() - start_time  # Calculer le temps écoulé
            self.update_progress(row_idx + 1, total_rows, elapsed_time)  # mettre à jour la barre de progression

        df_sortie = df_filtre.iloc[:, [int(self.colonne_X.get()), int(self.colonne_Y.get())]].copy()

        # Appliquer la fonction pour chaque ligne et calculer 'Z' et 'distance'
        df_sortie[['Z', 'distance']] = df_filtre.apply(
            lambda row: match_color_to_value(
                row.iloc[int(self.colonne_R.get())], row.iloc[int(self.colonne_G.get())], row.iloc[int(self.colonne_B.get())],
                self.interp_palette, update_progress_in_lambda(row.name)
            ),
            axis=1, result_type='expand', raw=False
        )

        # Filtrer les résultats en fonction du seuil de distance
        df_sortie = df_sortie[df_sortie['distance'] <= float(self.seuil_distance_couleur.get())]
        df_sortie = df_sortie.drop(columns=['distance'])
        df_sortie.columns = [self.nom_X.get(), self.nom_Y.get(), self.nom_Z.get()]

        self.queue.put(df_sortie)
        df_sortie.to_csv(os.path.join(self.dossier_sortie.get(),self.fichier_sortie_csv.get()  + ".csv"), index=False)
        self.window.after(1000, self.check_for_updates)


    def check_for_updates(self):
        try:
            df_sortie = self.queue.get_nowait()
            # Sauvegarder la figure une fois que l'interpolation est terminée
            plot_scatter(df_sortie, self.nom_X.get(), self.nom_Y.get(), self.nom_Z.get(), self.interp_palette, os.path.join(self.dossier_sortie.get(), self.fichier_sortie_image_csv.get()  + ".png"))
        except queue.Empty:
            # Pas encore de mise à jour, vérifier à nouveau
            self.window.after(1000, self.check_for_updates)

    def process(self):
        if self.is_processing:
            return  # Ne pas démarrer un traitement si déjà en cours

        # Vérification des fichiers
        if not self.fichier_extraction.get() or not os.path.exists(self.fichier_extraction.get()):
            messagebox.showerror("Erreur", "Le fichier d'extraction n'existe pas.")
            return
        if not self.fichier_palette.get() or not os.path.exists(self.fichier_palette.get()):
            messagebox.showerror("Erreur", "Le fichier de palette n'existe pas.")
            return

        # Récupérer les valeurs des fichiers de sortie et autres paramètres
        fichier_extraction = self.fichier_extraction.get()
        fichier_palette = self.fichier_palette.get()

        # Vérification des paramètres n_points_interpolation et n_ticks_yticks
        n_points_interpolation_str = self.n_points_interpolation.get()  # Valeur sous forme de chaîne
        if not n_points_interpolation_str.isdigit() or int(n_points_interpolation_str) < 0:
            messagebox.showerror("Erreur", "Nombre de points d'interpolation de la palette doit être un entier positif.")
            return
        n_points_interpolation = int(n_points_interpolation_str)  # Convertir en entier

        n_ticks_yticks_str = self.n_ticks_yticks.get()  # Valeur sous forme de chaîne
        if not n_ticks_yticks_str.isdigit() or int(n_ticks_yticks_str) <= 0:
            messagebox.showerror("Erreur", "Nombre d'étiquettes pour la palette doit être un entier positif.")
            return
        n_ticks_yticks = int(n_ticks_yticks_str)  # Convertir en entier

        # Vérification du seuil_distance_couleur
        seuil_distance_couleur_str = self.seuil_distance_couleur.get()  # Valeur sous forme de chaîne
        try:
            seuil_distance_couleur = float(seuil_distance_couleur_str)
            if seuil_distance_couleur < 0:
                raise ValueError("seuil_distance_couleur doit être un float positif.")
        except ValueError:
            messagebox.showerror("Erreur", "Seuil du filtre des couleurs hors de la palette doit être un float positif.")
            return

        # Vérification des indices des colonnes
        try:
            df = pd.read_csv(fichier_extraction)  # Chargement du fichier d'extraction
            col_X, col_Y, col_R, col_G, col_B = self.colonne_X.get(), self.colonne_Y.get(), self.colonne_R.get(), self.colonne_G.get(), self.colonne_B.get()
            try:
                col_X = int(col_X)
                col_Y = int(col_Y)
                col_R = int(col_R)
                col_G = int(col_G)
                col_B = int(col_B)
            except ValueError:
                messagebox.showerror("Erreur", "Les indices des colonnes doivent être des entiers.")
                return
            # Vérifier que les colonnes spécifiées existent dans le DataFrame
            for col_index in [col_X, col_Y, col_R, col_G, col_B]:
                if int(col_index) >= len(df.columns):
                    raise ValueError(
                        f"Indice de colonne {col_index} invalide. Le fichier ne contient pas autant de colonnes.")

        except ValueError as e:
            messagebox.showerror("Erreur", f"Erreur dans les indices de colonnes : {e}")
            return

        self.is_processing = True

        # Charger les fichiers
        df = pd.read_csv(fichier_extraction)  # Chargement du fichier d'extraction
        ref_palette = load_reference_palette(fichier_palette)  # Chargement de la palette de référence

        progress_window = Toplevel(self.window)
        progress_window.title("Progression de l'interpolation")

        # Créer la barre de progression
        self.progress = Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=0, column=0, padx=10)

        # Créer un label pour afficher la progression avec des informations supplémentaires
        self.progress_label = Label(progress_window, text="Ligne 0/0 (0%)", font=("Arial", 10))
        self.progress_label.grid(row=1, column=0, padx=10, pady=10)

        # Ajouter la protection pour la fermeture de la fenêtre de progression
        def on_progress_window_close():
            if self.is_processing:
                messagebox.showwarning("Fermeture", "Le calcul est en cours. Impossible de fermer la fenêtre.")
            else:
                progress_window.destroy()

        progress_window.protocol("WM_DELETE_WINDOW", on_progress_window_close)

        # === Créer une palette interpolée avec le nombre de points spécifié ===
        self.interp_palette = interpolate_palette(ref_palette, n_points_interpolation)

        # === Tracer la palette interpolée verticalement ===
        plot_palette_vertical(self.interp_palette, os.path.join(self.dossier_sortie.get(), self.fichier_sortie_image_palette.get() + ".png"), n_ticks_yticks)

        # === Filtrer le tableau en supprimant les lignes à 0 ou NaN ===
        filtre = False
        if filtre:
            df_filtre = df.loc[~(
                    ((df.iloc[:, col_R] == 255) & (df.iloc[:, col_G] == 255) & (df.iloc[:, col_B] == 255)) |  # Supprimer les lignes (255, 255, 255)
                    ((df.iloc[:, col_R] == 0) & (df.iloc[:, col_G] == 0) & (df.iloc[:, col_B] == 0)) |  # Supprimer les lignes (0, 0, 0)
                    (pd.isna(df.iloc[:, col_R]) | pd.isna(df.iloc[:, col_G]) | pd.isna(df.iloc[:, col_B]))
            # Supprimer les lignes avec NaN
            )].reset_index(drop=True)
        else:
            df_filtre= df

        # === Associer la valeur interpolée aux couleurs ===
        self.start_thread(df_filtre)




