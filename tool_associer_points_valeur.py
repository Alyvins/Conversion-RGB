import pandas as pd
from sklearn.neighbors import NearestNeighbors

# --- Charger les CSV ---
positions = pd.read_csv('/Users/sylvain/Desktop/These/Etude Sédimentaire/Sources/MDN/Résultats/points_fusionnes.csv')  # colonnes X,Y,Z
values = pd.read_csv('/Users/sylvain/Desktop/These/Etude Sédimentaire/Sources/MDN/Résultats/points_couleur.csv')        # colonnes X,Y,Z

# --- Ne garder que X,Y pour les positions ---
pos_coords = positions[["X","Y"]].values
val_coords = values[["X","Y"]].values
val_z = values["Z"].values

# --- Trouver le voisin le plus proche ---
nbrs = NearestNeighbors(n_neighbors=1).fit(val_coords)
distances, indices = nbrs.kneighbors(pos_coords)

# --- Associer les valeurs Z correspondantes ---
closest_z = val_z[indices.flatten()]

# --- Remplacer par les étiquettes ---
labels_dict = {
    0: "Roche",
    1: "Gravier sableux",
    2: "Sable graveleux",
    3: "Sable",
    4: "Sable boueux",
    5: "Boue sableuse",
    6: "Boue"
}

labeled_values = [labels_dict[int(z)] for z in closest_z]

# --- Créer le DataFrame de sortie ---
output_df = positions.copy()
output_df["Composition"] = labeled_values
output_df["Nom"] = [f"SP-2007-{i+1}" for i in range(len(output_df))]

output_df = output_df.drop(columns=["Z"])  # drop Z initial
output_df = output_df.rename(columns={"X": "Longitude (°)", "Y": "Latitude (°)"})

# --- Sauvegarder en CSV ---
output_df.to_csv("positions_with_values.csv", index=False)

print("Fichier créé : positions_with_values.csv")
print(output_df.head())
