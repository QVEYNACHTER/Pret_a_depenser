import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, ScalarFormatter
import matplotlib.ticker as ticker
import requests
import streamlit as st

#On récupère data_final
data_path = os.path.join('data_sample.parquet')
df = pd.read_parquet(data_path)

#Le threshold
threshold = 44.5262

#Pour étendre la largeur de la page
st.set_page_config(layout='wide')

#Fonction pour récupérer les états stockés
def get_state():
    if 'state' not in st.session_state:
        st.session_state['state'] = {'data_received': False,
                                     'data': None,
                                     'last_sk_id_curr': None}
    elif ('last_sk_id_curr' not in st.session_state['state']): #On vérifie si 'last_sk_id_curr' existe
        st.session_state['state']['last_sk_id_curr'] = None #On l'ajoute si ce n'est pas le cas

    return st.session_state['state']

#Fonction pour formater les valeurs numériques
def format_value(val):
    if pd.isna(val):
        return val
    if isinstance(val, (float, int)):
        if val == int(val):
            return f"{val:.0f}" #return int(val) ne fonctionnait pas comme espéré
        return round(val, 2)
    return val

#Fonction pour retourner une couleur (vert ou rouge) en fonction du threshold
def compute_color(value):
    if 0 <= value < threshold:
        return "green"
    elif threshold <= value <= 100:
        return "red"

#Fonction pour plot la distribution des features
def plot_distribution(select_feature, col):
    if select_feature:
        data = df[select_feature]

        #La valeur de la feature pour le client actuel
        client_feature_value = feature_values[feature_names.index(select_feature)]

        fig, ax = plt.subplots(figsize=(10, 6)) #Taille du graphique

        #On vérifie si la feature est catégorielle, comme elles ont été one-hot encodées, elles ne peuvent prendre que les valeurs 0, 1 ou NaN
        unique_values = sorted(data.dropna().unique())
        if set(unique_values) <= {0, 1}:
            #On compte les occurences de chaque valeur
            counts = data.value_counts().sort_index()

            #On colorie les barres en bleu
            colors = ['blue'] * len(unique_values)

            #Sauf celle du client concerné
            if client_feature_value in unique_values:
                client_value_index = unique_values.index(client_feature_value)
                colors[client_value_index] = 'darkorange'

            #On trace le barplot
            ax.bar(unique_values, counts.values, color=colors, edgecolor='black')

            #On fixe explicitement les xticks à 0 et 1
            ax.set_xticks([0, 1])

        #Si la feature n'est pas catégorielle
        else:
            #On détermine dynamiquement le nombre de bins
            n_unique = data.nunique() #Nombre de valeurs uniques
            n_bins = min(n_unique, 20) #Jusqu'à 20 bins max

            #On trace maintenant l'histogramme (en bleu)
            hist_data, bins, patches = ax.hist(data.dropna(), bins=n_bins, color='blue', edgecolor='black')

            #On trouve la bin correspondant au client
            client_bin_index = np.digitize(client_feature_value, bins, right=True) - 1

            #Correction pour les valeurs minimales
            if client_feature_value == bins[0]:
                client_bin_index = 0 #On force la première bin

            #Et on change la couleur en orange
            if 0 <= client_bin_index < len(patches): #On vérifie que l'index est valide
                patches[client_bin_index].set_facecolor('darkorange')

            #On ajoute les NaNs comme une barre séparée (en calculant dynamiquement sa position)
            n_nan = data.isna().sum()
            if n_nan > 0:
                #On calcule la position et la largeur de la barre
                bin_width = bins[1] - bins[0]  #Largeur des bins
                ax.bar(bins[-1] + bin_width / 2, n_nan, width=bin_width, color='blue', label='NaN', edgecolor='black')

                #Si la valeur du client pour cette feature est NaN, on la colorie en orange
                if pd.isna(client_feature_value):
                    ax.bar(bins[-1] + bin_width / 2, n_nan, width=bin_width, color='darkorange', label='NaN', edgecolor='black')

                #On étiquète la barre pour la distinguer des autres catégories
                ax.text(bins[-1] + bin_width / 2, n_nan, 'NaN', ha='center', va='bottom')

            #On applique une échelle logarythmique si nécessaire
            total_values = np.append(hist_data, n_nan) #On inclue les NaNs
            mean_val = np.mean(total_values)
            max_val = np.max(total_values)
            if max_val > 500: #Correspond à la moitié de l'échantillon
                ax.set_yscale('log')

            #Pour éviter la notation scientifique sur l'axe des y après passage à l'échelle logarythmique
            ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
            ax.yaxis.get_major_formatter().set_useOffset(False)

            #On limite à 5 ticks, et on évite également la notation scientifique sur l'axe des x
            ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
            ax.ticklabel_format(axis='x', style='plain')

        #On retirer le cadre du graphique
        for spine in ax.spines.values():
            spine.set_visible(False)

        #On ajoute les titres et labels
        ax.set_title(f'Distribution pour {select_feature}', weight='bold')
        ax.set_xlabel(select_feature)
        ax.set_ylabel('Nombre de clients')

        col.pyplot(fig)

