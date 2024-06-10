from google.colab import drive
drive.mount('/content/gdrive')

import pandas as pd
from collections import deque
import random
import numpy as np
from sklearn import preprocessing


SEQ_LEN = 60  #longueur des séquences à utiliser pour chaque échantillon de données
FUTURE_PERIOD_PREDICT = 3  #periode future à prédire
RATIO_TO_PREDICT = "LTC-USD" #crypto à prédire


def classify(current, future):
  #si val future > val actuelle
    if float(future) > float(current):
        return 1 #prédire un achat
    else:
        return 0 #prédire une vente

def preprocess_df(df):
    df = df.drop("future", axis=1)  #supp colonne 'future' qui était temporaire

    for col in df.columns:
        if col != "target":
            df[col] = df[col].pct_change() #calcul le % de changement
            df.dropna(inplace=True)
            df[col] = preprocessing.scale(df[col].values) #mise à l'échelle des valeurs

    df.dropna(inplace=True)

    sequential_data = []  #init liste pour les données séquentielles
    prev_days = deque(maxlen=SEQ_LEN) #utilisation deque pour garder les dernières valeurs

    for i in df.values:
        prev_days.append([n for n in i[:-1]])
        if len(prev_days) == SEQ_LEN:
            sequential_data.append([np.array(prev_days), i[-1]])

    random.shuffle(sequential_data) #melanger les données séquentielles

    buys = []  #liste séquences pour achat
    sells = []  #liste séquences pour vente

    for seq, target in sequential_data:
        if target == 0:  #si la cible est O
            sells.append([seq, target])  #ajout à la liste 'sells'
        elif target == 1: #si la cible est 1
            buys.append([seq, target]) #ajout à la liste 'buys'

    random.shuffle(buys)
    random.shuffle(sells)

    lower = min(len(buys), len(sells)) #determine la taille min des listes 'buys' et 'sells'

    buys = buys[:lower]  #tronque la liste 'buys' à cette taille
    sells = sells[:lower] #tronque la liste 'sells' à cette taille

    sequential_data = buys + sells #concaténation des 2 listes
    random.shuffle(sequential_data)
    X = []
    y = []

    for seq, target in sequential_data:
        X.append(seq) #ajoute la séquence à X
        y.append(target)  #ajout de la cible à y
    return np.array(X), y

main_df = pd.DataFrame()  #création d'un dataframe vide 'main_df'

ratios = ["BTC-USD", "LTC-USD", "BCH-USD", "ETH-USD"]  #liste des crypto à analyser
for ratio in ratios:  #parcourir chaque crypto
    print(ratio)
    dataset = f'/content/gdrive/My Drive/crypto_data/{ratio}.csv'
    df = pd.read_csv(dataset, names=['time', 'low', 'high', 'open', 'close', 'volume'])


    df.rename(columns={"close": f"{ratio}_close", "volume": f"{ratio}_volume"}, inplace=True) #renommer les colonnes pertinentes

    df.set_index("time", inplace=True)
    df = df[[f"{ratio}_close", f"{ratio}_volume"]]  #selectionne uniquement les colonnes de cloture et de volume

    if len(main_df) == 0:  #si 1er dataframe
        main_df = df #assigner le dataframe initial à main_df
    else:
        main_df = main_df.join(df) #joindre le nouveau dataframe à main_df

main_df.fillna(method="ffill", inplace=True)  #remplir val manquantes
main_df.dropna(inplace=True) #supp les lignes avec des val restantes

main_df['future'] = main_df[f'{RATIO_TO_PREDICT}_close'].shift(-FUTURE_PERIOD_PREDICT)
main_df['target'] = list(map(classify, main_df[f'{RATIO_TO_PREDICT}_close'], main_df['future']))

main_df.dropna(inplace=True)

times = sorted(main_df.index.values) #obtenir les val d'index triées
last_5pct = times[-int(0.05 * len(times))] #déterminer le point de séparation pour les données de validation (5% les + récentes)

validation_main_df = main_df[(main_df.index >= last_5pct)] #Sélection des données de validation à partir du point de séparation
main_df = main_df[(main_df.index < last_5pct)] #Sélection des données d'entraînement jusqu'au point de séparation

train_x, train_y = preprocess_df(main_df)
validation_x, validation_y = preprocess_df(validation_main_df)

print(f"train data: {len(train_x)} validation: {len(validation_x)}")
print(f"Dont buys: {train_y.count(0)}, buys: {train_y.count(1)}")
print(f"VALIDATION Dont buys: {validation_y.count(0)}, buys: {validation_y.count(1)}")
