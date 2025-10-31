import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn #Linear, ReLU, Dropout, Softmax
import torch.optim as optim
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset
import os

#evaluacion
from sklearn.metrics import classification_report, confusion_matrix

#Cargar y preparar datos
def cargar_datos(ruta_json):
    with open(ruta_json) as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    
    # Separar features y target 32 bits para compatibilidad con tpyorch
    X = df.drop(['resultado_final', 'resultado_ht', 'goles_local_final', 'goles_visitante_final'], axis=1).values.astype('float32')
    #64 bits para crossentropyloss
    y = df['resultado_final'].values.astype('int64')

    valores, conteos = np.unique(y, return_counts=True)
    print("Distribución de clases en y:")
    for v, c in zip(valores, conteos):
        print(f"Clase {v}: {c} muestras")

    return X, y


# dataloaders para entrenamiento y validación Random state para que siempre sea la misma distribución 
def crear_dataloaders(X, y, batch_size=32, val_split=0.2):
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=val_split, random_state=42, stratify=y)
    # TORCH tensor pytorch dataset y dataloader, tensordataset los empaqueta juntos para Dataloader
    train_ds = TensorDataset(torch.tensor(X_train), torch.tensor(y_train))
    val_ds = TensorDataset(torch.tensor(X_val), torch.tensor(y_val))

    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    #ERROR, NO SAE NECESITA SHUFFLE EN VALIDACIÓN
    val_dl = DataLoader(val_ds, batch_size=batch_size)
    return train_dl, val_dl

# ARQUITECTURA PRINCIPAL DE LA RED NEURONAL
class RedNeuronal(nn.Module):
    def __init__(self, entrada, oculta_1=32, oculta_2=16, salida=3):
        #Llamada al constructor del padre nn.Module
        super().__init__()

        #Capas tipo cFull connected 

        self.fc1 = nn.Linear(entrada, oculta_1) # features convertidos en neuronas entrada x oculta_1
        self.relu1 = nn.ReLU()
        #self.dropout1 = nn.Dropout(0.3) 
        
        #variar el dropout entre capas pq¡ue puede ayudar a generalizar mejor

        self.fc2 = nn.Linear(oculta_1, oculta_2)
        self.relu2 = nn.ReLU() # oculta_1 x oculta_2
        #self.dropout2 = nn.Dropout(0.2)
        
        self.fc3 = nn.Linear(oculta_2, salida) # oculta_2 x salida

    # FORWARD
    def forward(self, x):
        #x = self.dropout1(self.relu1(self.fc1(x)))
        #x = self.dropout2(self.relu2(self.fc2(x)))
        x = self.relu1(self.fc1(x))
        x = self.relu2(self.fc2(x))
        x = self.fc3(x)
        return x

#Función para entrenar una época
def entrenar_epoch(modelo, dataloader, perdida, optimizer, host):
    #Modo entrenamiento
    modelo.train()
    # perdida, correctitud y total de procesados
    #AQUI EL ERROR loss.item() retorna float
    perdidas = 0.0
    correctitud = 0
    total = 0

    for X_batch, y_batch in dataloader:
        X_batch, y_batch = X_batch.to(host), y_batch.to(host)

        # Reiniciar gradientes
        optimizer.zero_grad()
        
        outputs = modelo(X_batch)
        # perdida = crossentropyloss aplica softmax internamente
        loss = perdida(outputs, y_batch)
        # gradientes hacia atrás y ajuste de pesos
        loss.backward()
        optimizer.step()
        # loss es el promedio de la batch, multiplicamos por tamaño batch para tener la suma total
        perdidas += loss.item() * X_batch.size(0)
        # torch max devuelve valor y índice de la clase predicha, solo queremos el indice   
        _, preds = torch.max(outputs, 1)
        # sumar correctos
        correctitud += torch.sum(preds == y_batch).item()
        # GUARDAR TOTAL PROCESADOS
        total += y_batch.size(0)
        
    perdida_epoca = perdidas / total
    correctitud_epoca = correctitud / total
    return perdida_epoca, correctitud_epoca

# Función para validar modeloo
def validar_epoch(modelo, dataloader, perdida, host):
    modelo.eval()
    perdidas = 0.0
    correctitud = 0
    total = 0
    
    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            X_batch, y_batch = X_batch.to(host), y_batch.to(host)
            outputs = modelo(X_batch)
            loss = perdida(outputs, y_batch)
            
            perdidas += loss.item() * X_batch.size(0)
            _, preds = torch.max(outputs, 1)
            correctitud += torch.sum(preds == y_batch).item()
            total += y_batch.size(0)
    
    perdida_epoca = perdidas / total
    correctitud_epoca = correctitud / total
    return perdida_epoca, correctitud_epoca