state = get_state()

st.markdown("<h1 style='text-align: center; color: black;'>Probablité de remboursement</h1>", unsafe_allow_html=True)

#On augmente la taille du texte dans les graphs
plt.rcParams.update({'font.size': 14})

#Ainsi que l'input
st.markdown("""
            <style>.stTextInput input {font-size: 24px !important; height: 40px !important}</style>
            """,
            unsafe_allow_html=True)

#One entre l'identifiant
sk_id_curr = st.text_input(r"$\textsf{\LARGE Entrez le SK\_ID\_CURR :}$")

#Style pour le bouton
st.markdown("""
            <style>button {width: 80px !important; height: 50px !important; white-space: nowrap !important}</style>
            """,
            unsafe_allow_html=True)

#Bouton pour exécuter l'appel API
if st.button(r"$\textsf{\LARGE Run}$"):
    #Vérifications avant l'exécution
    if not sk_id_curr: #Si aucun ID n'a été entré
        st.error('Aucun SK_ID_CURR saisi')
        st.stop()

    #On vérifie si l'ID est un entier positif
    if not sk_id_curr.isdigit() or int(sk_id_curr) < 0:
        st.error('SK_ID_CURR saisi invalide')
        st.stop()

    #Si l'ID est différent du précédent, on réinitialise
    if sk_id_curr != state['last_sk_id_curr']:
        state['data_received'] = False
        state['last_sk_id_curr'] = sk_id_curr #On met à jour l'ID client
    else:
        st.success('Données déjà reçues pour ce client')

#Si les données ne sont pas encore reçues
if not state['data_received']:
    if state['last_sk_id_curr']: #On vérifie qu'un ID a été fourni
        try:
            #Appel à l'API
            response = requests.post('http://127.0.0.1:5000/predict', json={'SK_ID_CURR': int(state['last_sk_id_curr'])})

            #Gestion des erreurs de l'API
            if response.status_code == 500:
                st.error("Cet SK_ID_CURR n'existe pas ou est invalide")
                st.stop()
            elif response.status_code != 200: #Autres erreurs API
                st.error(f"Erreur lors de l'appel à l'API : {response.status_code} - {response.text}")
                st.stop()

            #On sauvegarde les données reçues si tout est OK
            state['data'] = response.json()
            state['data_received'] = True

        #Autres erreurs potentielles
        except requests.exceptions.ConnectionError:
            st.error("Le serveur est indisponible, vérifiez qu'il est bien démarré")
            st.stop()
        except requests.exceptions.Timeout:
            st.error('La requête a expiré, le serveur met trop de temps à répondre')
            st.stop()
        except ValueError:
            st.error('SK_ID_CURR saisi invalide')
            st.stop()

