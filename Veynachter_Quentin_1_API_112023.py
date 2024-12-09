import subprocess
import os

#Chemin pour accéder à api.py et dashboard.py
dir = './Veynachter_Quentin_3_Dossier_Code_112023/Artefacts'

#On récupère les variables d'environnement
env = os.environ.copy()

#On exécute api.py et dashboard.py
subprocess.Popen(['python', f'{dir}/api.py', '--port', '5000'], env=env)
subprocess.Popen(['streamlit', 'run', f'{dir}/dashboard.py', '--server.port', '8000'], env=env)