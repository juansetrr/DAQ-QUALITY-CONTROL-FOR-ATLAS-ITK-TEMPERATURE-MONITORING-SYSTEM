import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QLineEdit, QPushButton, QMessageBox, QSizePolicy, QScrollArea
)
from PyQt5.QtGui import QPixmap, QFont, QMovie, QPalette
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
import subprocess
import os
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class WorkerThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, voltage, cycles):
        super().__init__()
        self.voltage = voltage
        self.cycles = cycles

    def run(self):
        proceso_fase3 = subprocess.Popen(
            ["python3", "fase3.py", str(self.voltage), str(self.cycles)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = proceso_fase3.communicate()
        
        if proceso_fase3.returncode == 0:
            proceso_fase4 = subprocess.Popen(
                ["python3", "fase4.py"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout_fase4, stderr_fase4 = proceso_fase4.communicate()
            
            if proceso_fase4.returncode == 0:
                output_folder = ""
                for line in stdout_fase4.decode().splitlines():
                    if "Gráficas y archivos CSV guardados en la carpeta:" in line:
                        output_folder = line.split(":")[-1].strip()
                        break
                self.finished.emit(output_folder)
            else:
                self.finished.emit("Error generating graph in fase4.py.")
        else:
            self.finished.emit("Error in fase3.py process.")

class GraphWidget(QWidget):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.figure.patch.set_facecolor('#1e1e1e')  # Fondo negro de la figura
        self.canvas = FigureCanvas(self.figure)
        
        # Personalizar la barra de herramientas de navegación para que sea azul con texto blanco
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: #0079c2; color: white;")

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1e1e1e')  # Fondo negro de los ejes
        self.ax.tick_params(colors='white')  # Color blanco para las etiquetas de los ejes
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('#61dafb')  # Azul claro para el título

    def update_graph(self, data, title, x_label, y_label):
        self.ax.clear()
        
        # Personalización del boxplot con colores
        boxprops = dict(color='#61dafb', facecolor='#282c34')  # Bordes de las cajas y fondo de las cajas
        medianprops = dict(color='orange', linewidth=2)  # Color de la mediana
        whiskerprops = dict(color='#61dafb')  # Bigotes
        capprops = dict(color='#61dafb')  # Borde de los bigotes
        flierprops = dict(marker='o', markerfacecolor='cyan', markersize=6)  # Outliers
        
        self.ax.boxplot(data, vert=True, patch_artist=True, 
                        boxprops=boxprops, medianprops=medianprops,
                        whiskerprops=whiskerprops, capprops=capprops, flierprops=flierprops)
        
        self.ax.set_title(title, color='#61dafb')
        self.ax.set_xlabel(x_label, color='#61dafb')
        self.ax.set_ylabel(y_label, color='#61dafb')
        
        # Ajustar color de texto y rotación de las etiquetas del eje X
        self.ax.set_xticklabels(self.ax.get_xticks(), rotation=45, ha="right", rotation_mode="anchor")
        
        # Dibujar la cuadrícula
        self.ax.grid(True, linestyle="--", color='#61dafb', alpha=0.3)
        
        # Redibujar el canvas
        self.canvas.draw()

class DashboardVoltage(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.output_folder = ""

    def initUI(self):
        self.setWindowTitle("Dashboard - Voltage")
        self.setGeometry(100, 100, 1200, 800)  # Ajustado el tamaño para acomodar las nuevas secciones
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.setFont(QFont('Arial', 10))

        # Crear una QScrollArea para manejar contenido que exceda la ventana
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        layout = QVBoxLayout(scroll_content)  # Cambiar el layout al contenido del scroll
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # ----- Barra superior -----
        header_frame = QFrame(self)
        header_frame.setStyleSheet("background-color: #0079c2;")
        header_frame.setFixedHeight(130)
        
        atlas_label = QLabel(header_frame)
        atlas_pixmap = QPixmap("images/ATLAS-Logo-White-transparent.png")
        atlas_pixmap = atlas_pixmap.scaled(200, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        atlas_label.setPixmap(atlas_pixmap)
        atlas_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.return_button = QPushButton("Return to Menu", header_frame)
        self.return_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.return_button.setStyleSheet(self.button_style())
        self.return_button.clicked.connect(self.return_to_menu)
        self.return_button.setFixedSize(150, 40)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.addWidget(atlas_label, alignment=Qt.AlignLeft)
        header_layout.addStretch()
        header_layout.addWidget(self.return_button, alignment=Qt.AlignRight)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        layout.addWidget(header_frame)

        # ----- Sección de introducción con imágenes -----
        intro_frame = QFrame(self)
        intro_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
                padding: 20px;
            }
        """)

        # Introducción dentro del frame con QLabel
        intro_label = QLabel(intro_frame)
        intro_label.setTextFormat(Qt.RichText)
        intro_label.setWordWrap(True)
        intro_label.setText(
            "<div style='text-align: justify;'>"
            "The Constant Voltage Mode allows you<br>"
            "to set a steady voltage and specify<br>"
            "the number of cycles, with each cycle<br>"
            "lasting 15 seconds. This configuration<br>"
            "enables you to conduct measurements<br>"
            "over a consistent voltage for a defined<br>"
            "duration, useful for observations<br>"
            "requiring stable voltage conditions<br>"
            "across a set period."
            "</div>"
        )
        intro_label.setFont(QFont('Arial', 16, QFont.Bold))
        intro_label.setAlignment(Qt.AlignCenter)  # Alinear el texto en el centro del frame
        intro_label.setStyleSheet("color: #ffffff;")


        # Layout vertical para la introducción (texto dentro del frame)
        intro_layout = QVBoxLayout(intro_frame)
        intro_layout.addWidget(intro_label)

        # ----- Frames para las imágenes -----
        # Frame para la imagen izquierda
        left_frame = QFrame(self)
        left_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        left_image = QLabel(left_frame)

        # Utilizar QMovie para GIF animado
        left_movie = QMovie("images/image 1703.gif")  # Ruta a la imagen izquierda
        left_movie.setScaledSize(QSize(300, 300))  # Escalar el GIF
        left_image.setMovie(left_movie)
        left_image.setAlignment(Qt.AlignCenter)
        left_movie.start()  # Iniciar la animación del GIF

        left_layout = QVBoxLayout(left_frame)
        left_layout.addWidget(left_image)

        # Frame para la imagen derecha
        right_frame = QFrame(self)
        right_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        right_image = QLabel(right_frame)

        # Utilizar QMovie para GIF animado
        right_movie = QMovie("images/constant_voltage_graph_animation.gif")  # Ruta a la imagen derecha
        right_movie.setScaledSize(QSize(500, 300))  # Escalar el GIF
        right_image.setMovie(right_movie)
        right_image.setAlignment(Qt.AlignCenter)
        right_movie.start()  # Iniciar la animación del GIF

        right_layout = QVBoxLayout(right_frame)
        right_layout.addWidget(right_image)

        # Layout horizontal para imágenes e introducción
        hbox_intro = QHBoxLayout()
        hbox_intro.addWidget(left_frame)
        hbox_intro.addWidget(intro_frame)
        hbox_intro.addWidget(right_frame)
        hbox_intro.setSpacing(20)
        hbox_intro.setContentsMargins(20, 20, 20, 20)

        # Añadir hbox_intro al layout principal
        layout.addLayout(hbox_intro)

        # ----- Sección de parámetros y explicación en horizontal -----
        # Crear un layout horizontal para contener parámetros y explicación
        hbox_parametros_explicacion = QHBoxLayout()
        hbox_parametros_explicacion.setSpacing(20)
        hbox_parametros_explicacion.setContentsMargins(20, 20, 20, 20)

        # ----- Sección de parámetros -----
        parameters_frame = QFrame(self)
        parameters_frame.setStyleSheet("background-color: #2c313c; border-radius: 10px;")
        
        parameters_label = QLabel("Parameters", parameters_frame)
        parameters_label.setFont(QFont('Arial', 16, QFont.Bold))
        parameters_label.setAlignment(Qt.AlignCenter)
        parameters_label.setStyleSheet("color: #61dafb;")
        
        self.voltage_input = QLineEdit(parameters_frame)
        self.voltage_input.setPlaceholderText("Enter voltage")
        self.voltage_input.setStyleSheet(self.input_style())
        
        self.cycles_input = QLineEdit(parameters_frame)
        self.cycles_input.setPlaceholderText("Enter number of cycles")
        self.cycles_input.setStyleSheet(self.input_style())
        
        self.start_button = QPushButton('Start Process', parameters_frame)
        self.start_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.start_button.setStyleSheet(self.button_style())
        self.start_button.clicked.connect(self.start_process)
        
        self.status_label = QLabel('', parameters_frame)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #f44747;")
        self.status_label.setFont(QFont('Arial', 12))
        
        # Añadir botón para abrir la carpeta de resultados
        self.open_folder_button = QPushButton("Open Results Folder", parameters_frame)
        self.open_folder_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.open_folder_button.setStyleSheet(self.button_style())
        self.open_folder_button.clicked.connect(self.abrir_carpeta_resultados)
        self.open_folder_button.setVisible(False)  # Ocultar inicialmente

        parameters_layout = QVBoxLayout(parameters_frame)
        parameters_layout.addWidget(parameters_label)
        parameters_layout.addWidget(self.voltage_input)
        parameters_layout.addWidget(self.cycles_input)
        parameters_layout.addWidget(self.start_button)
        parameters_layout.addWidget(self.status_label)
        parameters_layout.addWidget(self.open_folder_button, alignment=Qt.AlignCenter)
        parameters_layout.setContentsMargins(20, 20, 20, 20)
        
        # ----- Sección de explicación -----
        explicacion_frame = QFrame(self)
        explicacion_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
            }
        """)

        explicacion_label = QLabel("Explanation of Parameters", explicacion_frame)
        explicacion_label.setFont(QFont('Arial', 16, QFont.Bold))
        explicacion_label.setAlignment(Qt.AlignCenter)
        explicacion_label.setStyleSheet("color: #61dafb;")
        
        # Explicación de los parámetros
        explicacion_text = QLabel(
            "• Voltage: The voltage value to be used in the process.\n"
            "• Number of Cycles: The number of cycles for the process.",
            explicacion_frame
        )
        explicacion_text.setWordWrap(True)
        explicacion_text.setAlignment(Qt.AlignLeft)
        explicacion_text.setFont(QFont('Arial', 12))
        explicacion_text.setStyleSheet("color: #dcdcdc;")

        explicacion_layout = QVBoxLayout(explicacion_frame)
        explicacion_layout.addWidget(explicacion_label)
        explicacion_layout.addWidget(explicacion_text)
        explicacion_layout.setContentsMargins(20, 20, 20, 20)

        # Añadir parámetros y explicación al layout horizontal
        hbox_parametros_explicacion.addWidget(parameters_frame, stretch=2)
        hbox_parametros_explicacion.addWidget(explicacion_frame, stretch=3)

        # Añadir el layout horizontal al layout principal
        layout.addLayout(hbox_parametros_explicacion)

        # ----- Crear widgets de gráficas -----
        self.graph_widget_voltages = GraphWidget(self, width=10, height=5, dpi=100)
        self.graph_widget_temperature = GraphWidget(self, width=10, height=5, dpi=100)
        self.graph_widget_voltages.setVisible(False)
        self.graph_widget_temperature.setVisible(False)
        self.graph_widget_heatmap = GraphWidget(self, width=10, height=5, dpi=100)
        self.graph_widget_heatmap.setMinimumSize(200, 200)  # Ajusta según sea necesario
        self.graph_widget_heatmap.setVisible(False)  # Inicialmente oculto
        
        layout.addWidget(self.graph_widget_heatmap)
        layout.addWidget(self.graph_widget_voltages)
        layout.addWidget(self.graph_widget_temperature)

        # ----- Añadir la nueva sección del pie de página (rectángulo al final) -----
        footer_frame = QFrame(self)
        footer_frame.setStyleSheet("background-color: #005a9e; padding: 10px;")
        # No establecer un tamaño fijo para permitir flexibilidad

        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 10, 10, 10)
        footer_layout.setSpacing(10)

        # ----- Parte Superior del Footer -----
        upper_footer_layout = QHBoxLayout()
        upper_footer_layout.setContentsMargins(0, 0, 0, 0)
        upper_footer_layout.setSpacing(20)
        upper_footer_layout.setAlignment(Qt.AlignLeft)

        # Imagen de CERN
        cern_label = QLabel(footer_frame)
        cern_pixmap = QPixmap("images/cern_logo.png")  # Asegúrate de tener esta imagen en la carpeta 'images/'
        if not cern_pixmap.isNull():
            cern_pixmap = cern_pixmap.scaled(100, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            cern_label.setPixmap(cern_pixmap)
        else:
            cern_label.setText("CERN Logo")  # Texto alternativo si la imagen no se carga
            cern_label.setStyleSheet("color: #ffffff;")
        cern_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        upper_footer_layout.addWidget(cern_label)

        # Información de texto (Nombres y Contactos)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        # Nombres de los desarrolladores
        names_label = QLabel("Developed by:\nMateo Alejandro Ruiz Cubides\nJuan Sebastian Cardenas Torres", footer_frame)
        names_label.setFont(QFont('Arial', 10))
        names_label.setStyleSheet("color: #ffffff;")
        names_label.setAlignment(Qt.AlignLeft)
        info_layout.addWidget(names_label)

        # Información de contacto
        contacts_label = QLabel("Contacts:\nruizmateo@javeriana.edu.co\njuanscardenast@javeriana.edu.co", footer_frame)
        contacts_label.setFont(QFont('Arial', 10))
        contacts_label.setStyleSheet("color: #ffffff;")
        contacts_label.setAlignment(Qt.AlignLeft)
        info_layout.addWidget(contacts_label)

        upper_footer_layout.addLayout(info_layout)

        footer_layout.addLayout(upper_footer_layout)

        # ----- Parte Inferior del Footer -----
        experiment_label = QLabel("Experiment ATLAS © 2024 CERN", footer_frame)
        experiment_label.setFont(QFont('Arial', 10, QFont.Bold))
        experiment_label.setStyleSheet("color: #ffffff;")
        experiment_label.setAlignment(Qt.AlignCenter)
        footer_layout.addStretch()  # Añadir stretch para empujar el experiment_label hacia abajo
        footer_layout.addWidget(experiment_label)

        layout.addWidget(footer_frame)
        
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll_area)

    def input_style(self):
        return """
            QLineEdit {
                background-color: #3c3f41;
                border: 1px solid #5c5c5c;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #61dafb;
            }
        """

    def button_style(self):
        return """
            QPushButton {
                background-color: #61dafb;
                color: #000000;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #21a1c4;
            }
            QPushButton:pressed {
                background-color: #1b8ca6;
            }
            QPushButton:disabled {
                background-color: #3c3f41;
                color: #5c5c5c;
            }
        """

    def start_process(self):
        try:
            voltage = float(self.voltage_input.text())
            cycles = int(self.cycles_input.text())

            # Validate voltage range
            if voltage > 1.94410 or voltage < 1.42927:
                QMessageBox.warning(
                    self,
                    "Invalid Voltage Range",
                    "The voltage must be between approximately 1.42927 V (-80°C) and 1.94410 V (60°C)."
                )
                return

            self.start_button.setEnabled(False)
            self.status_label.setText("Process started...")

            self.worker = WorkerThread(voltage, cycles)
            self.worker.finished.connect(self.process_finished)
            self.worker.start()

        except ValueError:
            QMessageBox.critical(self, 'Error', 'Invalid input. Please enter numeric values.')

    def process_finished(self, message_or_folder):
        self.start_button.setEnabled(True)
        if "Error" in message_or_folder:
            self.status_label.setText(message_or_folder)
        else:
            self.output_folder = message_or_folder
            self.status_label.setText("Process completed successfully.")
            # Show the graphs
            self.graph_widget_voltages.setVisible(True)
            self.graph_widget_temperature.setVisible(True)
            self.graph_widget_heatmap.setVisible(True)  # Mostrar el widget del mapa de calor
            self.update_heatmap()  # Actualizar y mostrar el mapa de calor

            self.open_folder_button.setVisible(True)  # Mostrar el botón para abrir la carpeta de resultados
            self.update_graphs()

    def abrir_carpeta_resultados(self):
        if hasattr(self, 'output_folder') and self.output_folder:
            try:
                # Abre la carpeta en el explorador de archivos
                if sys.platform == 'win32':
                    os.startfile(self.output_folder)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', self.output_folder])
                else:
                    subprocess.Popen(['xdg-open', self.output_folder])
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to open folder: {str(e)}')

    def update_graphs(self):
        # Voltage adjusted errors graph
        voltage_csv_path = os.path.join(self.output_folder, 'errores_ajustados_voltios.csv')
        if os.path.exists(voltage_csv_path):
            data_voltages = pd.read_csv(voltage_csv_path)
            channels = [col for col in data_voltages.columns if col.startswith('Canal_')]
            voltage_errors = [data_voltages[col].dropna() for col in channels]
            self.graph_widget_voltages.update_graph(
                voltage_errors,
                'Distribution of Adjusted Error in Each Channel (Volts)',
                'Channels',
                'Adjusted Error (V)'
            )
        
        # Temperature adjusted errors graph
        temperature_csv_path = os.path.join(self.output_folder, 'errores_ajustados_temperatura.csv')
        if os.path.exists(temperature_csv_path):
            data_temperature = pd.read_csv(temperature_csv_path)
            channels = [col for col in data_temperature.columns if col.startswith('Canal_')]
            temperature_errors = [data_temperature[col].dropna() for col in channels]
            self.graph_widget_temperature.update_graph(
                temperature_errors,
                'Distribution of Adjusted Error in Each Channel (Temperature)',
                'Channels',
                'Adjusted Error in Temperature (°C)'
            )
    
    def update_heatmap(self):
        heatmap_csv_path = os.path.join(self.output_folder, 'mapa_calor_error_temperatura.csv')
        if os.path.exists(heatmap_csv_path):
            data_heatmap = pd.read_csv(heatmap_csv_path, index_col=0)
            
            # Configurar el gráfico de mapa de calor
            self.graph_widget_heatmap.ax.clear()
            im = self.graph_widget_heatmap.ax.imshow(
                data_heatmap.values, aspect='auto', cmap='hot', interpolation='nearest'
            )
            
            # Ajustar los límites de los ejes
            self.graph_widget_heatmap.ax.set_xlim(-0.5, data_heatmap.shape[1] - 0.5)
            self.graph_widget_heatmap.ax.set_ylim(-0.5, data_heatmap.shape[0] - 0.5)
            
            # Establecer los ticks correctos en el eje y (ciclos)
            y_ticks = range(data_heatmap.shape[0])
            self.graph_widget_heatmap.ax.set_yticks(y_ticks)
            self.graph_widget_heatmap.ax.set_yticklabels(y_ticks)

            # Remover márgenes de la figura
            self.graph_widget_heatmap.figure.tight_layout(pad=0)

            # Añadir color bar para indicar los valores de error en el mapa de calor
            cbar = self.graph_widget_heatmap.figure.colorbar(im, ax=self.graph_widget_heatmap.ax)
            cbar.set_label('Error Absoluto de Temperatura (°C)', color='#61dafb')
            cbar.ax.yaxis.set_tick_params(color='#61dafb')
            
            # Configuración de etiquetas y título
            self.graph_widget_heatmap.ax.set_title('Mapa de Calor de Error de Temperatura por Canal y Ciclo', color='#61dafb')
            self.graph_widget_heatmap.ax.set_xlabel('Canales', color='#61dafb')
            self.graph_widget_heatmap.ax.set_ylabel('Ciclos', color='#61dafb')

            # Configuración de ticks y bordes
            self.graph_widget_heatmap.ax.tick_params(axis='x', colors='#61dafb')
            self.graph_widget_heatmap.ax.tick_params(axis='y', colors='#61dafb')
            for spine in self.graph_widget_heatmap.ax.spines.values():
                spine.set_color('#61dafb')

            # Dibujar el canvas del mapa de calor
            self.graph_widget_heatmap.canvas.draw_idle()

    def return_to_menu(self):
        self.close()
        try:
            from main_inter import MenuWindow  # Asegúrate de que 'main_inter' y 'MenuWindow' existan y estén correctamente nombrados
            self.menu_window = MenuWindow()
            self.menu_window.show()
        except ImportError:
            QMessageBox.critical(self, 'Error', "No se pudo importar 'MenuWindow' desde 'main_inter.py'.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DashboardVoltage()
    # Cambiar window.show() por window.showMaximized() para abrir maximizado
    window.showMaximized()
    sys.exit(app.exec_())