#On traite les données uniquement si elles sont disponibles
if state['data_received']:
    data = state['data']

    proba = data['probability']
    shap_values = data['shap_values']
    shap_values = [val[0] if isinstance(val, list) else val for val in shap_values] #Si val est une liste on récupère le premier élément val[0], sinon on récupère val tel quel
    feature_names = data['feature_names']
    feature_values = data['feature_values']

    #On créé un df
    shap_df = pd.DataFrame(list(zip(feature_names,
                                    shap_values,
                                    [format_value(val) for val in feature_values])),
                           columns=['Feature', 'SHAP Value', 'Feature Value'])
    
    #On applique la couleur en fonction de la proba
    color = compute_color(proba)

    #Création d'une jauge pour voir où se positionne le client par rapport au threshold
    jauge_html = f"""
                <div style="position: relative; width: 100%; height: 30px; background: linear-gradient(to right, green {threshold}%, red {threshold}%); border-radius: 15px">
                    <div style="position: absolute; top: 50%; left: {proba}%; transform: translateX(-50%) translateY(-50%);
                    width: 20px; height: 20px; background-color: black; border-radius: 50%; border: 3px solid white">
                </div></div>
                """

    #On affiche
    st.markdown(jauge_html, unsafe_allow_html=True)

    #Un peu d'espace avant la suite
    st.markdown("<br>", unsafe_allow_html=True)

    #Message en fonction de la décision
    message_decision = (f'Risque faible ({proba:.2f}%)' if proba < threshold else f'Risque potentiel ({proba:.2f}%)')
    st.markdown(f"<div style='text-align: center; color:{color}; font-size:30px; border:2px solid {color}; padding:10px;'>{message_decision}</div>", unsafe_allow_html=True)

    #Encore un espace
    st.markdown("<br>", unsafe_allow_html=True)

    #On filtre le top 10 features qui réduisent et augmentent le risque
    shap_df_decrease = shap_df[shap_df['SHAP Value'] < 0].sort_values(by='SHAP Value').head(10)
    shap_df_increase = shap_df[shap_df['SHAP Value'] > 0].sort_values(by='SHAP Value', ascending=False).head(10)

    #On créé des subplots
    fig, axes = plt.subplots(1, 2, figsize=(16, 8), gridspec_kw={'width_ratios': [1, 1]})

    #Graphique pour les features qui réduisent le risque
    bars_left = axes[0].barh(shap_df_decrease['Feature'], shap_df_decrease['SHAP Value'], color='lightgreen', edgecolor='black')
    axes[0].set_xlabel('Feature importance')
    axes[0].set_title('Top 10 features qui réduisent le risque', weight='bold')
    axes[0].invert_yaxis() #Inverse l'axe pour que la feature la plus importante soit en haut
    axes[0].invert_xaxis() #Inverse l'axe pour les barres pointent vers la droite
    axes[0].xaxis.set_major_locator(MaxNLocator(nbins=3)) #Limite à 3 xticks

    #On retire le cadre autour des axes
    for spine in axes[0].spines.values():
        spine.set_visible(False)

    #On ajoute les feature values en annotations
    for bar, feature_value in zip(bars_left, shap_df_decrease['Feature Value']):
        axes[0].text(bar.get_width() - 0.0005, #Hors de la barre
                     bar.get_y() + bar.get_height() / 2, #Centré dans la barre
                     f'{feature_value}',
                     va='center', ha='left', fontweight='bold', color='black') #Aligné à gauche

    #Graphique pour les features qui augmentent le risque
    bars_right = axes[1].barh(shap_df_increase['Feature'], shap_df_increase['SHAP Value'], color='lightcoral', edgecolor='black')
    axes[1].set_xlabel('Feature importance')
    axes[1].set_title('Top 10 features qui augmentent le risque', weight='bold')
    axes[1].invert_xaxis() #Inverse l'axe pour les barres pointent vers la gauche
    axes[1].yaxis.tick_right() #Déplace les yticks à droite
    axes[1].yaxis.set_tick_params(left=False) #Désactive les yticks à gauche
    axes[1].xaxis.set_major_locator(MaxNLocator(nbins=3)) #Limite à 3 xticks

    #On retire le cadre autour des axes
    for spine in axes[1].spines.values():
        spine.set_visible(False)

    #On ajoute les feature values en annotations
    for bar, feature_value in zip(bars_right, shap_df_increase['Feature Value']):
        axes[1].text(bar.get_width() + 0.0005, #Hors de la barre
                     bar.get_y() + bar.get_height() / 2, #Centré dans la barre
                     f'{feature_value}',
                     va='center', ha='right', fontweight='bold', color='black') #Aligné à droite

    st.pyplot(fig)

    #Un dernier espace pour la route
    st.markdown("<br>", unsafe_allow_html=True)
    
    #On créé des colonnes pour les listes déroulantes
    col1, col2 = st.columns(2)

    #Ajout des features qui réduisent le risque dans col1
    with col1:
        select_decrease = st.selectbox(r"$\textsf{\LARGE Sélectionnez une feature réduisant le risque :}$",
                                       [''] + shap_df_decrease['Feature'].tolist())
    
    #Ajout des features qui augmentent le risque dans col2
    with col2:
        select_increase = st.selectbox(r"$\textsf{\LARGE Sélectionnez une feature augmentant le risque :}$",
                                       [''] + shap_df_increase['Feature'].tolist())
    
    #On plot
    plot_distribution(select_decrease, col1)
    plot_distribution(select_increase, col2)
