import sys
import pickle
import numpy as np
import csv
import matplotlib.pyplot as plt
import math  # Importar para usar funciones matemáticas
import os
import datetime


# Cargar 'datos' desde el archivo
with open('datos.pkl', 'rb') as f:
   datos = pickle.load(f)

# Validar y obtener los argumentos de la línea de comandos
if len(sys.argv) != 3:
    print("Usage: python3 fase2.py <rms_maximo_permitido> <ID>")
    sys.exit(1)

try:
    valor_rms_temp_usuario = float(sys.argv[1])
    Id = int(sys.argv[2])
except ValueError:
    print("Error: Invalid input. RMS máximo permitido debe ser un número.")
    sys.exit(1)

print("Iniciando el procesamiento de datos...")


# Crear carpeta de salida con fecha y hora actual
fecha_hora_actual = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
carpeta_base = os.path.expanduser("~/resultados_atlas")
carpeta_salida1 = os.path.join(carpeta_base, f"ID_{Id}")
carpeta_salida = os.path.join(carpeta_salida1, f"test_{fecha_hora_actual}")
os.makedirs(carpeta_salida, exist_ok=True)

# --------- Calcular voltaje multímetro vs voltaje OPC y guardar en CSV -------
voltajes_multimetro = []
voltajes_opc_por_multimetro = []

for lectura in datos:
    voltaje_multimetro = lectura['voltaje_medido']
    voltajes_opc = lectura['voltajes_opc']
    
    voltajes_multimetro.append(voltaje_multimetro)
    voltajes_opc_por_multimetro.append(voltajes_opc)

# Calcular la media y la desviación estándar de los voltajes OPC para cada valor del multímetro
medias_opc = []
desviaciones_opc = []

for voltajes_opc in voltajes_opc_por_multimetro:
    # Convertir cada valor de microvoltios a voltios dividiendo por 1e6
    voltajes_opc = [v * 1e-6 for v in voltajes_opc if v is not None]  # Excluir valores None y convertir a voltios
    if voltajes_opc:
        media = np.mean(voltajes_opc)
        desviacion = np.std(voltajes_opc)
    else:
        media = None
        desviacion = None
    medias_opc.append(media)
    desviaciones_opc.append(desviacion)


# Guardar los datos en un archivo CSV
ruta_csv_grafica = os.path.join(carpeta_salida, 'voltaje_multimetro_vs_opc.csv')
with open(ruta_csv_grafica, mode='w', newline='') as archivo_csv:
    escritor_csv = csv.writer(archivo_csv)
    escritor_csv.writerow(['Voltaje Multímetro (V)', 'Media Voltaje OPC (V)', 'Desviación Voltaje OPC (V)'])

    for voltaje_multimetro, media_opc, desviacion_opc in zip(voltajes_multimetro, medias_opc, desviaciones_opc):
        escritor_csv.writerow([voltaje_multimetro, media_opc, desviacion_opc])

print(f"Archivo CSV de voltaje multímetro vs. voltaje OPC guardado en: {ruta_csv_grafica}")

# ------- Fin de la sección de CSV de voltaje multímetro vs OPC -------

# ------ Generar y guardar la gráfica de voltaje multímetro vs voltaje OPC -------
plt.figure(figsize=(10, 6))
plt.errorbar(voltajes_multimetro, medias_opc, yerr=desviaciones_opc, fmt='o', ecolor='gray', capsize=5, label='Voltajes OPC')
plt.xlabel("Voltaje Multímetro (V)")
plt.ylabel("Voltaje OPC (V)")
plt.title("Voltaje del Multímetro vs Voltajes OPC con Dispersión")
plt.legend()
plt.grid(True)

# Guardar la gráfica en la carpeta de salida
ruta_grafica_opc = os.path.join(carpeta_salida, 'grafica_multimetro_vs_opc.png')
plt.savefig(ruta_grafica_opc)
plt.show()

