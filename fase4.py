import os
import datetime
import pickle
import matplotlib.pyplot as plt
import numpy as np
import csv

# Función para convertir voltaje a temperatura (en grados Celsius) usando la fórmula no lineal
def convertir_voltaje_a_celsius(volt_microv):
    volt_microv = float(volt_microv)
    Vref = 789000  # Vref en microvoltios (789,000 µV)
    
    if volt_microv == Vref:
        raise ValueError("El voltaje es igual a Vref, lo que provoca una división por cero.")
    
    R = 10e3 * Vref / (volt_microv - Vref)
    
    if R > 10e3:
        T = (-24536.24 + 0.02350289 * R * 100 + 1.034084e-9 * (R * 100)**2) / 100
    else:
        T = (-24564.58 + 0.02353718 * R * 100 + 1.027502e-9 * (R * 100)**2) / 100
    
    return T

# Cargar el archivo de datos
with open('datos2.pkl', 'rb') as f:
    datos = pickle.load(f)

# Crear carpeta de salida con fecha y hora actual
fecha_hora_actual = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
carpeta_base = os.path.expanduser("~/resultados_atlas/result_cons")
carpeta_salida = os.path.join(carpeta_base, f"resultados_{fecha_hora_actual}")
os.makedirs(carpeta_salida, exist_ok=True)

# Extraer la información necesaria del archivo cargado
numero_ciclos = len(datos)
num_canales = len(datos[0]['voltajes_opc'])



# Inicializar matrices para almacenar los errores ajustados para cada canal y ciclo
errores_ajustados_voltios = np.zeros((numero_ciclos, num_canales))
errores_ajustados_temp = np.zeros((numero_ciclos, num_canales))

# Calcular el error ajustado para cada canal en cada ciclo, en voltios y en temperatura
for i, entry in enumerate(datos):
    voltaje_referencia = entry['voltaje_medido']
    voltajes_opc = entry['voltajes_opc']
    
    errores_ajustados_voltios[i, :] = [(opc - voltaje_referencia) / 1e6 for opc in voltajes_opc]
    
    try:
        temp_referencia = convertir_voltaje_a_celsius(voltaje_referencia)
        errores_ajustados_temp[i, :] = [
            convertir_voltaje_a_celsius(opc) - temp_referencia for opc in voltajes_opc
        ]
    except ValueError as e:
        print(f"Error en la conversión de voltaje a temperatura: {e}")
        continue

# Guardar los errores ajustados en voltios y temperatura en archivos CSV
ruta_csv_voltios = os.path.join(carpeta_salida, 'errores_ajustados_voltios.csv')
with open(ruta_csv_voltios, mode='w', newline='') as archivo_csv:
    escritor_csv = csv.writer(archivo_csv)
    escritor_csv.writerow(['Ciclo'] + [f'Canal_{i+1}' for i in range(num_canales)])
    for i in range(numero_ciclos):
        escritor_csv.writerow([i+1] + list(errores_ajustados_voltios[i, :]))

ruta_csv_temp = os.path.join(carpeta_salida, 'errores_ajustados_temperatura.csv')
with open(ruta_csv_temp, mode='w', newline='') as archivo_csv:
    escritor_csv = csv.writer(archivo_csv)
    escritor_csv.writerow(['Ciclo'] + [f'Canal_{i+1}' for i in range(num_canales)])
    for i in range(numero_ciclos):
        escritor_csv.writerow([i+1] + list(errores_ajustados_temp[i, :]))

#------------Mapa de calor------------------------
errores_temperatura = np.zeros((numero_ciclos, num_canales))

