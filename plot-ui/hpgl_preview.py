# hpgl_preview.py
import tkinter as tk
import re

class HPGLPreview:
    def __init__(self, canvas, file_path_label):
        self.canvas = canvas
        self.file_path_label = file_path_label
        self.last_x = None
        self.last_y = None

    def draw(self, hpgl_code):
        # Canvas-Größe ermitteln
        self.canvas.update_idletasks()  # Stellen sicher, dass die Canvas-Größe aktualisiert wurde
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Überprüfen, ob die Canvas-Größe korrekt ist
        if canvas_width == 1 or canvas_height == 1:
            print("Fehler: Canvas-Größe konnte nicht abgerufen werden.")
            return

        # Variablen zur Berechnung der maximalen und minimalen Koordinaten
        max_x, max_y, min_x, min_y = -float('inf'), -float('inf'), float('inf'), float('inf')
        
        # Regex, um die HPGL-Befehle zu extrahieren
        pattern = r"(PU|PD)(\d+,\d+(?:,\d+,\d+)*)"
        commands = re.findall(pattern, hpgl_code)

        # Durch die HPGL-Befehle iterieren, um die maximalen und minimalen Koordinaten zu finden
        for command in commands:
            move_type, coords_str = command
            coordinates = coords_str.split(',')
            
            # Bei `PU` und `PD` den Bewegungsbefehl erkennen
            for i in range(0, len(coordinates), 2):
                x = int(coordinates[i])
                y = int(coordinates[i + 1])

                # Maximal- und Minimalwerte anpassen
                max_x = max(max_x, x)
                max_y = max(max_y, y)
                min_x = min(min_x, x)
                min_y = min(min_y, y)

        # Berechne die Breite und Höhe des gesamten Objekts
        obj_width = max_x - min_x
        obj_height = max_y - min_y

        # Skalierungsfaktor basierend auf der Canvas-Größe und der maximalen Dimension des Objekts
        scale_factor = min(canvas_width / obj_width, canvas_height / obj_height) * 0.9

        # Berechne den Offset, um das Objekt innerhalb des Canvas zu zentrieren
        x_offset = (canvas_width - obj_width * scale_factor) / 2 - min_x * scale_factor
        y_offset = (canvas_height - obj_height * scale_factor) / 2 - min_y * scale_factor

        # Canvas zurücksetzen
        self.canvas.delete("all")

        # Startkoordinaten anpassen
        self.last_x, self.last_y = None, None

        # Durch die HPGL-Befehle iterieren, um das Objekt zu zeichnen
        for command in commands:
            move_type, coords_str = command
            coordinates = coords_str.split(',')
            
            # Bei `PU` und `PD` den Bewegungsbefehl erkennen
            for i in range(0, len(coordinates), 2):
                x = int(coordinates[i])
                y = int(coordinates[i + 1])

                # Skalierung anwenden und Y-Achse umkehren (Y wird jetzt von unten nach oben gezählt)
                x = x * scale_factor + x_offset
                y = canvas_height - (y * scale_factor + y_offset)

                # Wählen der Farbe basierend auf dem Befehl: Helles Grün für PU, Schwarz für PD
                line_color = "#66FF66" if move_type == "PU" else "black"

                # Zeichnen der Linie mit entsprechender Farbe
                if self.last_x is not None and self.last_y is not None:
                    self.canvas.create_line(self.last_x, self.last_y, x, y, fill=line_color)

                self.last_x, self.last_y = x, y

        # Diese Zeile ist jetzt nicht mehr nötig, da der file_path nicht mehr gespeichert wird
        # Selbst wenn du den Dateipfad im Label anzeigen möchtest, kannst du ihn an der Stelle übergeben, an der die Datei geladen wird
        # self.file_path_label.config(text=f"Dateipfad: {file_path}")

