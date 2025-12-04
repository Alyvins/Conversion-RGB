import pandas as pd
from sklearn.neighbors import NearestNeighbors

# Distance maximale (en degrés GPS) pour considérer deux points comme voisins
# 0.0003 ≈ 30 mètres
DIST_MAX = 0.00095

# Charger CSV
df = pd.read_csv('/Users/sylvain/Desktop/These/Etude Sédimentaire/Sources/MDN/liste_points.csv')

coords = df[["X", "Y"]].values

# Construire graphe de voisinage
nbrs = NearestNeighbors(radius=DIST_MAX).fit(coords)
distances, indices = nbrs.radius_neighbors(coords)

# --- Trouver les groupes de points connectés ---
visited = set()
groups = []

for i in range(len(coords)):
    if i in visited:
        continue

    stack = [i]
    group = []

    while stack:
        p = stack.pop()
        if p in visited:
            continue
        visited.add(p)
        group.append(p)

        # Ajouter ses voisins dans la pile
        for neigh in indices[p]:
            if neigh not in visited:
                stack.append(neigh)

    groups.append(group)

# --- Calcul du centre pour chaque groupe ---
merged_points = []

for group in groups:
    if len(group) == 1:
        # garder tel quel
        p = df.iloc[group[0]]
        merged_points.append([p.X, p.Y, p.Z])
        continue

    # points à fusionner
    subset = df.iloc[group]

    # centre moyen
    Xc = subset["X"].mean()
    Yc = subset["Y"].mean()
    Zc = subset["Z"].mean()

    merged_points.append([Xc, Yc, Zc])

# --- Export final ---
result = pd.DataFrame(merged_points, columns=["X", "Y", "Z"])
result.to_csv("points_fusionnes.csv", index=False)

print(f"Nombre de points d'origine : {len(df)}")
print(f"Nombre de points après fusion : {len(result)}")
