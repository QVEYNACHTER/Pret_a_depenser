import subprocess
import os

#Chemin pour accéder à api.py et dashboard.py
dir = './Veynachter_Quentin_3_Dossier_Code_112023/Artefacts'

#On récupère les variables d'environnement
env = os.environ.copy()

#On exécute api.py et dashboard.py
subprocess.Popen(['python', f'{dir}/api.py'], env=env)
subprocess.Popen(['streamlit', 'run', f'{dir}/dashboard.py', '--server.headless=true'], env=env)