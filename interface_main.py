"""
Script python créé par S. ROULLET
Dernière modification le 28/03/2025

Ce script contient les fonctions pour le lancement de l'application Conversion RGB
"""

from tkinter import *
from tkinter import messagebox
from interface_palette import ColorPaletteWindow  # Importer la fenêtre de palette
from interface_extraction import ExtractionWindow  # Importer la fenêtre d'extraction
from interface_conversion import ConversionWindow  # Importer la fenêtre de conversion
from interface_tif import TifWindow

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

class Main:
    def __init__(self):
        self.ui = Tk()
        self.ui.title("Outil : Conversion Couleur - Valeur")
        self.ui.config(bg=BG_1)

        self.create_menu()
        self.create_buttons()

        self.ui.mainloop()

    def create_menu(self):
        """Crée la barre de menu."""
        self.menu = Menu(self.ui)
        self.ui.config(menu=self.menu)

        window_menu = Menu(self.menu, tearoff=0)
        window_menu.add_command(label="Extraction des Couleurs", command=self.open_extraction_window, accelerator="Ctrl+E")
        window_menu.add_command(label="Palette de Couleurs", command=self.open_palette_window, accelerator="Ctrl+P")
        window_menu.add_command(label="Conversion en Valeurs", command=self.open_conversion_window, accelerator="Ctrl+C")
        window_menu.add_command(label="Création d'un Tif", command=self.open_tif_window, accelerator="Ctrl+T")
        window_menu.add_separator()
        window_menu.add_command(label="Quitter", command=self.ui.destroy, accelerator="Ctrl+Q")
        self.menu.add_cascade(label="Fenêtre", menu=window_menu)

        # Définir les raccourcis clavier
        self.ui.bind_all("<Control-e>", lambda event: self.open_extraction_window())  # Ctrl+E pour Extraction
        self.ui.bind_all("<Control-p>", lambda event: self.open_palette_window())     # Ctrl+P pour Palette
        self.ui.bind_all("<Control-c>", lambda event: self.open_conversion_window())  # Ctrl+C pour Conversion
        self.ui.bind_all("<Control-t>", lambda event: self.open_tif_window())  # Ctrl+C pour Conversion
        self.ui.bind_all("<Control-q>", lambda event: self.ui.destroy())  # Ctrl+C pour Conversion

        aide_menu = Menu(self.menu, tearoff=0)
        aide_menu.add_command(label="Crédits", command=show_credits)
        self.menu.add_cascade(label="Aide", menu=aide_menu)

    def create_buttons(self):
        """Crée les boutons pour chaque option."""
        info_label = Label(self.ui,text="Sélectionnez une fonctionnalité pour commencer", font=("Arial", 15, "bold"), bg=BG_2)
        info_label.grid(row=0, column=0, pady=10, padx=10, sticky="nswe")
        button_extraction = Button(self.ui, text="Extraire les couleurs d'une image", command=self.open_extraction_window, width=20, height=2, relief="solid", bg=BG_1, highlightbackground=BG_1, highlightcolor=FG)
        button_extraction.grid(row=1, column=0, pady=10, padx=10, sticky="nswe")

        button_palette = Button(self.ui, text="Créer la palette de couleurs correspondante", command=self.open_palette_window, width=20, height=2, relief="solid", bg=BG_1, highlightbackground=BG_1, highlightcolor=FG)
        button_palette.grid(row=2, column=0, pady=10, padx=10, sticky="nswe")

        button_conversion = Button(self.ui, text="Convertir les couleurs en valeurs", command=self.open_conversion_window, width=20, height=2, relief="solid", bg=BG_1, highlightbackground=BG_1, highlightcolor=FG)
        button_conversion.grid(row=3, column=0, pady=10, padx=10, sticky="nswe")

        button_conversion = Button(self.ui, text="Créer un TIF depuis le CSV", command=self.open_tif_window, width=20, height=2, relief="solid", bg=BG_1, highlightbackground=BG_1, highlightcolor=FG)
        button_conversion.grid(row=4, column=0, pady=10, padx=10, sticky="nswe")

    def open_palette_window(self):
        """Ouvre la fenêtre de la palette de couleurs."""
        ColorPaletteWindow(self.ui)

    def open_extraction_window(self):
        """Ouvre la fenêtre d'extraction."""
        ExtractionWindow(self.ui)

    def open_conversion_window(self):
        """Ouvre la fenêtre de conversion."""
        ConversionWindow(self.ui)

    def open_tif_window(self):
        TifWindow(self.ui)

if __name__ == "__main__":
    Main()
