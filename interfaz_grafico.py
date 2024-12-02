import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QLineEdit, QPushButton, QMessageBox, QSizePolicy, QScrollArea
)
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor, QMovie
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize

import subprocess
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import pandas as pd
import numpy as np
import mplcursors
import os
import time

class WorkerThread(QThread):
    finished = pyqtSignal(str)  # Signal that emits the output folder path

    def __init__(self, temp_inicio, temp_final, numero_pasos, RMS, Iden):
        super().__init__()
        self.temp_inicio = temp_inicio
        self.temp_final = temp_final
        self.numero_pasos = numero_pasos
        self.Iden = Iden
        self.RMS = RMS

    def run(self):
        # Run fase1.py
        subprocess.call(["python3", "fase1.py", str(self.temp_inicio), str(self.temp_final), str(self.numero_pasos)])
        
        # Run fase2.py and capture the output
        proceso = subprocess.Popen(["python3", "fase2.py", str(self.RMS), str(self.Iden)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proceso.communicate()

        if proceso.returncode == 0:
            # Look for the line containing the output folder
            for line in stdout.decode().splitlines():
                if "Carpeta de salida:" in line:
                    carpeta_salida = line.split("Carpeta de salida:")[-1].strip()
                    # Emit the finished signal with the output folder
                    self.finished.emit(carpeta_salida)
                    return
        else:
            print(f"Error ejecutando fase2.py: {stderr.decode()}")
            self.finished.emit("")  # Emit an empty string in case of error

class GraphWidget(QWidget):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Create the figure and canvas
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvas(self.figure)

        # Customize the figure and axes backgrounds
        self.figure.patch.set_facecolor('#1e1e1e')  # Dark background for the figure
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1e1e1e')  # Dark background for the axes
        self.ax.tick_params(colors='white')  # White color for axis labels
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('#61dafb')  # Light blue for the title

        # Create the navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: #0079c2; color: white;")  # Blue background and white text

        # Add the toolbar and canvas to the layout
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)

    def get_ax(self):
        # Return the axis object
        return self.ax

    def draw(self):
        # Redraw the canvas
        self.canvas.draw()

    def clear(self):
        # Clear the axis
        self.ax.clear()

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.voltaje_cursor = None  # To store the cursor for the second graph

    def initUI(self):

        # Create a QScrollArea
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # Adjust the contained widget automatically
        scroll_content = QWidget()  # This will be the contained widget
        scroll_area.setWidget(scroll_content)

        # Set dark theme
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.setWindowTitle("Dashboard - ATLAS")
        self.setGeometry(100, 100, 1000, 700)

        # Use a modern font
        self.setFont(QFont('Arial', 10))

        # ----- Top Bar -----
        header_frame = QFrame(self)
        header_frame.setStyleSheet("background-color: #0079c2;")
        header_frame.setFixedHeight(130)

        # ATLAS logo aligned to the left
        atlas_label = QLabel(header_frame)
        atlas_pixmap = QPixmap("images/ATLAS-Logo-White-transparent.png")  # Adjust your image path
        atlas_pixmap = atlas_pixmap.scaled(200, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        atlas_label.setPixmap(atlas_pixmap)
        atlas_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # "Return to Menu" button at the top right corner
        self.return_button = QPushButton("Return to Menu", header_frame)
        self.return_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.return_button.setStyleSheet(self.button_style())
        self.return_button.clicked.connect(self.return_to_menu)
        self.return_button.setFixedSize(150, 40)  # Adjust button size

        # Horizontal layout for the top bar
        header_layout = QHBoxLayout(header_frame)
        header_layout.addWidget(atlas_label, alignment=Qt.AlignLeft)  # Logo aligned to the left
        header_layout.addStretch()  # Flexible space in the middle
        header_layout.addWidget(self.return_button, alignment=Qt.AlignRight)  # Button aligned to the right
        header_layout.setContentsMargins(10, 10, 10, 10)

        # ----- Introduction Section with Images -----
        # Frame for the introduction
        intro_frame = QFrame(self)
        intro_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
                padding: 20px;
            }
        """)

        # Introduction text inside the frame using QLabel
        intro_label = QLabel(intro_frame)
        intro_label.setTextFormat(Qt.RichText)
        intro_label.setWordWrap(True)
        intro_label.setText(
            "<div style='text-align: justify;'>"
            "The Temperature Sweep Mode allows you to configure key parameters, such "
            "as the initial and final temperatures, the number of steps, and an RMS limit for "
            "comparison. Throughout the process, precise voltage and temperature data "
            "from multiple channels are collected and processed to calculate relevant "
            "statistics and determine the status of each channel based on the RMS limit. "
            "Finally, graphical visualizations, like heat maps and interactive charts, are "
            "generated to help interpret and evaluate results from the temperature sweep."
            "</div>"
        )
        intro_label.setFont(QFont('Arial', 16, QFont.Bold))
        intro_label.setAlignment(Qt.AlignCenter)  # Center the text within the frame
        intro_label.setStyleSheet("color: #ffffff;")

        # Vertical layout for the introduction text inside the frame
        intro_layout = QVBoxLayout(intro_frame)
        intro_layout.addWidget(intro_label)

        # ----- Frames for Images -----
        # Left image frame
        left_frame = QFrame(self)
        left_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        left_image = QLabel(left_frame)

        # Use QMovie for animated GIF
        left_movie = QMovie("images/image 1703.gif")  # Path to the left image
        left_movie.setScaledSize(QSize(300, 300))  # Scale the GIF
        left_image.setMovie(left_movie)
        left_image.setAlignment(Qt.AlignCenter)
        left_movie.start()  # Start the GIF animation

        left_layout = QVBoxLayout(left_frame)
        left_layout.addWidget(left_image)

        # Right image frame
        right_frame = QFrame(self)
        right_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        right_image = QLabel(right_frame)

        # Use QMovie for animated GIF
        right_movie = QMovie("images/step_graph_color_adjusted_animation.gif")  # Path to the right image
        right_movie.setScaledSize(QSize(500, 300))  # Scale the GIF
        right_image.setMovie(right_movie)
        right_image.setAlignment(Qt.AlignCenter)
        right_movie.start()  # Start the GIF animation

        right_layout = QVBoxLayout(right_frame)
        right_layout.addWidget(right_image)

        # Horizontal layout for images and introduction
        hbox_intro = QHBoxLayout()
        hbox_intro.addWidget(left_frame)
        hbox_intro.addWidget(intro_frame)
        hbox_intro.addWidget(right_frame)
        hbox_intro.setSpacing(20)
        hbox_intro.setContentsMargins(20, 20, 20, 20)

        # ----- Parameters Section -----
        parametros_frame = QFrame(self)
        parametros_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
            }
        """)

        parametros_label = QLabel("Parameters", parametros_frame)
        parametros_label.setFont(QFont('Arial', 16, QFont.Bold))
        parametros_label.setAlignment(Qt.AlignCenter)
        parametros_label.setStyleSheet("color: #61dafb;")  # Neon blue color

        # Inputs for initial temperature, final temperature, number of steps, RMS, and ID
        self.temp_inicio_input = QLineEdit(parametros_frame)
        self.temp_inicio_input.setPlaceholderText("Enter initial temperature")
        self.temp_inicio_input.setStyleSheet(self.input_style())

        self.temp_final_input = QLineEdit(parametros_frame)
        self.temp_final_input.setPlaceholderText("Enter final temperature")
        self.temp_final_input.setStyleSheet(self.input_style())

        self.pasos_input = QLineEdit(parametros_frame)
        self.pasos_input.setPlaceholderText("Enter number of steps")
        self.pasos_input.setStyleSheet(self.input_style())

        self.RMS_input = QLineEdit(parametros_frame)
        self.RMS_input.setPlaceholderText("RMS")
        self.RMS_input.setStyleSheet(self.input_style())

        self.Iden_input = QLineEdit(parametros_frame)
        self.Iden_input.setPlaceholderText("ID")
        self.Iden_input.setStyleSheet(self.input_style())

        # Button to start the process
        self.start_button = QPushButton('Start Process', parametros_frame)
        self.start_button.clicked.connect(self.iniciar_proceso)
        self.start_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.start_button.setStyleSheet(self.button_style())

        # Label to display messages to the user
        self.status_label = QLabel('', parametros_frame)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #f44747;")  # Red color
        self.status_label.setFont(QFont('Arial', 12))

        # Button to open the results folder
        self.open_folder_button = QPushButton("Open Results Folder")
        self.open_folder_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.open_folder_button.setStyleSheet(self.button_style())
        self.open_folder_button.clicked.connect(self.abrir_carpeta_resultados)
        self.open_folder_button.setVisible(False)  # Initially hidden

        # Layout for the parameters
        parametros_layout = QVBoxLayout(parametros_frame)
        parametros_layout.addWidget(parametros_label)
        parametros_layout.addWidget(self.temp_inicio_input)
        parametros_layout.addWidget(self.temp_final_input)
        parametros_layout.addWidget(self.pasos_input)
        parametros_layout.addWidget(self.RMS_input)
        parametros_layout.addWidget(self.Iden_input)
        parametros_layout.addWidget(self.start_button)
        parametros_layout.addWidget(self.status_label)
        parametros_layout.addWidget(self.open_folder_button, alignment=Qt.AlignCenter)
        parametros_layout.setContentsMargins(20, 20, 20, 20)

        # ----- Explanation Section -----
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

        # Explanation of the parameters
        explicacion_text = QLabel(
            "• Initial Temperature: The starting temperature value for the process.\n"
            "• Final Temperature: The ending temperature value for the process.\n"
            "• Number of Steps: The number of increments between the initial and final temperatures.\n"
            "• RMS: Root Mean Square value.\n"
            "• ID: Identifier for the process.",
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

        # ----- Main Horizontal Layout for Parameters and Explanation -----
        hbox_parametros_explicacion = QHBoxLayout()
        hbox_parametros_explicacion.addWidget(parametros_frame)
        hbox_parametros_explicacion.addWidget(explicacion_frame)
        hbox_parametros_explicacion.setSpacing(20)
        hbox_parametros_explicacion.setContentsMargins(20, 20, 20, 20)

        # ----- Channel Status Section -----
        self.channel_status_frame = QFrame(self)
        self.channel_status_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
            }
        """)

        self.channel_status_frame.setVisible(False)  # Initially hidden

        # Layout for channel statuses (horizontal for two columns)
        self.channel_status_layout = QHBoxLayout(self.channel_status_frame)
        self.channel_status_layout.setContentsMargins(20, 20, 20, 20)

        # Create columns SCB - B (channels 0-23) and SCB - A (channels 24-47)
        self.vbox_scb_b = QVBoxLayout()
        self.vbox_scb_a = QVBoxLayout()

        # Title for SCB - B column
        label_scb_b = QLabel("SCB - B")
        label_scb_b.setFont(QFont('Arial', 14, QFont.Bold))
        label_scb_b.setAlignment(Qt.AlignCenter)
        label_scb_b.setStyleSheet("color: #61dafb;")
        self.vbox_scb_b.addWidget(label_scb_b)

        # Title for SCB - A column
        label_scb_a = QLabel("SCB - A")
        label_scb_a.setFont(QFont('Arial', 14, QFont.Bold))
        label_scb_a.setAlignment(Qt.AlignCenter)
        label_scb_a.setStyleSheet("color: #61dafb;")
        self.vbox_scb_a.addWidget(label_scb_a)

        # Add both columns to the main horizontal layout of the channel status section
        self.channel_status_layout.addLayout(self.vbox_scb_b)
        self.channel_status_layout.addLayout(self.vbox_scb_a)

        # Create the first graph widget with navigation toolbar
        self.graph_widget = GraphWidget(self, width=10, height=5, dpi=100)
        self.ax = self.graph_widget.get_ax()  # Get the axis for the first graph

        # Create the second graph widget with navigation toolbar
        self.graph_widget_voltaje = GraphWidget(self, width=10, height=5, dpi=100)
        self.ax_voltaje = self.graph_widget_voltaje.get_ax()  # Get the axis for the second graph

        self.graph_widget.setVisible(False)           # Initially hide the first graph
        self.graph_widget_voltaje.setVisible(False)    # Initially hide the second graph

        # Create the third graph widget with navigation toolbar
        self.graph_widget_error_absoluto = GraphWidget(self, width=10, height=5, dpi=100)
        self.ax_error_absoluto = self.graph_widget_error_absoluto.get_ax()  # Get the axis for the third graph

        self.graph_widget_error_absoluto.setVisible(False)  # Initially hide the third graph

        # Create the fourth graph widget for the heatmap
        self.graph_widget_heatmap = GraphWidget(self, width=10, height=5, dpi=100)
        self.ax_heatmap = self.graph_widget_heatmap.get_ax()  # Get the axis for the heatmap

        self.graph_widget_heatmap.setVisible(False)  # Initially hide the heatmap

        # Main horizontal layout containing the channel status and graphs
        hbox_status_and_graph = QHBoxLayout()

        # Left column: Channel Status
        vbox_status = QVBoxLayout()
        vbox_status.addWidget(self.channel_status_frame)  # Add the channel status frame to the left column
        hbox_status_and_graph.addLayout(vbox_status)  # Add the left column to the main layout

        # Right column: Graphs in a vertical arrangement
        vbox_graph_layout = QVBoxLayout()
        vbox_graph_layout.addWidget(self.graph_widget)  # First graph with toolbar
        vbox_graph_layout.addWidget(self.graph_widget_voltaje)  # Second graph with toolbar
        vbox_graph_layout.addWidget(self.graph_widget_error_absoluto)  # Third graph with toolbar
        vbox_graph_layout.addWidget(self.graph_widget_heatmap)  # Fourth graph (Heatmap)
        hbox_status_and_graph.addLayout(vbox_graph_layout)  # Add the graphs column to the main layout

        # Adjust the relative width of the columns in hbox_status_and_graph
        hbox_status_and_graph.setStretch(0, 2)  # The Channel Status column will be wider
        hbox_status_and_graph.setStretch(1, 3)  # The graphs column will have slightly less space

        # Add layouts and widgets to the main vertical layout
        vbox_main = QVBoxLayout(scroll_content)
        vbox_main.setAlignment(Qt.AlignTop)
        vbox_main.addWidget(header_frame)
        vbox_main.addLayout(hbox_intro)
        vbox_main.addLayout(hbox_parametros_explicacion)
        vbox_main.addLayout(hbox_status_and_graph)
        vbox_main.setSpacing(20)
        vbox_main.setContentsMargins(20, 20, 20, 20)

        # ----- Add the new footer section -----
        # Footer frame
        footer_frame = QFrame(self)
        footer_frame.setStyleSheet("background-color: #005a9e; padding: 10px;")
        # No fixed size to allow flexibility

        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 10, 10, 10)
        footer_layout.setSpacing(10)

        # ----- Upper part of the Footer -----
        upper_footer_layout = QHBoxLayout()
        upper_footer_layout.setContentsMargins(0, 0, 0, 0)
        upper_footer_layout.setSpacing(20)
        upper_footer_layout.setAlignment(Qt.AlignLeft)

        # CERN Image
        cern_label = QLabel(footer_frame)
        cern_pixmap = QPixmap("images/cern_logo.png")  # Ensure this image exists in the 'images/' folder
        if not cern_pixmap.isNull():
            cern_pixmap = cern_pixmap.scaled(100, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            cern_label.setPixmap(cern_pixmap)
        else:
            cern_label.setText("CERN")  # Alternative text if the image doesn't load
            cern_label.setStyleSheet("color: #ffffff;")
        cern_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        upper_footer_layout.addWidget(cern_label)

        # Text information (Names and Contacts)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        # Developers' names
        names_label = QLabel("Developed by:\nMateo Alejandro Ruiz Cubides\nJuan Sebastian Cardenas Torres", footer_frame)
        names_label.setFont(QFont('Arial', 10))
        names_label.setStyleSheet("color: #ffffff;")
        names_label.setAlignment(Qt.AlignLeft)
        info_layout.addWidget(names_label)

        # Contact information
        contacts_label = QLabel("Contacts:\nruizmateo@javeriana.edu.co\njuanscardenast@javeriana.edu.co", footer_frame)
        contacts_label.setFont(QFont('Arial', 10))
        contacts_label.setStyleSheet("color: #ffffff;")
        contacts_label.setAlignment(Qt.AlignLeft)
        info_layout.addWidget(contacts_label)

        upper_footer_layout.addLayout(info_layout)

        footer_layout.addLayout(upper_footer_layout)

        # ----- Lower part of the Footer -----
        experiment_label = QLabel("Experiment ATLAS © 2024 CERN", footer_frame)
        experiment_label.setFont(QFont('Arial', 10, QFont.Bold))
        experiment_label.setStyleSheet("color: #ffffff;")
        experiment_label.setAlignment(Qt.AlignCenter)
        footer_layout.addStretch()  # Add stretch to push the experiment_label down
        footer_layout.addWidget(experiment_label)

        vbox_main.addWidget(footer_frame)
        # End of footer addition

        # Main layout for the entire Dashboard window
        layout_principal = QVBoxLayout(self)
        layout_principal.addWidget(scroll_area)

    def return_to_menu(self):
        self.close()
        from main_inter import MenuWindow  # Import here to avoid circular imports
        self.menu_window = MenuWindow()
        self.menu_window.show()

    def iniciar_proceso(self):
        # Get input values
        try:
            temp_inicio = float(self.temp_inicio_input.text())
            temp_final = float(self.temp_final_input.text())
            numero_pasos = int(self.pasos_input.text())
            Iden = int(self.Iden_input.text())
            valor_RMS = float(self.RMS_input.text())

            # Validate inputs
            if numero_pasos <= 0:
                raise ValueError("Number of steps must be greater than zero.")

            # Validate temperature range
            if not (-80 <= temp_inicio <= 60):
                QMessageBox.warning(self, 'Input Error', 'Initial temperature must be between -80 and 60 degrees Celsius.')
                return  # Exit the function without starting the process

            if not (-80 <= temp_final <= 60):
                QMessageBox.warning(self, 'Input Error', 'Final temperature must be between -80 and 60 degrees Celsius.')
                return  # Exit the function without starting the process

            # Disable the button and show message
            self.start_button.setEnabled(False)
            self.status_label.setText("Process started...")

            # Start the worker thread
            self.worker = WorkerThread(temp_inicio, temp_final, numero_pasos, valor_RMS, Iden)
            self.worker.finished.connect(self.proceso_terminado)
            self.worker.start()

        except ValueError as e:
            QMessageBox.critical(self, 'Input Error', f'Invalid input: {str(e)}')

    def proceso_terminado(self, carpeta_salida):
        # Enable the button and update message
        self.start_button.setEnabled(True)
        if carpeta_salida:
            self.status_label.setText(f"Process completed. Output saved in: {carpeta_salida}")

            # Assign the output folder for the graphs
            self.carpeta_salida = carpeta_salida

            # Show the channel status and all graphs
            self.channel_status_frame.setVisible(True)
            self.graph_widget.setVisible(True)  # Show the first graph
            self.graph_widget_voltaje.setVisible(True)  # Show the second graph
            self.graph_widget_error_absoluto.setVisible(True)  # Show the third graph
            self.graph_widget_heatmap.setVisible(True)  # Show the heatmap
            self.open_folder_button.setVisible(True)  # Show the button to open the results folder

            # Call the update functions for the graphs now that carpeta_salida is defined
            self.update_channel_status()
            self.update_graph()                # Update the first graph
            self.update_graph_voltaje_opc()     # Update the second graph
            self.update_graph_error_absoluto()  # Update the third graph
            self.update_heatmap()               # Update the heatmap

        else:
            self.status_label.setText("Process failed.")

    def abrir_carpeta_resultados(self):
        if hasattr(self, 'carpeta_salida') and self.carpeta_salida:
            try:
                # Open the folder in the file explorer
                if sys.platform == 'win32':
                    os.startfile(self.carpeta_salida)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', self.carpeta_salida])
                else:
                    subprocess.Popen(['xdg-open', self.carpeta_salida])
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to open folder: {str(e)}')

    def update_graph(self):
        # Update the first graph
        try:
            if hasattr(self, 'carpeta_salida'):
                ruta_csv_ecm_canales = os.path.join(self.carpeta_salida, 'resultados_ecm_canales1.csv')
                if os.path.exists(ruta_csv_ecm_canales):
                    data = pd.read_csv(ruta_csv_ecm_canales)
                    # Clear the graph
                    self.ax.clear()
                    # Graph style and plot
                    self.ax.plot(
                        data['Canal'],
                        data['RMS Temperatura (°C)'],
                        marker='o',
                        linestyle='-',
                        color='#61dafb',  # Light blue for the line
                        markerfacecolor='#282c34',
                        markeredgecolor='#61dafb'
                    )
                    self.ax.set_title('Channels vs. RMS Temperature', color='#61dafb')
                    self.ax.set_xlabel('Channels', color='#61dafb')
                    self.ax.set_ylabel('RMS Temperature (°C)', color='#61dafb')
                    self.ax.tick_params(colors='#61dafb')  # Color of the numbers on the axes
                    self.ax.set_ylim(0, 0.3)

                    # Border colors
                    for spine in self.ax.spines.values():
                        spine.set_color('#61dafb')

                    # Redraw the canvas
                    self.graph_widget.draw()  # Update the canvas of the first graph
                else:
                    print(f"The file {ruta_csv_ecm_canales} does not exist.")
            else:
                print("The attribute 'carpeta_salida' does not exist.")
        except Exception as e:
            print(f"Error updating graph: {e}")

    def update_graph_voltaje_opc(self):
        try:
            if hasattr(self, 'carpeta_salida'):
                ruta_csv_voltaje = os.path.join(self.carpeta_salida, 'voltaje_multimetro_vs_opc.csv')
                if os.path.exists(ruta_csv_voltaje):
                    data = pd.read_csv(ruta_csv_voltaje)
                    self.ax_voltaje.clear()

                    # Graph configuration
                    line = self.ax_voltaje.errorbar(
                        data['Voltaje Multímetro (V)'], data['Media Voltaje OPC (V)'],
                        yerr=data['Desviación Voltaje OPC (V)'], fmt='o', ecolor='#61dafb',
                        capsize=5, label='Voltajes OPC', color='#61dafb'
                    )
                    self.ax_voltaje.set_title("Voltaje Multímetro vs Voltajes OPC con Varianza", color='#61dafb')
                    self.ax_voltaje.set_xlabel("Voltaje Multímetro (V)", color='#61dafb')
                    self.ax_voltaje.set_ylabel("Voltaje OPC (V)", color='#61dafb')
                    self.ax_voltaje.tick_params(colors='#61dafb')  # Color of the numbers on the axes
                    self.ax_voltaje.grid(True, linestyle="--", color='#61dafb', alpha=0.3)

                    # Border colors
                    for spine in self.ax_voltaje.spines.values():
                        spine.set_color('#61dafb')

                    # Add interactive cursor
                    if self.voltaje_cursor:
                        self.voltaje_cursor.remove()
                    self.voltaje_cursor = mplcursors.cursor(self.ax_voltaje.lines, hover=True)

                    @self.voltaje_cursor.connect("add")
                    def on_add(sel):
                        x, y = sel.target
                        # Find the closest index to the selected point
                        index = ((data['Voltaje Multímetro (V)'] - x) ** 2 + (data['Media Voltaje OPC (V)'] - y) ** 2).idxmin()
                        multimetro_v = data.loc[index, 'Voltaje Multímetro (V)']
                        opc_v = data.loc[index, 'Media Voltaje OPC (V)']
                        desviacion_opc = data.loc[index, 'Desviación Voltaje OPC (V)']
                        sel.annotation.set_text(
                            f"Voltaje Multímetro: {multimetro_v:.6f} V\n"
                            f"Voltaje OPC: {opc_v:.6f} V\n"
                            f"Desviación: {desviacion_opc:.6f} V"
                        )
                        sel.annotation.get_bbox_patch().set(fc="white", alpha=0.5)

                    # Redraw the canvas
                    self.graph_widget_voltaje.draw()  # Update the canvas of the second graph
                else:
                    print(f"The file {ruta_csv_voltaje} does not exist.")
            else:
                print("The attribute 'carpeta_salida' does not exist.")
        except Exception as e:
            print(f"Error updating Voltaje Multímetro vs OPC graph: {e}")

    def update_graph_error_absoluto(self):
        try:
            if hasattr(self, 'carpeta_salida'):
                ruta_csv_error = os.path.join(self.carpeta_salida, 'errores_absolutos_por_voltaje_boxplot.csv')
                if os.path.exists(ruta_csv_error):
                    data = pd.read_csv(ruta_csv_error)
                    self.ax_error_absoluto.clear()

                    # Transpose data if necessary
                    if 'Voltaje Multímetro (V)' in data.columns:
                        data = data.set_index('Voltaje Multímetro (V)').transpose()

                    # Get voltages and absolute errors
                    voltajes_multimetro = [float(col) for col in data.columns]
                    errores_absolutos = [data[col].dropna().values for col in data.columns]

                    # Boxplot configuration
                    boxprops = dict(color='#61dafb')
                    medianprops = dict(color='orange', linewidth=2)
                    whiskerprops = dict(color='#61dafb')
                    capprops = dict(color='#61dafb')
                    flierprops = dict(marker='o', markerfacecolor='cyan', markersize=6)

                    # Create the boxplot with adjusted positions and width
                    self.ax_error_absoluto.boxplot(
                        errores_absolutos, positions=range(len(voltajes_multimetro)), widths=0.6,
                        boxprops=boxprops, medianprops=medianprops,
                        whiskerprops=whiskerprops, capprops=capprops, flierprops=flierprops
                    )

                    # Graph configuration
                    self.ax_error_absoluto.set_title("Voltaje vs Error Absoluto por Canal (Boxplot)", color='#61dafb')
                    self.ax_error_absoluto.set_xlabel("Voltaje Multímetro (V)", color='#61dafb')
                    self.ax_error_absoluto.set_ylabel("Error Absoluto (V)", color='#61dafb')
                    self.ax_error_absoluto.tick_params(colors='#61dafb')
                    self.ax_error_absoluto.grid(True, linestyle="--", color='#61dafb', alpha=0.3)

                    # Adjust X-axis labels
                    self.ax_error_absoluto.set_xticks(range(len(voltajes_multimetro)))
                    self.ax_error_absoluto.set_xticklabels(
                        [f"{v:.2f}" for v in voltajes_multimetro], rotation=45, ha="right", rotation_mode="anchor"
                    )

                    # Adjust borders
                    for spine in self.ax_error_absoluto.spines.values():
                        spine.set_color('#61dafb')

                    # Redraw the canvas
                    self.graph_widget_error_absoluto.draw()
                else:
                    print(f"The file {ruta_csv_error} does not exist.")
            else:
                print("The attribute 'carpeta_salida' does not exist.")
        except Exception as e:
            print(f"Error updating Error Absoluto vs Voltaje graph: {e}")

    def update_heatmap(self):
        try:
            if hasattr(self, 'carpeta_salida'):
                ruta_csv_mapa_calor = os.path.join(self.carpeta_salida, 'mapa_calor_error_absoluto_temperatura.csv')
                if os.path.exists(ruta_csv_mapa_calor):
                    data = pd.read_csv(ruta_csv_mapa_calor)
                    self.ax_heatmap.clear()

                    # Prepare data for the heatmap
                    temperatura_referencia = data['Temperatura de Referencia (°C)']
                    canales = data.columns[1:]  # Skip the first column which is the reference temperature

                    # Convert data to numpy matrix and handle missing values (optional)
                    matriz_errores = data[canales].to_numpy(dtype=float)

                    # Create the heatmap
                    im = self.ax_heatmap.imshow(
                        matriz_errores, aspect='auto', cmap='hot', interpolation='nearest',
                        extent=[0, 47, temperatura_referencia.min(), temperatura_referencia.max()],
                        origin='lower'
                    )

                    # Add colorbar and adjust
                    cbar = self.graph_widget_heatmap.figure.colorbar(im, ax=self.ax_heatmap)
                    cbar.set_label('Error Absoluto de Temperatura (°C)', color='#61dafb')
                    cbar.ax.yaxis.set_tick_params(color='#61dafb')
                    plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#61dafb')

                    # Labels and title configuration
                    self.ax_heatmap.set_title('Mapa de Calor de Error Absoluto de Temperatura por Canal y Temperatura de Referencia', color='#61dafb')
                    self.ax_heatmap.set_xlabel('Canales', color='#61dafb')
                    self.ax_heatmap.set_ylabel('Temperatura de Referencia (°C)', color='#61dafb')

                    # Ticks configuration on X and Y axes
                    self.ax_heatmap.set_xticks(range(0, 48))  # Channel labels from 0 to 47
                    self.ax_heatmap.set_yticks(np.linspace(temperatura_referencia.min(), temperatura_referencia.max(), len(temperatura_referencia)))

                    # Change color of ticks and numbers on axes
                    self.ax_heatmap.tick_params(axis='x', colors='#61dafb')
                    self.ax_heatmap.tick_params(axis='y', colors='#61dafb')

                    # Adjust borders
                    for spine in self.ax_heatmap.spines.values():
                        spine.set_color('#61dafb')

                    # Redraw the canvas to update the heatmap
                    self.graph_widget_heatmap.draw()
                else:
                    print(f"The file {ruta_csv_mapa_calor} does not exist.")
            else:
                print("The attribute 'carpeta_salida' does not exist.")
        except Exception as e:
            print(f"Error updating heatmap: {e}")

    def update_channel_status(self):
        try:
            ruta_estatus_canales = os.path.join(self.carpeta_salida, 'estatus_canales.csv')
            if os.path.exists(ruta_estatus_canales):
                # Load the CSV file with channel statuses
                status_data = pd.read_csv(ruta_estatus_canales)

                # Clear both columns' layouts without removing the titles
                while self.vbox_scb_b.count() > 1:
                    item = self.vbox_scb_b.takeAt(1)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()

                while self.vbox_scb_a.count() > 1:
                    item = self.vbox_scb_a.takeAt(1)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()

                # Iterate through each channel and its status
                for index, row in status_data.iterrows():
                    canal = row['Canal']
                    status = row['Estatus']

                    # Create a label for each channel
                    channel_label = QLabel(f'Channel {canal}: {status}')
                    channel_label.setFont(QFont('Arial', 12, QFont.Bold))
                    channel_label.setAlignment(Qt.AlignCenter)

                    # Apply color based on the status
                    if status == 'OK':
                        channel_label.setStyleSheet("color: green;")
                    elif status == 'FAIL':
                        channel_label.setStyleSheet("color: red;")
                    else:
                        channel_label.setStyleSheet("color: grey;")

                    # Add the label to the corresponding layout
                    if canal <= 23:
                        self.vbox_scb_b.addWidget(channel_label)
                    else:
                        self.vbox_scb_a.addWidget(channel_label)

            else:
                print("The file estatus_canales.csv does not exist.")
        except Exception as e:
            print(f"Error updating channel status: {e}")

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
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: #000000;
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    # Replace dashboard.show() with dashboard.showMaximized() to open the window maximized
    dashboard.showMaximized()
    sys.exit(app.exec_())
