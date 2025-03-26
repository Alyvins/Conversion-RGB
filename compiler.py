from os import system
from os import getcwd

type_ordinateur = "Mac"
dossier_actuel = getcwd()
formule_python = ""

if type_ordinateur == "Mac":
    formule_python = f"""pyinstaller --noconfirm --onedir --windowed --target-arch arm64 --icon "{dossier_actuel}/Icone.icns" --name 'Conversion RGB' "{dossier_actuel}/interface_main.py" """
else:
    formule_python = f"""pyinstaller --noconfirm --onefile --windowed --icon "{dossier_actuel}/Icone.icns" --name 'Conversion RGB' "{dossier_actuel}/interface_main.py" """
system(formule_python)


# Formule bash pour lancement depuis le terminal :
## pyinstaller --noconfirm --onefile --windowed --icon "Icone.icns" --name 'Conversion RGB' "interface_main.py"