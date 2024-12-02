import sys
import time
import datetime
import elmb_opc_client
import pyvisa
import pickle
import re
import threading  # Para manejar suscripciones en segundo plano

# Validar y obtener los argumentos de la línea de comandos
if len(sys.argv) != 3:
    print("Usage: python3 fase3.py <voltaje> <numero_ciclos>")
    sys.exit(1)

try:
    voltaje_objetivo = float(sys.argv[1])
    numero_ciclos = int(sys.argv[2])
except ValueError:
    print("Error: El voltaje debe ser un número y el número de ciclos un entero.")
    sys.exit(1)

# CLIENTE OPC para el ELMB
client = elmb_opc_client.elmb_opc_client("opc.tcp://localhost.localdomain:48012")
client.Open()

# Conectar con la fuente Keysight E36233A y el multímetro Keithley 2110
rm = pyvisa.ResourceManager()
fuente = rm.open_resource('USB0::0x2A8D::0x3302::MY61004641::0::INSTR')
multimetro = rm.open_resource('USB0::0x05E6::0x2110::8000020::0::INSTR')

# Inicializar listas para almacenar datos
datos = []
voltajes_opc = [None] * 48
datos_opc_actualizados = [False] * 48

# Clase de manejador para la suscripción OPC
class SubscriptionHandler:
    def datachange_notification(self, node, val, data):
        try:
            match = re.search(r'ch(\d+)', node.nodeid.Identifier)
            if match:
                canal = int(match.group(1))
                if canal < 48:
                    voltajes_opc[canal] = val
                    datos_opc_actualizados[canal] = True
                    print(f"Nuevo dato recibido del canal {canal}: {val} V")
        except Exception as e:
            print(f"Error procesando el nodo {node.nodeid.Identifier}: {e}")

# Función para leer voltaje estable del multímetro
def leer_voltaje_estable(multimetro):
    while True:
        lectura1 = float(multimetro.query("MEAS:VOLT:DC?"))
        time.sleep(0.1)
        lectura2 = float(multimetro.query("MEAS:VOLT:DC?"))
        if abs(lectura1 - lectura2) < 0.01:
            return lectura2  *1e6# Evitar multiplicar por 1e6 si no es necesario

# Configurar la fuente de voltaje
fuente.write("*RST")
fuente.write("INST:NSEL 1")
fuente.write("OUTP ON")

# Configurar el voltaje fijo en la fuente
fuente.write(f"VOLT {voltaje_objetivo}")
print(f"Ajustando voltaje de la fuente a {voltaje_objetivo:.6f} V para todos los ciclos")

# Crear la suscripción OPC en un hilo separado
handler = SubscriptionHandler()
subscription = client.client.create_subscription(1000, handler)

canales_a_leer = list(range(0, 48))
for channel in canales_a_leer:
    schn = f"ch{channel}"
    try:
        node = client.nodes["bus1"]["elmb1"]["TPDO3"][schn]
        subscription.subscribe_data_change(node)
        print(f"Suscrito al canal {channel}")
    except Exception as e:
        print(f"No se pudo suscribir al canal {channel}: {e}")

# Hilo para monitorear OPC
def monitor_opc():
    client.client.run()

opc_thread = threading.Thread(target=monitor_opc)
opc_thread.start()

# Iniciar la recolección de datos
print("Iniciando la recolección de datos...")

for ciclo in range(numero_ciclos):
    # Esperar a que el voltaje se estabilice
    time.sleep(2)

    # Leer el voltaje medido con el multímetro
    valor_medido = leer_voltaje_estable(multimetro)

    # Reiniciar las banderas de datos OPC antes de recibir nuevos datos
    datos_opc_actualizados = [False] * 48
    timestamp = datetime.datetime.now().strftime("%d-%H:%M:%S.%f")[:-3]
    
    print(f"Esperando datos OPC para el ciclo {ciclo + 1} con voltaje fijo {voltaje_objetivo:.6f} V...")

    # Espera hasta recibir datos actualizados de todos los canales OPC (con un límite de tiempo)
    timeout = 30  # tiempo de espera máximo en segundos
    start_time = time.time()
    while not all(datos_opc_actualizados):
        if time.time() - start_time > timeout:
            print("Tiempo de espera excedido para datos OPC.")
            break
        time.sleep(0.5)
    
    # Guardar los datos del ciclo
    datos.append({
        'timestamp': timestamp,
        'ciclo': ciclo + 1,
        'voltaje_objetivo': voltaje_objetivo,
        'voltaje_medido': valor_medido,
        'voltajes_opc': voltajes_opc.copy()
    })

    print(f"{timestamp} - Ciclo: {ciclo + 1}, Voltaje fijo: {voltaje_objetivo:.6f} V, Voltaje medido: {valor_medido} V")

# Apagar la fuente y cerrar conexiones
fuente.write("OUTP OFF")
fuente.close()
multimetro.close()
client.Close()

# Detener el hilo de monitoreo OPC
opc_thread.join()

print("Recolección de datos completada.")

# Guardar los datos en un archivo .pkl
with open('datos2.pkl', 'wb') as f:
    pickle.dump(datos, f)
print("Datos guardados en 'datos2.pkl'.")
