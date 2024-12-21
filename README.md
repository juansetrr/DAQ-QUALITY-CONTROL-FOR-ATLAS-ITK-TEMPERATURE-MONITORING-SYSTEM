Esta carpeta de proyecto es el software desarrollado para el control de calidad de las tarjetas DAQ ELMB del sistema de monitoreo de temperatura ATKLAS-ITK

-La carpeta consta de lo siguiente:

fase1.py --> (Modo barrido de voltaje) recopila datos del elmb a través de sistema de suscripción utilizando el ELMB OPC CLIENT y exportando los datos en un formato pkl

fase2.py --> (Modo barrido de voltaje) hace el procesamiento de los datos provenientes de la fase 1

interfaz_grafico.py -->(Modo barrido de voltaje) es el front end que se encarga de generar la interfaz gráfica para interactuar con los datos de la prueba


fase3.py --> (Modo voltaje constante) recopila datos del elmb a traves de sistema de suscripción utilizando el ELMB OPC CLIENT y exportando los datos en un formato pkl

fase4.py --> (Modo voltaje constante) hace el procesamiento de los datos provenientes de la fase 1

interfaz_grafico_cons.py -->(Modo voltaje constante) es el front end que se encarga de generar la interfaz gráfica para interactuar con los datos de la prueba


noise_analisis.py --> (Modo análisis de ruido) recopila datos del osciloscopio a la entrada de los canales y hace el procesamiento de datos en el mismo código, el código obtiene una señal del osciloscopio y posteriormente realiza un análisis en el dominio de la frecuencia FFT

front_noise.py--> (Modo análisis de ruido) es el front end que se encarga de generar la interfaz gráfica para interactuar con los datos de la prueba


-Archivos pkl y csv: archivos generados por el sistema para el almacenamiento de los datos y respectivo procesamiento, es almacenamiento local, los datos obtenidos de las pruebas se realizan de forma local, se genera una carpeta de proyecto y se pueden explorar gráficas y csv de los datos obtenidos

El presente software es de uso libre, puede ser editado a gusto del usuario, el código se encuentra comentado especificando las funciones de cada línea importante de código.