print(f"Gráfica de voltaje multímetro vs OPC guardada en: {ruta_grafica_opc}")
# ------ Fin de la sección de gráfica -------
# Inicializar diccionarios para almacenar errores
errores_cuadrados_por_canal = {i: [] for i in range(48)}  # Diccionario para almacenar errores cuadrados por canal
errores_cuadrados_temp_por_canal = {i: [] for i in range(48)}  # Diccionario para almacenar errores cuadrados de temperatura por canal

# Función para convertir voltaje a temperatura (en grados Celsius) usando la fórmula no lineal
def convertir_voltaje_a_celsius(volt_microv):
   # Asegurarse de que volt_microv es un número de punto flotante
   volt_microv = float(volt_microv)
   
   # Constante Vref en microvoltios
   Vref = 789000  # 789,000 µV
   
   # Evitar división por cero
   if volt_microv == Vref:
       raise ValueError("El voltaje es igual a Vref, lo que provoca una división por cero.")
   
   # Calcular la resistencia R
   R = 10e3 * Vref / (volt_microv - Vref)
   
   # Determinar qué ecuación usar según el valor de R
   if R > 10e3:
       # Fórmula para R > 10kΩ (T ≤ 0°C)
       T = (-24536.24 + 0.02350289 * R * 100 + 1.034084e-9 * (R * 100)**2) / 100
   else:
       # Fórmula para R ≤ 10kΩ (T ≥ 0°C)
       T = (-24564.58 + 0.02353718 * R * 100 + 1.027502e-9 * (R * 100)**2) / 100
   
   return T

# Abrir archivo CSV para escribir los resultados
ruta_csv_ppp5 = os.path.join(carpeta_salida, 'ppp5.csv')
with open(ruta_csv_ppp5, mode='w', newline='') as archivo_csv:
   escritor_csv = csv.writer(archivo_csv)

   # Añadir encabezados de las columnas, incluyendo el número de canal, las temperaturas y el error relativo de temperatura
   escritor_csv.writerow([
       'Timestamp', 'Voltaje Fuente (µV)', 'Voltaje Medido (µV)', 
       'Canal', 'Voltaje OPC Canal (µV)', 'Error Voltaje (V)', 
       'Temperatura OPC (°C)', 'Temperatura Multímetro (°C)', 'Error Temperatura (°C)'
   ])

   # Procesar cada lectura almacenada
   for lectura in datos:
       timestamp = lectura['timestamp']
       valor_fuente = lectura['voltaje_fuente'] * 1e6  # Convertir a microvoltios si está en voltios
       valor_medido = lectura['voltaje_medido'] * 1e6  # Convertir a microvoltios si está en voltios
       voltajes_opc_actuales = lectura['voltajes_opc']  # Los voltajes OPC ya están en microvoltios

       # Procesar cada canal para calcular el error relativo del voltaje, temperatura y almacenar el error cuadrado
       for i, voltaje_opc in enumerate(voltajes_opc_actuales):
           if voltaje_opc is not None and voltaje_opc != 0:
               # Como voltaje_opc ya está en µV, no es necesario convertir
               voltaje_opc_microv = voltaje_opc  # Ya en µV

               # valor_medido ya está en µV
               valor_medido_microv = valor_medido  # Ya en µV

               # Calcular el error con signo del voltaje
               error_voltaje = (voltaje_opc_microv - valor_medido_microv)
               try:
                   temperatura_opc = convertir_voltaje_a_celsius(voltaje_opc_microv)  # Calcular la temperatura del voltaje OPC
                   temperatura_multimetro = convertir_voltaje_a_celsius(valor_medido_microv)  # Calcular la temperatura del multímetro

                   # Calcular el error con signo de la temperatura
                   error_temperatura = (temperatura_opc - temperatura_multimetro) 

                   #-------Esto es para ECM de voltajes--------
                   # Calcular el error cuadrado del voltaje y almacenarlo
                   error_cuadrado = (voltaje_opc_microv - valor_medido_microv) ** 2
                   errores_cuadrados_por_canal[i].append(error_cuadrado)

                   #-------Esto es para ECM de temperatura--------
                   # Calcular el error cuadrado de la temperatura y almacenarlo
                   error_cuadrado_temp = (temperatura_opc - temperatura_multimetro) ** 2
                   errores_cuadrados_temp_por_canal[i].append(error_cuadrado_temp)





               except ValueError as e:
                   print(f"Error al convertir voltaje a temperatura en canal {i}: {e}")
                   # En caso de error, asignamos None a las variables correspondientes
                   temperatura_opc = None
                   temperatura_multimetro = None
                   error_temperatura = None

           else:
               error_voltaje = None
               temperatura_opc = None
               temperatura_multimetro = None
               error_temperatura = None
               voltaje_opc_microv = None

           # Escribir una fila para cada canal, incluyendo los errores relativos para voltaje y temperatura
           escritor_csv.writerow([
               timestamp, valor_fuente, valor_medido, 
               i, voltaje_opc_microv, error_voltaje, temperatura_opc, 
               temperatura_multimetro, error_temperatura
           ])

