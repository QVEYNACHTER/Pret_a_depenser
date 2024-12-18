import subprocess
import os

#Chemin pour accéder à api.py et dashboard.py
dir = './Veynachter_Quentin_3_Dossier_Code_112023/Artefacts'

#On récupère les variables d'environnement
env = os.environ.copy()

#Azure définit le port dans la variable d'environnement "PORT"
#Ici on utilise donc soit le port imposé par Azure, soit le port par défaut (en local)
port = env.get('PORT', '8501')

#On exécute api.py et dashboard.py
subprocess.Popen(['python', f'{dir}/api.py'], env=env)
subprocess.Popen(['streamlit', 'run', f'{dir}/dashboard.py', '--server.headless=true', f'--server.port={port}', '--server.address=0.0.0.0'], env=env)
