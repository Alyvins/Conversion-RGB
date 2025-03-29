"""
Script python créé par S. ROULLET
Dernière modification le 28/03/2025

Ce script contient les fonctions pour la fenêtre de création d'un tif.
"""

import numpy as np
import pandas as pd
import os
import rasterio
from rasterio.transform import from_origin
from scipy.interpolate import griddata
import json
import csv
from tkinter import *
from tkinter import filedialog, messagebox

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

class TifWindow:
    def __init__(self, root):
        self.window = Toplevel(root)
        self.window.title("Création d'un Tif")
        self.window.config(bg=BG_1)

        # Variables de configuration
        self.fichier_extraction = StringVar()

        self.grid_res_x = StringVar(value="5000")
        self.grid_res_y = StringVar(value="5000")
        self.epsg = StringVar(value="32198")

        self.nom_X = StringVar(value="X")
        self.nom_Y = StringVar(value="Y")
        self.nom_Z = StringVar(value="Z")

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
        file_menu.add_separator()
        file_menu.add_command(label="Charger Paramètres", command=self.load_parameters, accelerator="Ctrl+L")
        file_menu.add_command(label="Sauvegarder Paramètres", command=self.save_parameters, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.on_close, accelerator="Ctrl+Q")

        self.menu.add_cascade(label="Créer un Tif", menu=file_menu)

        aide_menu = Menu(self.menu, tearoff=0)
        aide_menu.add_command(label="Crédits", command=show_credits)
        self.menu.add_cascade(label="Aide", menu=aide_menu)

        # Ajout des raccourcis clavier
        self.window.bind_all("<Control-e>", lambda event: self.browse_extraction_file())
        self.window.bind_all("<Control-s>", lambda event: self.save_parameters())
        self.window.bind_all("<Control-l>", lambda event: self.load_parameters())
        self.window.bind_all("<Control-q>", lambda event: self.on_close())

    def on_close(self):
        """Vérifie si la palette a été sauvegardée avant de fermer la fenêtre."""
        self.window.destroy()

    def create_widgets(self):
        # Fichier d'extraction
        Label(self.window, text="Fichier CSV", font=("Arial", 12, "bold"), bg=BG_1).grid(row=0, column=0, padx=10,
                                                                                         pady=10, sticky="w")
        Entry(self.window, textvariable=self.fichier_extraction, width=30, relief="solid",highlightbackground=BG_1).grid(row=0, column=1,
                                                                                                padx=10, pady=10)
        Button(self.window, text="Parcourir", command=self.browse_extraction_file, width=15, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=0, column=2, padx=10, pady=10)

        # Nombre de points d'interpolation
        Label(self.window, text="Résolution de sortie en X", font=("Arial", 12, "bold"), bg=BG_1).grid(row=1, column=0,
                                                                                                     padx=10, pady=10,
                                                                                                     sticky="w")
        Entry(self.window, textvariable=self.grid_res_x, width=10, relief="solid", highlightbackground=BG_1).grid(row=1, column=1,
                                                                                                    padx=10, pady=10)
        Label(self.window, text="Résolution de sortie en Y", font=("Arial", 12, "bold"), bg=BG_1).grid(row=2, column=0,
                                                                                                     padx=10, pady=10,
                                                                                                     sticky="w")
        Entry(self.window, textvariable=self.grid_res_y, width=10, relief="solid", highlightbackground=BG_1).grid(row=2, column=1,
                                                                                                    padx=10, pady=10)

        # Nombre de ticks Y
        Label(self.window, text="EPSG", font=("Arial", 12, "bold"), bg=BG_1).grid(row=3, column=0, padx=10, pady=10,
                                                                                      sticky="w")
        Entry(self.window, textvariable=self.epsg, width=10, relief="solid", highlightbackground=BG_1).grid(row=3, column=1, padx=10,
                                                                                            pady=10)


        # Indices des colonnes dans un frame avec columnspan=5
        self.frame_noms = Frame(self.window, bg=BG_2, relief="solid", bd=2)
        self.frame_noms.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        self.label_colonnes = Label(self.frame_noms, text="", bg=BG_2)

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

        # Si un fichier d'extraction est chargé, afficher les colonnes et leurs indices
        if self.fichier_extraction.get():  # Vérifiez si un fichier a été chargé
            # Cette partie suppose que le fichier est chargé et contient des données
            self.show_column_names_and_indices()

            # Bouton de traitement
        Button(self.window, text="Charger les param.", command=self.load_parameters, width=20, height=2, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=5, column=0, padx=10, pady=20)
        Button(self.window, text="Sauvegarder les param.", command=self.save_parameters, width=20, height=2, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=5, column=1, padx=10, pady=20)
        Button(self.window, text="Lancer la conversion", command=self.process, width=20, height=2, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=5, column=2, padx=10, pady=20)

    def save_parameters(self):
        """Sauvegarde les paramètres dans un fichier JSON."""
        params = {
            "fichier_extraction": self.fichier_extraction.get(),
            "grid_res_x": self.grid_res_x.get(),
            "grid_res_y": self.grid_res_y.get(),
            "epsg": self.epsg.get(),
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
                self.grid_res_x.set(params.get("grid_res_x", "5000"))
                self.grid_res_y.set(params.get("grid_res_y", "5000"))
                self.epsg.set(params.get("epsg", "32198"))
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
                column_names_text = "\t".join(f"{index} : {name}" for index, name in enumerate(headers))


                # Ajouter l'affichage des noms des colonnes et de leurs indices sous les entrées d'indices
                Label(self.frame_noms, text="Colonnes et Index du Fichier Extraction :",
                      font=("Arial", 12, "bold"), bg=BG_2).grid(row=2, column=0, columnspan=5)
                self.label_colonnes = Label(self.frame_noms, text=column_names_text, font=("Arial", 12), bg=BG_2)
                self.label_colonnes.grid(row=3, column=0, columnspan=5)
            except Exception as e:
                # Si une erreur se produit, afficher un message d'erreur
                self.label_colonnes.destroy()
                self.label_colonnes = Label(self.frame_noms, text=f"Erreur lors de la lecture du fichier: {e}", font=("Arial", 12, "bold"),
                      fg="red", bg=BG_2)
                self.label_colonnes.grid(row=2, column=0, columnspan=5)

    def browse_extraction_file(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            self.fichier_extraction.set(filename)
            self.show_column_names_and_indices()

    def process(self):
        if not self.fichier_extraction.get() or not os.path.exists(self.fichier_extraction.get()):
            messagebox.showerror("Erreur", "Le fichier d'extraction n'existe pas.")
            return
        df = pd.read_csv(self.fichier_extraction.get())

        if not {self.nom_X.get(), self.nom_Y.get(), self.nom_Z.get()}.issubset(df.columns):
            messagebox.showwarning("Erreur", "Les colonnes n'ont pas été trouvées dans le CSV")

        x = df[self.nom_X.get()].values
        y = df[self.nom_Y.get()].values
        z = df[self.nom_Z.get()].values

        # Définir une grille régulière
        grid_x, grid_y = np.meshgrid(
            np.linspace(x.min(), x.max(), int(self.grid_res_x.get())),
            np.linspace(y.min(), y.max(), int(self.grid_res_y.get()))
        )

        # Interpoler les valeurs Z avec 'nearest' pour éviter les NaN
        grid_z = griddata((x, y), z, (grid_x, grid_y), method="linear")

        # Définir la transformation spatiale
        pixel_size_x = (x.max() - x.min()) / int(self.grid_res_x.get())
        pixel_size_y = (y.max() - y.min()) / int(self.grid_res_y.get())

        transform = from_origin(x.min(), y.min(), pixel_size_x, -pixel_size_y)

        # Enregistrer le raster en GeoTIFF avec EPSG:32198
        file_path = filedialog.asksaveasfilename(defaultextension=".tiff", filetypes=[("Fichiers tif", "*.tiff")])
        if file_path:
            with rasterio.open(
                    file_path, "w",
                    driver="GTiff",
                    height=grid_z.shape[0],
                    width=grid_z.shape[1],
                    count=1,
                    dtype=rasterio.float32,
                    crs=f"EPSG:{self.epsg.get()}",  # PROJECTION ICI
                    transform=transform
            ) as dst:
                dst.write(grid_z.astype(np.float32), 1)
            messagebox.showinfo("Succès", "Tif sauvegardé avec succès.")