#-------Cálculo de ECM y RMS para voltajes--------
# Calcular el ECM (Error Cuadrático Medio) por canal
ecm_por_canal = {}
rms_por_canal = {}  # Diccionario para almacenar el RMS por canal
for canal, errores in errores_cuadrados_por_canal.items():
   if len(errores) > 0:
       ecm = np.mean(errores)  # Calcular la media de los errores cuadrados para cada canal
       ecm_por_canal[canal] = ecm
       rms_por_canal[canal] = np.sqrt(ecm)  # Calcular la raíz cuadrada del ECM para obtener el RMS
   else:
       ecm_por_canal[canal] = None
       rms_por_canal[canal] = None  # Si no hay ECM, tampoco se puede calcular el RMS

#-------Cálculo de ECM y RMS para temperaturas--------
# Calcular el ECM (Error Cuadrático Medio) por canal para temperaturas
ecm_temp_por_canal = {}
rms_temp_por_canal = {}  # Diccionario para almacenar el RMS de la temperatura por canal
for canal, errores_temp in errores_cuadrados_temp_por_canal.items():
   if len(errores_temp) > 0:
       ecm_temp = np.mean(errores_temp)  # Calcular la media de los errores cuadrados de la temperatura para cada canal
       ecm_temp_por_canal[canal] = ecm_temp
       rms_temp_por_canal[canal] = np.sqrt(ecm_temp)  # Calcular la raíz cuadrada del ECM de la temperatura
   else:
       ecm_temp_por_canal[canal] = None
       rms_temp_por_canal[canal] = None  # Si no hay ECM, tampoco se puede calcular el RMS de la temperatura

# Exportar el ECM y RMS por canal a un archivo CSV
ruta_csv_ecm = os.path.join(carpeta_salida, 'resultados_ecm_canales1.csv')
with open(ruta_csv_ecm, mode='w', newline='') as archivo_ecm:
   escritor_ecm = csv.writer(archivo_ecm)
   escritor_ecm.writerow(['Canal', 'ECM Voltaje (µV^2)', 'RMS Voltaje (µV)', 'ECM Temperatura (°C^2)', 'RMS Temperatura (°C)'])  # Añadir encabezado para el RMS de temperatura
   for canal in ecm_por_canal:
       ecm_volt = ecm_por_canal[canal]
       rms_volt = rms_por_canal[canal]
       ecm_temp = ecm_temp_por_canal[canal]
       rms_temp = rms_temp_por_canal[canal]
       escritor_ecm.writerow([canal, ecm_volt, rms_volt, ecm_temp, rms_temp])

#-------Cálculo de status
status_ch = {}  # Diccionario para almacenar el estado del canal

