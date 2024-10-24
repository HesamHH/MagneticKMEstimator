import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QLineEdit,
    QLabel,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QAction,
    QMenu
)
import os
from PyQt5.QtCore import QBuffer, QIODevice
from PyQt5.QtGui import QFont, QPixmap, QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import fiona
import geopandas as gpd
import pyproj
import shapely.affinity
from shapely.geometry import Polygon, LineString, Point
import utm
from shapely.geometry import mapping
from matplotlib.font_manager import FontProperties
from PyQt5.QtCore import Qt

class PlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plot Window")
        self.setGeometry(200, 200, 600, 400)
        self.plot_widget = QWidget(self)
        self.setCentralWidget(self.plot_widget)
        self.figure, self.ax = plt.subplots()  # Store figure and axes
        self.canvas = FigureCanvas(self.figure)
        self.setup_plot()

    def setup_plot(self):
        plot_layout = QVBoxLayout(self.plot_widget)
        plot_layout.addWidget(self.canvas)


class SnapshotWindow(QMainWindow):
    def __init__(self, plot_data, parameters):
        super().__init__()
        self.setWindowTitle("Plot Snapshot")
        self.setGeometry(300, 300, 800, 600)

        layout = QVBoxLayout()
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_widget.setLayout(layout)

        # Display plot
        plot_label = QLabel(self)
        plot_pixmap = QPixmap()
        plot_pixmap.loadFromData(plot_data)
        plot_label.setPixmap(plot_pixmap)
        layout.addWidget(plot_label)

        times_font = QFont("Times New Roman", 12)  # You can adjust the size as needed

        # Display parameters with Times New Roman font
        params_label = QLabel("Parameters:\n" + parameters, self)
        params_label.setFont(times_font)
        layout.addWidget(params_label)
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MKE")


        self.add_about_menu()

        # Initialize attributes
        self.initAttributes()

        # Setup the main window
        self.setupWindow()

        # Setup the central widget and layout
        self.setupCentralWidget()

        # Setup the main interface sections
        self.setupInputsAndControls()
        self.setupLabels()
        self.setupPlotWidget()

        # Set the central widget
        self.setCentralWidget(self.central_widget)

        # Apply stylesheet
        self.applyStylesheet()

    def add_about_menu(self):
        # Create a menu bar
        menubar = self.menuBar()

        # Create About menu
        about_menu = menubar.addMenu('About')

        # Add action to display information about the program
        about_action = QAction('About ArcaSIIMAP', self)
        about_action.triggered.connect(self.show_about_message)
        about_menu.addAction(about_action)

    def show_about_message(self):
        # Display information about the program
        QMessageBox.about(self, "About",
                          "This App is developed by ArcaSIIMAP\n"
                          "for UAV-Borne Magnetometer Price Estimation")
        
    def initAttributes(self):
        self.utm_zone_number = None
        self.kml_file_name = ""

    def setupWindow(self):
        self.setWindowTitle("MKE App")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)

    def setupCentralWidget(self):
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout(self.central_widget)

    def setupInputsAndControls(self):
        # Create a group box for inputs
        input_group_box = QGroupBox("Input Parameters")
        input_layout = QFormLayout()

        # Create input fields
        self.line_spacing_input = QLineEdit()
        self.angle_input = QLineEdit()
        self.margin_input = QLineEdit()
        self.ground_distance_input = QLineEdit()
        self.cross_line_spacing_input = QLineEdit()  # New input field for cross line spacing

        # Set default values as placeholders
        self.line_spacing_input.setPlaceholderText("400")  # Default line spacing
        self.angle_input.setPlaceholderText("0")           # Default rotation angle
        self.margin_input.setPlaceholderText("0")          # Default margin
        self.ground_distance_input.setPlaceholderText("1000")  # Default ground distance
        self.cross_line_spacing_input.setPlaceholderText("500")  # Default cross line spacing

        # Add inputs to the layout
        input_layout.addRow("Line Spacing:", self.line_spacing_input)
        input_layout.addRow("Rotation Angle:", self.angle_input)
        input_layout.addRow("Margin:", self.margin_input)
        input_layout.addRow("Ground Distance:", self.ground_distance_input)
        input_layout.addRow("Cross Line Spacing:", self.cross_line_spacing_input)  # Add cross line spacing to layout

        # Set the layout and add to central layout
        input_group_box.setLayout(input_layout)
        self.central_layout.addWidget(input_group_box)

        # Connect signals
        self.line_spacing_input.editingFinished.connect(self.update_plot)
        self.angle_input.editingFinished.connect(self.update_plot)
        self.margin_input.editingFinished.connect(self.update_plot)
        self.ground_distance_input.editingFinished.connect(self.update_plot)
        self.cross_line_spacing_input.editingFinished.connect(self.update_plot)  # Connect cross line spacing input

        # Buttons
        self.import_button = QPushButton("Import KML")
        self.export_button = QPushButton("Export Lines to KML")
        self.central_layout.addWidget(self.import_button)
        self.central_layout.addWidget(self.export_button)
        self.import_button.clicked.connect(self.import_kml)
        self.export_button.clicked.connect(self.export_lines_to_kml)
        snapshot_button = QPushButton("Take Snapshot", self)
        self.central_layout.addWidget(snapshot_button)
        snapshot_button.clicked.connect(self.take_snapshot)



    def setupLabels(self):
        self.line_count_label = QLabel("Lines: 0")
        self.line_length_label = QLabel("Total Length: 0m")
        self.point_count_label = QLabel("Points: 0")
        self.central_layout.addWidget(self.line_count_label)
        self.central_layout.addWidget(self.line_length_label)
        self.central_layout.addWidget(self.point_count_label)

    def setupPlotWidget(self):
            # Opens the plot in a new window
            self.plot_window = PlotWindow()
            # self.plot_window.show()

    def applyStylesheet(self):
        style = """
            QWidget {
                font-size: 14px;
                font-family: 'Times New Roman';
            }
            QPushButton {
                background-color: #336699;
                color: white;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #4477AA;
            }
            QLineEdit, QCheckBox {
                padding: 5px;
                margin: 5px;
            }
            QGroupBox {
                border: 1px solid silver;
                border-radius: 5px;
                margin-top: 20px;
                padding: 10px;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
        """
        self.setStyleSheet(style)
        self.snapshot_windows = []


    def take_snapshot(self):
        try:
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            self.plot_window.canvas.figure.savefig(buffer, format='png')
            plot_data = buffer.data()

            # Gather parameters as a string
            line_spacing_text = self.line_spacing_input.text() if self.line_spacing_input.text() else "400"
            angle_text = self.angle_input.text() if self.angle_input.text() else "0"
            margin_text = self.margin_input.text() if self.margin_input.text() else "0"
            ground_distance_text = self.ground_distance_input.text() if self.ground_distance_input.text() else "1000"

            parameters = f"Line Spacing: {line_spacing_text}\n" \
                        f"Rotation Angle: {angle_text}\n" \
                        f"Margin: {margin_text}\n" \
                        f"Ground Distance: {ground_distance_text}\n" \
                        f"{self.line_count_label.text()}\n" \
                        f"{self.line_length_label.text()}\n" \
                        f"{self.point_count_label.text()}"

            snapshot_window = SnapshotWindow(plot_data, parameters)
            snapshot_window.show()
            self.snapshot_windows.append(snapshot_window)
        except Exception as e:
            QMessageBox.warning(self, "Error", "Please, add a polygon or change the parameters first.")



    def import_kml(self):
        kml_file_path, _ = QFileDialog.getOpenFileName(
            None, "Select KML File", "", "KML Files (*.kml)"
        )

        if kml_file_path:  # Check if a file is selected
            # Extract the file name from the file path
            kml_file_name_with_extension = os.path.basename(kml_file_path)
            # Split the filename and extension
            root, ext = os.path.splitext(kml_file_name_with_extension)
            # Assign the filename without extension to self.kml_file_name
            self.kml_file_name = root

        try:

            fiona.drvsupport.supported_drivers["KML"] = "rw"
            gdf = gpd.read_file(kml_file_path, driver="KML")
            

            # Extract the polygon geometry
            polygon = gdf.geometry.iloc[0]

            # Get the centroid of the polygon
            centroid = polygon.centroid

            # Get the latitude and longitude of the centroid
            lon, lat = centroid.x, centroid.y

            # Get UTM zone number and zone letter from the centroid's coordinates
            easting, northing, self.utm_zone_number, zone_letter = utm.from_latlon(lat, lon)

            # Define UTM projection
            utm_proj = pyproj.Proj(proj="utm", zone=self.utm_zone_number, ellps="WGS84")

            # Extract the polygon geometry
            polygon = gdf.geometry.iloc[0]
            polygon_coords = list(polygon.exterior.coords)
            polygon_coords = [
                (coord[0], coord[1]) for coord in polygon_coords
            ]  # Extract only (x, y) coordinates
            self.polygon_utm = Polygon(polygon_coords)

            # Convert polygon coordinates to UTM
            polygon_coords_utm = [utm_proj(x, y) for x, y in polygon_coords]
            self.polygon_utm = Polygon(polygon_coords_utm)

            # Plot the polygon and lines
            self.plot_polygon()
        except Exception as e:
            QMessageBox.warning(self, "Error", "Please, choose a file.")

    def ground_points(self, line, ground_distance):
        # Calculate the number of points to be drawn on the line based on ground distance
        num_points = int(line.length / ground_distance)

        # Create an empty list to store the points
        points = []

        # Iterate along the line and add points to the list
        for distance in np.linspace(0, line.length, num_points):
            point = line.interpolate(distance)
            points.append(point)

        return points

    def plot_polygon(self):
        ax = self.plot_window.ax  # Correctly reference the axes
        ax.clear()

        # Set font properties for Times New Roman
        font = FontProperties(family='Times New Roman', size=12)

        # Plot original polygon
        x, y = self.polygon_utm.exterior.xy
        ax.plot(x, y, label="Original Polygon")

        ax.ticklabel_format(style='plain', useOffset=False)
        ax.set_aspect('equal')

        # Plot buffered polygon
        diagonal_length = np.sqrt(self.polygon_utm.area) * 2  # Diagonal length
        buffered_polygon = self.polygon_utm.buffer(diagonal_length)

        # Get line spacing from input field
        line_spacing_text = self.line_spacing_input.text()
        line_spacing = float(line_spacing_text) if line_spacing_text else 400
        cross_line_text = self.cross_line_spacing_input.text()
        cross_line_spacing = float(cross_line_text) if cross_line_text else 500

        # Create lines inside the buffered polygon
        lines, cross_lines = self.create_lines(buffered_polygon, line_spacing, cross_line_spacing)

        # Get rotation angle from input field
        angle_text = self.angle_input.text()
        rotation_angle = float(angle_text) if angle_text else 0

        # Trimmed lines inside the margin polygon
        margin_input_text = self.margin_input.text()
        margin = float(margin_input_text) if margin_input_text else 0
        margin_polygon = self.polygon_utm.buffer(margin)

        # Get ground distance from input field
        ground_distance_text = self.ground_distance_input.text()
        ground_distance = float(ground_distance_text) if ground_distance_text else 1000

        main_line_count = 0  # Initialize main line count
        cross_line_count = 0  # Initialize cross line count
        total_main_line_length_km = 0  # Initialize total main line length in km
        total_cross_line_length_km = 0  # Initialize total cross line length in km
        total_points = 0  # Initialize total points count

        # Plot main lines and count them
        for line in lines:
            rotated_line = shapely.affinity.rotate(line, rotation_angle, origin=buffered_polygon.centroid)
            intersection = rotated_line.intersection(self.polygon_utm)

            if not intersection.is_empty:
                main_line_count += 1
                margin_intersection = rotated_line.intersection(margin_polygon) if margin_input_text else intersection
                if margin_intersection.geom_type == "MultiLineString":
                    for trimmed_line in margin_intersection.geoms:
                        ax.plot(*trimmed_line.xy, color="blue", label="Main Line")
                        total_main_line_length_km += trimmed_line.length / 1000  # Add length in km
                        for point in self.ground_points(trimmed_line, ground_distance):
                            ax.plot(*point.xy, 'o', color='green')
                            total_points += 1
                else:
                    ax.plot(*margin_intersection.xy, color="blue", label="Main Line")
                    total_main_line_length_km += margin_intersection.length / 1000  # Add length in km
                    for point in self.ground_points(margin_intersection, ground_distance):
                        ax.plot(*point.xy, 'o', color='green')
                        total_points += 1

        # Plot cross lines and count them
        for cross_line in cross_lines:
            rotated_cross_line = shapely.affinity.rotate(cross_line, rotation_angle, origin=buffered_polygon.centroid)
            cross_line_intersection = rotated_cross_line.intersection(self.polygon_utm)

            if not cross_line_intersection.is_empty:
                cross_line_count += 1
                if cross_line_intersection.geom_type == "MultiLineString":
                    for cross_rotated_line in cross_line_intersection.geoms:
                        ax.plot(*cross_rotated_line.xy, color="purple", label="Cross Line")
                        total_cross_line_length_km += cross_rotated_line.length / 1000  # Add length in km
                else:
                    ax.plot(*cross_line_intersection.xy, color="purple", label="Cross Line")
                    total_cross_line_length_km += cross_line_intersection.length / 1000  # Add length in km

        # Calculate combined total length
        total_combined_length_km = total_main_line_length_km + total_cross_line_length_km

        # Update the line count label to show main and cross lines separately
        self.line_count_label.setText(f"Main Lines: {main_line_count}, Cross Lines: {cross_line_count}")

        # Update the total length label to include main, cross lines separately, and combined total
        # Update the total length label to include main, cross lines separately, and combined total
        # Update the total length label to include main, cross lines separately, and combined total
        self.line_length_label.setText(
            f"Total Main Line Length (km): {total_main_line_length_km:.2f}\n"
            f"Total Cross Line Length (km): {total_cross_line_length_km:.2f}\n"
            f"Total Combined Length (km): {total_combined_length_km:.2f}")

        self.point_count_label.setText(f"Total Points: {total_points}")

        # Update the legend to show correct labels
        legend_labels = ["Main Lines", "Cross Lines"]
        ax.legend(legend_labels, prop=font)
        ax.set_title(f"Geophysical Flight Path Design For {self.kml_file_name}", fontproperties=font)

        # Apply font to tick labels
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font)

        # Refresh the canvas and display the plot
        self.plot_window.canvas.draw()
        self.plot_window.show()

    def create_lines(self, polygon, line_spacing, cross_line_spacing):
        diagonal_length = np.sqrt(
            (polygon.bounds[2] - polygon.bounds[0]) ** 2
            + (polygon.bounds[3] - polygon.bounds[1]) ** 2
        )
        num_lines = int(diagonal_length / line_spacing)
        lines = []
        cross_lines = []

        # Calculate the middle y-coordinate of the polygon's bounding box
        mid_y = (polygon.bounds[1] + polygon.bounds[3]) / 2

        # Calculate the maximum number of cross lines that can fit within the bounds
        num_cross_lines = int(min(mid_y - polygon.bounds[1], polygon.bounds[3] - mid_y) / cross_line_spacing)

        # Generate main lines
        for i in range(num_lines):
            x_coord = polygon.bounds[0] + i * line_spacing
            line_start = Point(x_coord, polygon.bounds[1])
            line_end = Point(x_coord, polygon.bounds[3])
            line = LineString([line_start, line_end])
            intersection = line.intersection(polygon)
            if not intersection.is_empty:
                if intersection.geom_type == "MultiLineString":
                    lines.extend(intersection.geoms)
                else:
                    lines.append(intersection)

        # Add a cross line at the midpoint
        mid_cross_line_start = Point(polygon.bounds[0], mid_y)
        mid_cross_line_end = Point(polygon.bounds[2], mid_y)
        mid_cross_line = LineString([mid_cross_line_start, mid_cross_line_end])
        intersection_mid_cross = mid_cross_line.intersection(polygon)
        if not intersection_mid_cross.is_empty:
            if intersection_mid_cross.geom_type == "MultiLineString":
                cross_lines.extend(intersection_mid_cross.geoms)
            else:
                cross_lines.append(intersection_mid_cross)

        # Generate cross lines above and below the midpoint
        for j in range(1, num_cross_lines + 1):
            # Create the upper cross line
            upper_cross_line_start = Point(polygon.bounds[0], mid_y + j * cross_line_spacing)
            upper_cross_line_end = Point(polygon.bounds[2], mid_y + j * cross_line_spacing)
            upper_cross_line = LineString([upper_cross_line_start, upper_cross_line_end])
            intersection_upper_cross = upper_cross_line.intersection(polygon)
            if not intersection_upper_cross.is_empty:
                if intersection_upper_cross.geom_type == "MultiLineString":
                    cross_lines.extend(intersection_upper_cross.geoms)
                else:
                    cross_lines.append(intersection_upper_cross)

            # Create the lower cross line
            lower_cross_line_start = Point(polygon.bounds[0], mid_y - j * cross_line_spacing)
            lower_cross_line_end = Point(polygon.bounds[2], mid_y - j * cross_line_spacing)
            lower_cross_line = LineString([lower_cross_line_start, lower_cross_line_end])
            intersection_lower_cross = lower_cross_line.intersection(polygon)
            if not intersection_lower_cross.is_empty:
                if intersection_lower_cross.geom_type == "MultiLineString":
                    cross_lines.extend(intersection_lower_cross.geoms)
                else:
                    cross_lines.append(intersection_lower_cross)

        return lines, cross_lines


    def update_plot(self):
        self.plot_polygon()

    def export_lines_to_kml(self):
        try:
            # Get file path to save the KML file
            save_path, _ = QFileDialog.getSaveFileName(
                None, "Save Lines as KML", "", "KML Files (*.kml)"
            )

            if save_path:
                # Initialize a set to hold unique lines
                unique_lines = set()

                # Plot the polygon to get the current lines displayed on the plot
                self.plot_polygon()

                # Extract lines from the plot excluding the polygon
                for line in self.plot_window.ax.lines:
                    if line.get_label() in ["Main Line", "Cross Line"]:  # Exclude the polygon from export
                        x, y = line.get_data()
                        line_coords = tuple((x[i], y[i]) for i in range(len(x)))
                        unique_lines.add(line_coords)

                # Convert the set back to a list of LineString objects
                all_lines = [LineString(line) for line in unique_lines]

                # Create a GeoDataFrame from the lines
                if all_lines:
                    # Save the DataFrame to KML file
                    fiona.drvsupport.supported_drivers['KML'] = 'rw'
                    fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'
                    gdf_lines = gpd.GeoDataFrame(geometry=all_lines, crs=f'EPSG:326{self.utm_zone_number}')

                    with fiona.open(save_path, 'w', driver='LIBKML', crs=f'EPSG:326{self.utm_zone_number}', schema={'geometry': 'LineString'}) as dst:
                        for line in gdf_lines.geometry:
                            dst.write({'geometry': {'type': 'LineString', 'coordinates': line.coords}})

                    print("Lines exported to KML successfully.")
                else:
                    print("No valid lines found for export.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")



def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()