# Calcular el error en temperatura para cada canal en cada ciclo
for i, entry in enumerate(datos):
    voltaje_referencia = entry['voltaje_medido']  # Voltaje de referencia del multímetro ya en microvoltios
    voltajes_opc = entry['voltajes_opc']  # Voltajes OPC ya en microvoltios
    
    # Convertir voltaje de referencia a temperatura en grados Celsius
    try:
        temp_referencia = convertir_voltaje_a_celsius(voltaje_referencia)  # Convertir a temperatura en °C
        # Convertir voltajes OPC a temperatura y calcular el error
        errores_temperatura[i, :] = [
            abs(convertir_voltaje_a_celsius(opc) - temp_referencia) for opc in voltajes_opc
        ]
    except ValueError as e:
        print(f"Error en la conversión de voltaje a temperatura: {e}")
        continue

# Guardar el error en temperatura en un archivo CSV para el mapa de calor
ruta_csv_mapa_calor = os.path.join(carpeta_salida, 'mapa_calor_error_temperatura.csv')
with open(ruta_csv_mapa_calor, mode='w', newline='') as archivo_csv:
    escritor_csv = csv.writer(archivo_csv)
    # Cambiar 'Ciclo' a 'Numero de Ciclo' y comenzar desde 0
    escritor_csv.writerow(['Numero de Ciclo'] + [f'Canal_{i+1}' for i in range(num_canales)])
    for i in range(numero_ciclos):
        escritor_csv.writerow([i] + list(errores_temperatura[i, :]))  # Comenzar desde 0

# Generar el mapa de calor y guardarlo como imagen
plt.figure(figsize=(12, 8))
im = plt.imshow(
    errores_temperatura, 
    aspect='auto', 
    cmap='hot', 
    interpolation='nearest',
    origin='lower'  # Establecer el origen en la parte inferior
)

plt.colorbar(label='Error Absoluto de Temperatura (°C)')
plt.xlabel('Canales')
plt.ylabel('Numero de Ciclo')
plt.title('Mapa de Calor del Error de Temperatura por Canal y Ciclo')

# Configurar las etiquetas del eje X
plt.xticks(ticks=np.arange(num_canales), labels=[f"{i+1}" for i in range(num_canales)], rotation=90)

# Configurar las etiquetas del eje Y de 0 a numero_ciclos
etiquetas_y = [f"{i}" for i in range(numero_ciclos)]
plt.yticks(ticks=np.arange(numero_ciclos), labels=etiquetas_y)

# Eliminar la inversión del eje Y
# plt.gca().invert_yaxis()  # Eliminar o comentar esta línea

# Guardar el mapa de calor en la carpeta de salida
ruta_grafica_mapa_calor = os.path.join(carpeta_salida, 'mapa_calor_error_temperatura.png')
plt.savefig(ruta_grafica_mapa_calor)
plt.show()
#------------Mapa de calor------------------------


# Generar y guardar el boxplot de los errores ajustados en voltios para cada canal
plt.figure(figsize=(12, 6))
plt.boxplot(errores_ajustados_voltios, vert=True, patch_artist=True)
plt.xlabel('Canales')
plt.ylabel('Error Ajustado (V_OPC - V_Referencia por Ciclo) [V]')
plt.title('Distribución del Error Ajustado en Cada Canal (Voltios)')
ruta_grafica_voltios = os.path.join(carpeta_salida, 'grafica_error_ajustado_voltios.png')
plt.savefig(ruta_grafica_voltios)
plt.show()

# Generar y guardar el boxplot de los errores ajustados en temperatura para cada canal
plt.figure(figsize=(12, 6))
plt.boxplot(errores_ajustados_temp, vert=True, patch_artist=True)
plt.xlabel('Canales')
plt.ylabel('Error Ajustado en Temperatura (°C)')
plt.title('Distribución del Error Ajustado en Cada Canal (Temperatura)')
ruta_grafica_temp = os.path.join(carpeta_salida, 'grafica_error_ajustado_temperatura.png')
plt.savefig(ruta_grafica_temp)
plt.show()

# Al final del script
print(f"Gráficas y archivos CSV guardados en la carpeta: {carpeta_salida}")
