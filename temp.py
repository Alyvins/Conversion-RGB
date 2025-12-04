import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# --- Charger le CSV généré ---
df = pd.read_csv("positions_with_values.csv")  # colonnes Longitude (°), Latitude (°), Composition, Nom

# --- Palette fournie (Valeur, R, G, B) ---
palette_data = [
    (0.0, 0, 0, 0),
    (1.0, 253, 153, 53),
    (2.0, 253, 212, 69),
    (3.0, 251, 254, 81),
    (4.0, 11, 249, 105),
    (5.0, 40, 174, 249),
    (6.0, 52, 20, 245),
]

# Création d'une colormap à partir de la palette
values, r, g, b = zip(*palette_data)
colors = np.array([ [ri, gi, bi] for ri, gi, bi in zip(r, g, b) ]) / 255.0
cmap = mcolors.ListedColormap(colors)

# Associer les valeurs numériques aux étiquettes (optionnel pour la légende)
value_to_label = {
    0: "Roche",
    1: "Gravier sableux",
    2: "Sable graveleux",
    3: "Sable",
    4: "Sable boueux",
    5: "Boue sableuse",
    6: "Boue"
}

# Créer une colonne numérique correspondant à la valeur
df["Code"] = df["Composition"].map({v:k for k,v in value_to_label.items()})

# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 8))
scatter = ax.scatter(df["Longitude (°)"], df["Latitude (°)"], c=df["Code"], cmap=cmap, s=20, edgecolors='k')

# --- Colorbar ---
cbar = plt.colorbar(scatter, ax=ax, ticks=range(7))
cbar.ax.set_yticklabels([value_to_label[i] for i in range(7)])
cbar.set_label("Composition", fontsize=12)

ax.set_xlabel("Longitude (°)", fontsize=12)
ax.set_ylabel("Latitude (°)", fontsize=12)
ax.set_title("Carte des compositions", fontsize=14)
ax.set_aspect('equal')

plt.tight_layout()
plt.show()