# Función completa para entrenar la red
def entrenar_red(ruta_json, cantidad_epocas, batch_size, learning_rate):
    # Entrenamos con gpu si hay 
    host = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    X, y = cargar_datos(ruta_json)
    train_dl, val_dl = crear_dataloaders(X, y, batch_size=batch_size)
    entrada = X.shape[1]
    print(f"Número de características de entrada: {entrada}")
    modelo = RedNeuronal(entrada=entrada).to(host)
    # aplica softmax internamente
    perdida = nn.CrossEntropyLoss()


    optimizer = optim.Adam(modelo.parameters(), lr=learning_rate)

    # Early stopping variables
    mejor_val_loss = float('inf')
    paciocontar = 0
    paciencia = 10
    
    for epoca in range(cantidad_epocas):
        train_loss, train_acc = entrenar_epoch(modelo, train_dl, perdida, optimizer, host)
        val_loss, val_acc = validar_epoch(modelo, val_dl, perdida, host)

        #Progreso de la epoca
        print(f"Época {epoca+1}/{cantidad_epocas} | " f"Pérdida Entrenamiento: {train_loss:.4f} | Pérdida Validación: {val_loss:.4f} | " f"Precisión Entrenamiento: {train_acc:.4f} | Precisión Validación: {val_acc:.4f}")
        
        # Early stoppingz
        if val_loss < mejor_val_loss:
            mejor_val_loss = val_loss
            paciocontar = 0
            # Earluy stopping: guardar el mejor modelo
            torch.save(modelo.state_dict(), 'modelo_mejor.pth')
        else:
            paciocontar += 1
            if paciocontar >= paciencia:
                print("EARLY STOPPING. No hay mejora en la pérdida de validación.")
                break
    print("\nEntrenamiento finalizado. El mejor modelo se guardó'.")
    return modelo, val_dl
            #EVALUACIÓN FINAL 

from sklearn.metrics import confusion_matrix, classification_report

def evaluar_modelo(modelo, dataloader, host):
    modelo.eval()
    y_true, y_pred = [], []

    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            X_batch = X_batch.to(host)
            outputs = modelo(X_batch)
            _, preds = torch.max(outputs, 1)
            y_true.extend(y_batch.cpu().numpy())
            y_pred.extend(preds.cpu().numpy())

    print("\n--- Evaluación final ---")
    print("Matriz de confusión:")
    print(confusion_matrix(y_true, y_pred))
    print("\nReporte de clasificación:")
    print(classification_report(y_true, y_pred, target_names=['Away', 'Draw', 'Home']))
   

def main():
    # Directorio donde está este script
    script_dir = os.path.dirname(__file__)

    # Ruta relativa
    ruta_json = os.path.abspath(os.path.join(script_dir, "..", "preprocesamiento", "datos_procesados.json"))

    print("Iniciando entrenamiento de la red neuronal...")
    print("Archivo de datos:", ruta_json)

    # Verificar si hay GPU disponible
    host = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Usando dispositivo: {host}\n")

    # Parámetros del entrenamiento
    cantidad_epocas = 50
    batch_size = 32
    learning_rate = 0.001

    # Entrenar la red y obtener modelo + dataloader
    modelo, val_dl = entrenar_red(
        ruta_json=ruta_json,
        cantidad_epocas=cantidad_epocas,
        batch_size=batch_size,
        learning_rate=learning_rate
    )

    # Cargar mejor modelo y evaluar
    modelo.load_state_dict(torch.load('modelo_mejor.pth'))
    evaluar_modelo(modelo, val_dl, host)
      
    id_visitante = 1
    id_local = 3
     # Crear vector de entrada con valores promedio o neutros
    entrada = {
        "fecha": 0.5,
        "id_equipo_local": id_local,
        "id_equipo_visitante": id_visitante,
        "goles_local_ht": 0.5,
        "goles_visitante_ht": 0.5,
        "disparos_local": 0.5,
        "disparos_visitante": 0.5,
        "disparos_porteria_local": 0.5,
        "disparos_porteria_visitante": 0.5,
        "corners_local": 0.5,
        "corners_visitante": 0.5,
        "faltas_local": 0.5,
        "faltas_visitante": 0.5,
        "amarillas_local": 0.5,
        "amarillas_visitante": 0.5,
        "rojas_local": 0.0,
        "rojas_visitante": 0.0
    }

    df = pd.DataFrame([entrada])
    X = torch.tensor(df.values, dtype=torch.float32).to(host)

    with torch.no_grad():
        salida = modelo(X)
        probs = torch.softmax(salida, dim=1).cpu().numpy()[0]

    print(f"Pronóstico partido {id_local} vs {id_visitante}:")
    print(f"  Away: {probs[0]*100:.2f}%")
    print(f"  Draw: {probs[1]*100:.2f}%")
    print(f"  Home: {probs[2]*100:.2f}%")


# main
if __name__ == "__main__":
    main()

