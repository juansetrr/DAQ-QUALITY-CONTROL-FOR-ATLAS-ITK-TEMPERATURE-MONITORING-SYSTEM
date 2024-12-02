import sys  # Para obtener los argumentos de la línea de comandos
import time
import datetime
import elmb_opc_client
import pyvisa
import numpy as np
import pickle
import re  # Importar para usar expresiones regulares
import math  # Importar para usar funciones matemáticas

# Validar y obtener los argumentos de la línea de comandos
if len(sys.argv) != 4:
    print("Usage: python3 fase1.py <temp_inicio> <temp_final> <numero_pasos>")
    sys.exit(1)

try:
    temp_inicio = float(sys.argv[1])
    temp_final = float(sys.argv[2])
    numero_pasos = int(sys.argv[3])
except ValueError:
    print("Error: Invalid input. Temperatures should be numbers and steps should be an integer.")
    sys.exit(1)

# CLIENTE OPC para el ELMB
client = elmb_opc_client.elmb_opc_client("opc.tcp://localhost.localdomain:48012")
client.Open()

# Conectar con la fuente Keysight E36233A y el multímetro Keithley 2110
rm = pyvisa.ResourceManager()
fuente = rm.open_resource('USB0::0x2A8D::0x3302::MY61004641::0::INSTR')
multimetro = rm.open_resource('USB0::0x05E6::0x2110::8000020::0::INSTR')

# Inicializar listas para almacenar datos
datos = []  # Lista para almacenar todas las lecturas
voltajes_opc = [None] * 47  # Lista para almacenar los voltajes OPC por canal
datos_opc_actualizados = [False] * 47  # Lista para rastrear si los datos OPC han sido actualizados

# Clase de manejador para la suscripción OPC
class SubscriptionHandler:
    def datachange_notification(self, node, val, data):
        try:
            # Usar expresiones regulares para asegurarnos de extraer correctamente el canal
            match = re.search(r'ch(\d+)', node.nodeid.Identifier)
            if match:
                canal = int(match.group(1))  # Extraer el número del canal
                if canal < 47:  # Solo procesar hasta el canal 47
                    valor_en_volts = val 
                    voltajes_opc[canal] = valor_en_volts
                    datos_opc_actualizados[canal] = True  # Marcar el canal como actualizado
                    print(f"Nuevo dato recibido del canal {canal}: {valor_en_volts} V")
        except Exception as e:
            print(f"Error procesando el nodo {node.nodeid.Identifier}: {e}")

# Función para leer voltaje estable del multímetro
def leer_voltaje_estable(multimetro):
    while True:
        lectura1 = float(multimetro.query("MEAS:VOLT:DC?"))
        time.sleep(0.1)
        lectura2 = float(multimetro.query("MEAS:VOLT:DC?"))
        if abs(lectura1 - lectura2) < 0.01:  # Si la diferencia es menor que 0.01V, consideramos estable
            return lectura2

# Configurar la fuente de voltaje
fuente.write("*RST")
fuente.write("INST:NSEL 1")  # Seleccionar el canal 1
fuente.write("OUTP ON")  # Encender la salida

# Nueva función para convertir temperatura a voltaje (no lineal)
def convertir_celsius_a_voltaje(T):
    import math

    # Constante Vref en microvoltios
    Vref = 789000  # 789,000 µV

    R0 = 10e3  # 10,000 Ω

    if T >= 0:
        # Coeficientes para T ≥ 0°C (R ≤ 10kΩ)
        a = 1.027502e-5
        b = 2.353718
        c = -24564.58 - 100 * T
    else:
        # Coeficientes para T < 0°C (R > 10kΩ)
        a = 1.034084e-5
        b = 2.350289
        c = -24536.24 - 100 * T

    # Resolver la ecuación cuadrática a*R^2 + b*R + c = 0
    discriminante = b**2 - 4 * a * c
    if discriminante < 0:
        raise ValueError(f"Discriminante negativo para T={T}°C. No hay solución real para R.")
    else:
        sqrt_disc = math.sqrt(discriminante)
        # Tomamos la raíz positiva
        R = (-b + sqrt_disc) / (2 * a)
        if R <= 0:
            raise ValueError(f"La resistencia R calculada es negativa o cero para T={T}°C.")

    # Calcular volt_microv
    volt_microv = Vref + (R0 * Vref) / R

    # Convertir a voltios
    voltios = volt_microv / 1e6

    return voltios