for canal, status_s in rms_temp_por_canal.items(): 
    if status_s is not None:
        if status_s > valor_rms_temp_usuario:
            status_ch[canal] = "FAIL"
        else:
            status_ch[canal] = "OK"
    else: 
        status_ch[canal] = "No Data"

ruta_csv_estatus = os.path.join(carpeta_salida, 'estatus_canales.csv')
with open(ruta_csv_estatus, mode='w', newline='') as archivo_estatus:
    escritor_estatus = csv.writer(archivo_estatus)
    escritor_estatus.writerow(['Canal', 'Estatus'])

    for canal in status_ch:  
        status_123 = status_ch[canal]
        escritor_estatus.writerow([canal, status_123])

# Generar la gráfica de Canales vs. RMS de la temperatura
canales_validos_temp = [canal for canal in rms_temp_por_canal if rms_temp_por_canal[canal] is not None]
rms_validos_temp = [rms_temp_por_canal[canal] for canal in canales_validos_temp]

# Imprimir los datos para lfgrra gráfica
print("Canales válidos para la gráfica:", canales_validos_temp)
print("RMS válidos para la gráfica:", rms_validos_temp)

plt.figure(figsize=(10, 6))  # Tamaño de la figura
plt.plot(canales_validos_temp, rms_validos_temp, marker='o', linestyle='-', color='r')  # Línea roja para RMS temperatura
plt.title('Canales vs. RMS de Temperatura')
plt.xlabel('Canales')
plt.ylabel('RMS de Temperatura (°C)')
plt.ylim(0, 0.4)  # Limitar el eje y desde 0 hasta 0.1 grados Celsius
plt.grid(True)
ruta_grafica = os.path.join(carpeta_salida, 'grafica_rms_temperatura_canales.png')
plt.savefig(ruta_grafica)  # Guardar la gráfica
plt.show()

#-----------------------

voltajes_multimetro = []
voltajes_opc_por_multimetro = []

for lectura in datos:
    voltaje_multimetro = lectura['voltaje_medido']
    voltajes_opc = lectura['voltajes_opc']
    
    voltajes_multimetro.append(voltaje_multimetro)
    voltajes_opc_por_multimetro.append(voltajes_opc)

# Calcular la media y la desviación estándar de los voltajes OPC para cada valor del multímetro
medias_opc = []
desviaciones_opc = []

for voltajes_opc in voltajes_opc_por_multimetro:
    voltajes_opc = [v for v in voltajes_opc if v is not None]  # Excluir valores None
    if voltajes_opc:
        media = np.mean(voltajes_opc)
        desviacion = np.std(voltajes_opc)
    else:
        media = None
        desviacion = None
    medias_opc.append(media)
    desviaciones_opc.append(desviacion)

# Graficar voltaje del multímetro (eje x) vs voltaje OPC (eje y) con barras de error
plt.figure(figsize=(10, 6))
plt.errorbar(voltajes_multimetro, medias_opc, yerr=desviaciones_opc, fmt='o', ecolor='gray', capsize=5, label='Voltajes OPC')

# Personalizar la gráfica
plt.xlabel("Voltaje Multímetro (V)")
plt.ylabel("Voltaje OPC (V)")
plt.title("Voltaje del Multímetro vs Voltajes OPC con Dispersión")
plt.legend()
plt.grid(True)

# Guardar la gráfica en la carpeta de salida
ruta_grafica = os.path.join(carpeta_salida, 'grafica_multimetro_vs_opc.png')
plt.savefig(ruta_grafica)
plt.show()


#------------------------box--------------------------
# ---------------------- Generar CSV de Errores Absolutos Estructurado ----------------------

# Inicializar un diccionario para almacenar errores absolutos organizados por voltaje multímetro
errores_por_voltaje = {}

