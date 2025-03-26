"""
Script python créé par S. ROULLET
Dernière modification le 26/03/2025

Ce script contient les fonctions pour la fenêtre de création d'une palette.
"""

from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


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

class ColorPaletteWindow:
    def __init__(self, root):
        """Initialise la fenêtre de gestion de palette de couleurs."""
        self.master = root
        self.window = Toplevel(root)
        self.window.title("Palette des couleurs")
        self.window.config(bg=BG_1)

        # Variables de stockage
        self.image_path = None
        self.image = None
        self.tk_image = None
        self.selected_color = (0, 0, 0)
        self.colors = []
        self.is_saved = False
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_menu()
        self.create_widgets()

    def create_menu(self):
        # --- Menu ---
        self.menu = Menu(self.window)
        self.window.config(menu=self.menu)

        file_menu = Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Charger une image", command=self.load_image, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Charger une palette", command=self.load_palette, accelerator="Ctrl+L")
        file_menu.add_command(label="Sauvegarder la palette", command=self.save_palette, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.on_close, accelerator="Ctrl+Q")
        self.menu.add_cascade(label="Palette des couleurs", menu=file_menu)

        aide_menu = Menu(self.menu, tearoff=0)
        aide_menu.add_command(label="Crédits", command=show_credits)
        self.menu.add_cascade(label="Aide", menu=aide_menu)

        self.window.bind_all("<Control-o>", lambda event: self.load_image())
        self.window.bind_all("<Control-l>", lambda event: self.load_palette())
        self.window.bind_all("<Control-s>", lambda event: self.save_palette())
        self.window.bind_all("<Control-q>", lambda event: self.on_close())

    def create_widgets(self):
        # --- Interface graphique ---
        self.canvas = Canvas(self.window, width=400, height=580, bg="white", relief="solid", bd=2, highlightbackground=BG_1)
        self.canvas.grid(row=0, column=0, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.select_color)

        # Frame pour les éléments à droite
        frame_right = Frame(self.window, bg=BG_1)
        frame_right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)

        # Bouton de chargement d'image
        self.load_button = Button(frame_right, text="Charger une image", command=self.load_image, width=20, height=2,
                                  relief="solid", bg=BG_1, highlightbackground=BG_1, highlightcolor=FG)
        self.load_button.grid(row=0, column=0, padx=10, pady=10)

        # Cadre pour les entrées de couleur
        self.frame_entries = Frame(frame_right, relief="solid", bd=2, bg=BG_2)
        self.frame_entries.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        Label(self.frame_entries, text="Couleur sélectionnée :", font=("Arial", 14, "bold"), bg=BG_2).grid(row=0, column=0, columnspan=4, sticky="nsew")

        Label(self.frame_entries, text="Valeur", font=("Arial", 12, "bold"), bg=BG_2).grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        Label(self.frame_entries, text="R", font=("Arial", 12, "bold"), bg=BG_2).grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
        Label(self.frame_entries, text="G", font=("Arial", 12, "bold"), bg=BG_2).grid(row=1, column=2, padx=10, pady=5, sticky="nsew")
        Label(self.frame_entries, text="B", font=("Arial", 12, "bold"), bg=BG_2).grid(row=1, column=3, padx=10, pady=5, sticky="nsew")

        self.frame_entries.grid_columnconfigure(0, weight=1)
        self.frame_entries.grid_columnconfigure(1, weight=1)
        self.frame_entries.grid_columnconfigure(2, weight=1)
        self.frame_entries.grid_columnconfigure(3, weight=1)

        self.value_entry = Entry(self.frame_entries, width=10, relief="solid", highlightbackground=BG_2)
        self.value_entry.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        self.value_entry.insert(0, "0")

        self.rgb_entry_r = Entry(self.frame_entries, width=5, relief="solid", highlightbackground=BG_2)
        self.rgb_entry_g = Entry(self.frame_entries, width=5, relief="solid", highlightbackground=BG_2)
        self.rgb_entry_b = Entry(self.frame_entries, width=5, relief="solid", highlightbackground=BG_2)

        for i, entry in enumerate([self.rgb_entry_r, self.rgb_entry_g, self.rgb_entry_b]):
            entry.grid(row=2, column=i + 1, padx=5, pady=5, sticky="nsew")
            entry.insert(0, "0")

        # Bouton d'ajout de couleur
        self.add_button = Button(frame_right, text="Ajouter la couleur", command=self.add_color, width=20, height=2,
                                 relief="solid", bg=BG_1, highlightbackground=BG_1, highlightcolor=FG)
        self.add_button.grid(row=2, column=0, padx=10, pady=10)

        # Liste des couleurs
        self.color_listbox = Listbox(frame_right, height=15, relief="solid", bd=2, highlightbackground=BG_1)
        self.color_listbox.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Bouton de suppression
        self.delete_button = Button(frame_right, text="Supprimer la couleur", command=self.delete_color, width=20,
                                    height=2, relief="solid", bg=BG_1, highlightbackground=BG_1, highlightcolor=FG)
        self.delete_button.grid(row=4, column=0, padx=10, pady=5)

        # Boutons de sauvegarde/chargement
        frame = Frame(frame_right, padx=10, pady=10, bg=BG_1)
        frame.grid(row=5, column=0)

        Button(frame, text="Sauvegarder la palette", command=self.save_palette, width=20, height=2,
               relief="solid", bg=BG_1, highlightbackground=BG_1, highlightcolor=FG).grid(row=0, column=1, padx=10, pady=5)
        Button(frame, text="Charger une palette", command=self.load_palette, width=20, height=2, relief="solid", bg=BG_1,
               highlightbackground=BG_1, highlightcolor=FG).grid(row=0, column=0, padx=10, pady=5)

    def refresh_list(self):
        """Mise à jour de la liste des couleurs affichées."""
        # Supprimer les anciens éléments de la liste
        self.color_listbox.delete(0, END)

        # Trier la liste des couleurs (par nom de couleur ou par autre critère si nécessaire)
        self.colors.sort(key=lambda x: -float(x[0]))  # Trie par nom de couleur, mais peut être ajusté

        for color in self.colors:
            color_name = color[0]
            r, g, b = int(color[1]), int(color[2]), int(color[3])

            # Créer une chaîne pour afficher la couleur et ses valeurs RGB
            display_text = f"{color_name} -> RGB({r}, {g}, {b})"

            # Ajouter la couleur dans la Listbox avec un fond coloré correspondant
            self.color_listbox.insert(END, display_text)

            # Appliquer une couleur de fond correspondant à la couleur RGB (ajustée pour des contrastes lisibles)
            self.color_listbox.itemconfig(END, {'bg': f'#{r:02x}{g:02x}{b:02x}',
                                                'fg': 'white' if (r + g + b) < 382 else 'black'})


    def add_color(self):
        """Ajoute une couleur à la liste."""
        value = self.value_entry.get().strip()
        if not value:
            messagebox.showerror("Erreur", "Veuillez entrer une valeur.")
            return

        # Vérification si la valeur est un nombre
        try:
            # Tentative de conversion de la valeur en nombre
            float(value)
        except ValueError:
            # Si la conversion échoue, c'est que ce n'est pas un nombre
            messagebox.showerror("Erreur", "La valeur entrée doit être un nombre.")
            return

        if self.update_rgb():
            r, g, b = self.selected_color
            self.colors.append((value, r, g, b))
            self.refresh_list()

    def delete_color(self):
        """Supprime la couleur sélectionnée de la liste."""
        try:
            selected_index = self.color_listbox.curselection()[0]
            self.colors.pop(selected_index)
            self.refresh_list()
        except IndexError:
            messagebox.showerror("Erreur", "Aucune couleur sélectionnée dans la liste.")

    def load_image(self):
        """Charge une image et l'affiche sur le canvas."""
        file_path = filedialog.askopenfilename(filetypes=[("PNG", "*.png"), ("JPG", "*.jpg"), ("JPEG", "*.jpeg")])
        if file_path:
            self.image_path = file_path
            self.image = Image.open(file_path)
            self.image.thumbnail((400, 580))
            self.tk_image = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor=NW, image=self.tk_image)
            messagebox.showinfo("Succès", "Image chargée avec succès.")

    def select_color(self, event):
        """Sélectionne la couleur d'un pixel cliqué."""
        if self.image is None:
            response = messagebox.askyesno("Erreur", "Aucune image chargée. Voulez-vous en charger une maintenant ?")
            if response:  # Si l'utilisateur choisit 'Oui'
                self.load_image()  # Charge l'image
            return

        x, y = event.x, event.y
        if 0 <= x < self.image.width and 0 <= y < self.image.height:
            rgb = self.image.getpixel((x, y))[:3]
            self.selected_color = rgb
            self.update_entries(rgb)

    def update_entries(self, rgb):
        """Met à jour les champs de couleur avec les valeurs sélectionnées."""
        for entry, value in zip([self.rgb_entry_r, self.rgb_entry_g, self.rgb_entry_b], rgb):
            entry.delete(0, END)
            entry.insert(0, str(value))

    def update_rgb(self):
        """Met à jour la couleur sélectionnée à partir des entrées utilisateur."""
        try:
            r, g, b = (int(self.rgb_entry_r.get()), int(self.rgb_entry_g.get()), int(self.rgb_entry_b.get()))
            if all(0 <= v <= 255 for v in (r, g, b)):
                self.selected_color = (r, g, b)
                return True
        except ValueError:
            messagebox.showerror("Erreur", "Les valeurs RGB doivent être des nombres entre 0 et 255.")
            return False

    def save_palette(self):
        """Sauvegarde la palette dans un fichier texte avec un contrôle des valeurs."""
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Fichiers txt", "*.txt")])
        if file_path:
            try:
                with open(file_path, "w") as file:
                    for color in self.colors:
                        # Vérification des types avant la sauvegarde
                        file.write(f"{color[0]},{color[1]},{color[2]},{color[3]}\n")
                self.is_saved = True
                messagebox.showinfo("Succès", "Palette sauvegardée avec succès.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de la sauvegarde : {e}")

    def load_palette(self):
        """Charge une palette depuis un fichier texte avec une validation stricte des données."""
        file_path = filedialog.askopenfilename(filetypes=[("Fichiers txt", "*.txt")])
        if file_path:
            try:
                new_colors = []
                with open(file_path, "r") as file:
                    for line in file:
                        parts = line.strip().split(",")
                        if len(parts) != 4:
                            raise ValueError("Format incorrect (nombre de colonnes incorrect).")

                        # Vérification des types et des valeurs
                        try:
                            float_value = float(parts[0])
                        except ValueError:
                            raise ValueError(f"Valeur invalide pour le float : {parts[0]}.")

                            # Vérification des trois valeurs RGB (int entre 0 et 255)
                        try:
                            rgb_values = [int(parts[i]) for i in range(1, 4)]
                        except ValueError:
                            raise ValueError(f"Valeurs RGB invalides : {parts[1:]}. Doivent être des entiers.")

                        if not all(0 <= c <= 255 for c in rgb_values):
                            raise ValueError("Valeurs RGB hors plage (0-255).")

                        new_colors.append((float_value, rgb_values[0], rgb_values[1], rgb_values[2]))

                # Si toutes les données sont valides, on remplace la palette
                self.colors = new_colors
                self.refresh_list()
                messagebox.showinfo("Succès", "Palette chargée avec succès.")

            except ValueError as ve:
                messagebox.showerror("Erreur", f"Fichier invalide : {ve}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")

    def on_close(self):
        """Vérifie si la palette a été sauvegardée avant de fermer la fenêtre."""
        if not self.is_saved and len(self.colors) > 0:
            if messagebox.askyesno("Quitter",
                                   "La palette n'a pas été sauvegardée. Voulez-vous la sauvegarder avant de quitter ?"):
                self.save_palette()
        self.window.destroy()