# Generar la lista de temperaturas y luego convertirlas a voltajes
lista_temperaturas = np.linspace(temp_inicio, temp_final, numero_pasos)
lista_voltajes = []
for temp in lista_temperaturas:
    try:
        voltaje = convertir_celsius_a_voltaje(temp)
        lista_voltajes.append(voltaje)
    except ValueError as e:
        print(f"No se pudo calcular el voltaje para T={temp}°C: {e}")
        sys.exit(1)

# Lista de canales a leer en el cliente OPC (0 a 46)
canales_a_leer = list(range(0, 47))

# Crear la suscripción OPC con el manejador
handler = SubscriptionHandler()
subscription = client.client.create_subscription(1000, handler)

# Suscribirse a todos los canales OPC
for channel in canales_a_leer:
    schn = f"ch{channel}"
    try:
        node = client.nodes["bus1"]["elmb1"]["TPDO3"][schn]
        subscription.subscribe_data_change(node)
        print(f"Suscrito al canal {channel}")
    except Exception as e:
        print(f"No se pudo suscribir al canal {channel}: {e}")

#-----------------------------------------------------------------------------------------------------------------------
# Fase 1: Recolección de datos
print("Iniciando la recolección de datos...")

for temp_objetivo, valor_fuente in zip(lista_temperaturas, lista_voltajes):
    # Ajustar el voltaje en la fuente
    fuente.write(f"VOLT {valor_fuente}")

    # Esperar a que el voltaje se estabilice
    time.sleep(2)  # Esperar 2 segundos para estabilizar el voltaje

    # Leer el voltaje medido con el multímetro
    valor_medido = leer_voltaje_estable(multimetro)

    # Reiniciar las banderas de datos OPC antes de recibir nuevos datos
    datos_opc_actualizados = [False] * 47

    print(f"Esperando datos OPC para la temperatura objetivo de {temp_objetivo}°C...")

    timestamp_inicio = datetime.datetime.now().strftime("%d-%H:%M:%S.%f")[:-3]

    # Esperar a que se reciban datos nuevos de los 47 canales OPC
    while not all(datos_opc_actualizados):
        time.sleep(0.5)  # Verificar cada 0.5 segundos si todos los datos están disponibles

    timestamp_fin = datetime.datetime.now().strftime("%d-%H:%M:%S.%f")[:-3]

    # Guardar los datos en la lista
    datos.append({
        'timestamp_inicio': timestamp_inicio,
        'timestamp_fin': timestamp_fin,
        'temperatura_objetivo': temp_objetivo,
        'voltaje_fuente': valor_fuente,
        'voltaje_medido': valor_medido,
        'voltajes_opc': voltajes_opc.copy()  # Copia profunda de los voltajes OPC actuales
    })

    # Imprimir los resultados en consola
    print(f"{timestamp_fin} - Temperatura objetivo: {temp_objetivo}°C, Voltaje de la fuente: {valor_fuente} V, Voltaje medido: {valor_medido} V")

# Apagar la salida de la fuente y cerrar conexiones (finaliza la recolección de datos)
fuente.write("OUTP OFF")
fuente.close()
multimetro.close()
client.Close()

print("Recolección de datos completada.")

# Guardar 'datos' en un archivo para su posterior procesamiento
with open('datos.pkl', 'wb') as f:
    pickle.dump(datos, f)