# Calcular errores absolutos de cada canal respecto al voltaje medido del multímetro
for lectura in datos:
    voltaje_multimetro = lectura['voltaje_medido']  # Voltaje medido por el multímetro (en voltios)
    voltajes_opc = lectura['voltajes_opc']
    
    # Inicializar la lista de errores absolutos para el voltaje actual del multímetro
    if voltaje_multimetro not in errores_por_voltaje:
        errores_por_voltaje[voltaje_multimetro] = []

    # Calcular los errores absolutos por canal
    errores_actuales = []
    for voltaje_opc in voltajes_opc:
        if voltaje_opc is not None:
            voltaje_opc_v = voltaje_opc * 1e-6  # Convertir de microvoltios a voltios
            error_absoluto = abs(voltaje_opc_v - voltaje_multimetro )
            errores_actuales.append(error_absoluto)
        else:
            errores_actuales.append(None)  # Manejar valores faltantes
    
    # Almacenar los errores para el voltaje actual
    errores_por_voltaje[voltaje_multimetro].append(errores_actuales)

# Crear el archivo CSV estructurado para el frontend
ruta_csv_boxplot = os.path.join(carpeta_salida, 'errores_absolutos_por_voltaje_boxplot.csv')
with open(ruta_csv_boxplot, mode='w', newline='') as archivo_csv:
    escritor_csv = csv.writer(archivo_csv)
    
    # Encabezado: el voltaje multímetro y luego los canales
    encabezado = ['Voltaje Multímetro (V)'] + [f'Canal {i}' for i in range(48)]
    escritor_csv.writerow(encabezado)

    # Escribir los datos organizados por voltaje del multímetro
    for voltaje_multimetro, errores_por_lectura in errores_por_voltaje.items():
        # Para cada conjunto de errores por canal, escribir una fila
        for errores in errores_por_lectura:
            escritor_csv.writerow([voltaje_multimetro] + errores)

print(f"Archivo CSV estructurado de errores absolutos guardado en: {ruta_csv_boxplot}")

# ---------------------- Fin de CSV de Errores Absolutos Estructurado ----------------------

# ---------------------- Crear Gráfico Boxplot de Error Absoluto ----------------------


# Preparar datos para el boxplot: lista de errores por canal, agrupados por voltaje del multímetro
voltajes_multimetro = sorted(errores_por_voltaje.keys())
errores_absolutos_por_voltaje = [np.concatenate(errores_por_voltaje[voltaje]) for voltaje in voltajes_multimetro]

# Crear el gráfico boxplot de error absoluto por voltaje
plt.figure(figsize=(15, 8))  # Aumentar el tamaño de la figura para acomodar mejor las etiquetas
plt.boxplot(errores_absolutos_por_voltaje, positions=range(len(voltajes_multimetro)), widths=0.6)  # Ajustar posiciones y ancho

# Configurar los ticks y etiquetas para el eje X
plt.xticks(ticks=range(len(voltajes_multimetro)), labels=[f"{v:.2f}" for v in voltajes_multimetro], rotation=90, ha="right")

# Personalizar la gráfica
plt.xlabel("Voltaje Multímetro (V)")
plt.ylabel("Error Absoluto (V)")
plt.title("Voltaje vs Error Absoluto por Canal (Boxplot)")
plt.grid(True, linestyle="--", alpha=0.5)

# Guardar la gráfica boxplot en la carpeta de salida
ruta_boxplot = os.path.join(carpeta_salida, 'grafica_boxplot_error_absoluto_vs_voltaje.png')
plt.savefig(ruta_boxplot)
plt.tight_layout()  # Ajustar el layout para que ocupe todo el espacio disponible
plt.show()


# ---------------------- Fin de Gráfico Boxplot ----------------------

#------------------------box--------------------------


#--------------------mapa de calor---------------------
# Diccionario para almacenar errores de temperatura por canal y por temperatura de referencia
errores_absolutos_temp = {}

