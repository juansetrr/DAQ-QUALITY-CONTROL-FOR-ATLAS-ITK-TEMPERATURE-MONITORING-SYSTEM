import time
import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import pickle
import sys
import os

# Parámetro: establecer el voltaje objetivo en la fuente
if len(sys.argv) > 1:
    voltaje_objetivo = float(sys.argv[1])
else:
    voltaje_objetivo = 1.5  # Valor por defecto si no se proporciona argumento

# Conectar con la fuente Keysight E36233A y el osciloscopio Keysight DS0X2024A
rm = pyvisa.ResourceManager()
try:
    fuente = rm.open_resource('USB0::0x2A8D::0x3302::MY61004641::0::INSTR')
except pyvisa.errors.VisaIOError as e:
    print(f"Error al conectar con la fuente: {e}")
    sys.exit(1)

try:
    osciloscopio = rm.open_resource('USB0::0x0957::0x1796::MY63080005::0::INSTR')
except pyvisa.errors.VisaIOError as e:
    print(f"Error al conectar con el osciloscopio: {e}")
    fuente.close()
    sys.exit(1)

# Configuración de terminación para el osciloscopio
osciloscopio.read_termination = '\n'
osciloscopio.write_termination = '\n'

# Configuración de la fuente de voltaje
try:
    fuente.write("*RST")  # Resetear la fuente
    fuente.write("INST:NSEL 1")  # Seleccionar el canal 1
    fuente.write(f"VOLT {voltaje_objetivo}")  # Establecer el voltaje deseado
    fuente.write("OUTP ON")  # Encender la salida
    print(f"Voltaje de la fuente establecido en {voltaje_objetivo:.6f} V")
    time.sleep(2)  # Delay para estabilización de la fuente
except pyvisa.errors.VisaIOError as e:
    print(f"Error al configurar la fuente: {e}")
    fuente.close()
    sys.exit(1)

# Configuración básica del osciloscopio para medir en el canal 1
try:
    osciloscopio.write("*RST")  # Reiniciar el osciloscopio
    osciloscopio.write(":CHAN1:DISP ON")  # Activar el canal 1
    osciloscopio.write(":CHAN1:SCAL 0.5")  # Configurar escala del canal a 0.5 V/div
    osciloscopio.write(":CHAN1:OFFS 0")  # Sin offset
    osciloscopio.write(":WAV:FORM ASCII")  # Configurar la salida de datos en ASCII
    osciloscopio.write(":WAV:MODE RAW")  # Usar modo RAW para mayor precisión
    osciloscopio.write(":WAV:SOUR CHAN1")  # Seleccionar el canal 1 como fuente de datos
    print("Configuración del osciloscopio completada.")
except pyvisa.errors.VisaIOError as e:
    print(f"Error al configurar el osciloscopio: {e}")
    osciloscopio.close()
    fuente.write("OUTP OFF")
    fuente.close()
    sys.exit(1)

# Leer datos del osciloscopio y realizar FFT
try:
    # Configurar el rango de puntos para captura
    osciloscopio.write(":WAV:POIN 1000")  # Capturar 1000 puntos
    x_increment = float(osciloscopio.query(":WAV:XINC?"))  # Incremento de tiempo entre muestras
    print(f"Incremento de tiempo entre puntos: {x_increment} segundos")

    # Calcular la frecuencia de muestreo
    fs = 1 / x_increment  # Frecuencia de muestreo (Hz)
    print(f"Frecuencia de muestreo calculada: {fs} Hz")

    # Leer datos de voltaje
    osciloscopio.write(":WAV:DATA?")
    voltajes_raw = osciloscopio.read_raw()
    voltajes_str = voltajes_raw.decode('ascii', errors='ignore')
    if voltajes_str.startswith("#"):
        num_digits = int(voltajes_str[1])
        data_length = int(voltajes_str[2:2+num_digits])
        data_start_index = 2 + num_digits
        voltajes_data = voltajes_str[data_start_index:data_start_index+data_length]
    else:
        voltajes_data = voltajes_str

    # Convertir a un array de valores flotantes
    voltajes = np.array(list(map(float, voltajes_data.strip().split(','))))
    print(f"Datos adquiridos: {len(voltajes)} muestras")

    # Crear el eje de tiempo
    tiempos = np.arange(len(voltajes)) * x_increment  # Eje de tiempo

    # Calcular el valor DC (promedio)
    dc_value = np.mean(voltajes)

    # Calcular la señal de ruido (voltajes menos el valor DC)
    noise_signal = voltajes - dc_value

    # Calcular el RMS del ruido en el dominio del tiempo
    noise_rms = np.sqrt(np.mean(noise_signal ** 2))

    # Realizar la FFT sin aplicar ventana para preservar el componente DC
    N = len(voltajes)
    fft_result = np.fft.rfft(voltajes)
    fft_freqs = np.fft.rfftfreq(N, d=x_increment)

    # Calcular el espectro de amplitud (normalizado)
    fft_magnitude = np.abs(fft_result) / N

    # Multiplicar por 2 (excepto componentes DC y Nyquist si existe)
    if N % 2 == 0:
        fft_magnitude[1:-1] *= 2
    else:
        fft_magnitude[1:] *= 2

    # Calcular el espectro de potencia (amplitud al cuadrado)
    power_spectrum = fft_magnitude ** 2

    # Calcular la potencia de la señal (componente DC)
    signal_power = power_spectrum[0]

    # Calcular la potencia del ruido (suma de las potencias de los demás componentes)
    noise_power = np.sum(power_spectrum[1:])

    # Calcular SNR
    snr = 10 * np.log10(signal_power / noise_power)

    print(f"Valor DC: {dc_value:.6f} V")
    print(f"Voltaje RMS del ruido: {noise_rms:.6f} V")
    print(f"SNR: {snr:.2f} dB")

    # Guardar los datos en un archivo .pkl
    data = {
        'voltajes': voltajes.tolist(),
        'tiempos': tiempos.tolist(),
        'fft_freqs': fft_freqs.tolist(),
        'fft_magnitude': fft_magnitude.tolist(),
        'dc_value': dc_value,
        'noise_rms': noise_rms,
        'snr': snr,
    }

    # Guardar en el mismo directorio que el script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    datos_path = os.path.join(script_dir, 'datosfft3.pkl')
    with open(datos_path, 'wb') as f:
        pickle.dump(data, f)

except Exception as e:
    print(f"Error al leer datos del osciloscopio o calcular FFT: {e}")
    fuente.write("OUTP OFF")
    fuente.close()
    osciloscopio.close()
    sys.exit(1)

# Apagar la fuente y cerrar la conexión
fuente.write("OUTP OFF")
fuente.close()
osciloscopio.close()