# Calcular los errores absolutos de temperatura y agruparlos por canal y temperatura de referencia
for lectura in datos:
    voltaje_multimetro = lectura['voltaje_medido']  # Voltaje en voltios
    voltajes_opc = lectura['voltajes_opc']

    # Convertir el voltaje del multímetro a temperatura de referencia
    try:
        temperatura_multimetro = convertir_voltaje_a_celsius(voltaje_multimetro * 1e6)  # Pasar a microvoltios para la conversión
    except ValueError:
        continue  # Saltar en caso de error de conversión

    # Inicializar las entradas en el diccionario para cada canal si no existen
    if temperatura_multimetro not in errores_absolutos_temp:
        errores_absolutos_temp[temperatura_multimetro] = [None] * 48  # Crear un arreglo para los 48 canales

    # Calcular el error absoluto de temperatura para cada canal
    for canal, voltaje_opc in enumerate(voltajes_opc[:48]):
        if voltaje_opc is not None:
            try:
                # Convertir el voltaje OPC de microvoltios a temperatura
                temperatura_opc = convertir_voltaje_a_celsius(voltaje_opc)
                # Calcular el error absoluto de temperatura
                error_absoluto_temp = abs(temperatura_opc - temperatura_multimetro)
            except ValueError:
                error_absoluto_temp = None
        else:
            error_absoluto_temp = None

        # Almacenar el error absoluto de temperatura en el diccionario
        errores_absolutos_temp[temperatura_multimetro][canal] = error_absoluto_temp

# Crear el archivo CSV para el mapa de calor de errores absolutos en temperatura
ruta_csv_mapa_calor = os.path.join(carpeta_salida, 'mapa_calor_error_absoluto_temperatura.csv')
with open(ruta_csv_mapa_calor, mode='w', newline='') as archivo_csv:
    escritor_csv = csv.writer(archivo_csv)
    
    # Encabezado: Canal en el eje X y temperatura de referencia en el eje Y
    encabezado = ['Temperatura de Referencia (°C)'] + [f'Canal {i}' for i in range(48)]
    escritor_csv.writerow(encabezado)

    # Escribir los datos de errores absolutos por canal y temperatura de referencia
    for temperatura_ref, errores in sorted(errores_absolutos_temp.items()):
        escritor_csv.writerow([temperatura_ref] + errores)

print(f"Archivo CSV de mapa de calor guardado en: {ruta_csv_mapa_calor}")

# -------- Generar el mapa de calor --------

# Preparar los datos para el mapa de calor en formato de matriz
temperaturas_referencia = sorted(errores_absolutos_temp.keys())  # Temperaturas de referencia para el eje Y
matriz_errores = [errores_absolutos_temp[temp] for temp in temperaturas_referencia]

# Crear la figura del mapa de calor
plt.figure(figsize=(12, 8))
plt.imshow(
    matriz_errores, 
    aspect='auto', 
    cmap='hot', 
    interpolation='nearest',
    origin='lower',  # Establece el origen en la parte inferior
    extent=[0, 47, min(temperaturas_referencia), max(temperaturas_referencia)]  # Asegura que el eje Y esté en el orden correcto
)
plt.colorbar(label='Error Absoluto de Temperatura (°C)')
plt.xlabel('Canales')
plt.ylabel('Temperatura de Referencia (°C)')
plt.title('Mapa de Calor de Error Absoluto de Temperatura por Canal y Temperatura de Referencia')
plt.xticks(ticks=range(0, 48), labels=[f'{i}' for i in range(0, 48)], rotation=90)

# Guardar el mapa de calor en la carpeta de salida
ruta_grafica_mapa_calor = os.path.join(carpeta_salida, 'mapa_calor_error_absoluto_temperatura.png')
plt.savefig(ruta_grafica_mapa_calor)
plt.show()



#--------------------mapa de calor---------------------

#--------------------mapa de calor para error de temperatura con signo---------------------

# Diccionario para almacenar errores de temperatura con signo por canal y por temperatura de referencia
errores_con_signo_temp = {}

# Calcular los errores de temperatura con signo y agruparlos por canal y temperatura de referencia
for lectura in datos:
    voltaje_multimetro = lectura['voltaje_medido']  # Voltaje en voltios
    voltajes_opc = lectura['voltajes_opc']

    # Convertir el voltaje del multímetro a temperatura de referencia
    try:
        temperatura_multimetro = convertir_voltaje_a_celsius(voltaje_multimetro * 1e6)  # Pasar a microvoltios para la conversión
    except ValueError:
        continue  # Saltar en caso de error de conversión

    # Inicializar las entradas en el diccionario para cada canal si no existen
    if temperatura_multimetro not in errores_con_signo_temp:
        errores_con_signo_temp[temperatura_multimetro] = [None] * 48  # Crear un arreglo para los 48 canales

    # Calcular el error de temperatura con signo para cada canal
    for canal, voltaje_opc in enumerate(voltajes_opc[:48]):
        if voltaje_opc is not None:
            try:
                # Convertir el voltaje OPC de microvoltios a temperatura
                temperatura_opc = convertir_voltaje_a_celsius(voltaje_opc)
                # Calcular el error de temperatura con signo
                error_con_signo_temp = temperatura_opc - temperatura_multimetro
            except ValueError:
                error_con_signo_temp = None
        else:
            error_con_signo_temp = None

        # Almacenar el error de temperatura con signo en el diccionario
        errores_con_signo_temp[temperatura_multimetro][canal] = error_con_signo_temp

# Crear el archivo CSV para el mapa de calor de errores de temperatura con signo
ruta_csv_mapa_calor_signo = os.path.join(carpeta_salida, 'mapa_calor_error_temperatura_con_signo.csv')
with open(ruta_csv_mapa_calor_signo, mode='w', newline='') as archivo_csv:
    escritor_csv = csv.writer(archivo_csv)
    
    # Encabezado: Canal en el eje X y temperatura de referencia en el eje Y
    encabezado = ['Temperatura de Referencia (°C)'] + [f'Canal {i}' for i in range(48)]
    escritor_csv.writerow(encabezado)

    # Escribir los datos de errores de temperatura con signo por canal y temperatura de referencia
    for temperatura_ref, errores in sorted(errores_con_signo_temp.items()):
        escritor_csv.writerow([temperatura_ref] + errores)

print(f"Archivo CSV de mapa de calor de errores con signo guardado en: {ruta_csv_mapa_calor_signo}")

# -------- Generar el mapa de calor --------

# Preparar los datos para el mapa de calor en formato de matriz
temperaturas_referencia = sorted(errores_con_signo_temp.keys())  # Temperaturas de referencia para el eje Y
matriz_errores_signo = [errores_con_signo_temp[temp] for temp in temperaturas_referencia]

# Crear la figura del mapa de calor
plt.figure(figsize=(12, 8))
plt.imshow(
    matriz_errores_signo, 
    aspect='auto', 
    cmap='seismic',  # Colormap 'seismic' es útil para visualizar valores positivos y negativos
    interpolation='nearest',
    origin='lower',  # Establece el origen en la parte inferior
    extent=[0, 47, min(temperaturas_referencia), max(temperaturas_referencia)]  # Asegura que el eje Y esté en el orden correcto
)
plt.colorbar(label='Error de Temperatura con Signo (°C)')
plt.xlabel('Canales')
plt.ylabel('Temperatura de Referencia (°C)')
plt.title('Mapa de Calor de Error de Temperatura con Signo por Canal y Temperatura de Referencia')
plt.xticks(ticks=range(0, 48), labels=[f'{i}' for i in range(0, 48)], rotation=90)

# Guardar el mapa de calor en la carpeta de salida
ruta_grafica_mapa_calor_signo = os.path.join(carpeta_salida, 'mapa_calor_error_temperatura_con_signo.png')
plt.savefig(ruta_grafica_mapa_calor_signo)
plt.show()

#--------------------mapa de calor para error de temperatura con signo---------------------




# ------- Fin de la nueva sección de gráfica --------
# Al final del script
print(f"Carpeta de salida: {carpeta_salida}")

