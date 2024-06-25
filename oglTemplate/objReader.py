import numpy as np


def calculate_vertex_normals(vertices, faces):
    """ calculate the normals of the vertices """
    # np.zeros erstellt neues Array und initialisiert alle seine Elemente auf 0
    normals = np.zeros((len(vertices), 3), dtype=np.float32)

    for face in faces:
        # Indizes der drei Eckpunkte der Fläche
        a_index, b_index, c_index = face

        # Koordinaten der drei Eckpunkte holen
        a = np.array(vertices[a_index])
        b = np.array(vertices[b_index])
        c = np.array(vertices[c_index])

        # zwei Vektoren entlang der Kanten der Fläche berechnen
        vec1 = b - a
        vec2 = c - a

        # Kreuzprodukt der beiden Vektoren, um Flächennormale zu erhalten
        normal = np.cross(vec1, vec2)
        # Normale normalisieren (Einheitsvektor)
        normal /= np.linalg.norm(normal)

        # berechnete Normale den Vertices hinzufügen
        normals[a_index] += normal
        normals[b_index] += normal
        normals[c_index] += normal

    # alle Vertex-Normalen normalisieren
    normals = np.array([normal / np.linalg.norm(normal) for normal in normals])

    return normals


def calculate_center(vertices):
    """ calculate the center of the vertices """
    if len(vertices) == 0:
        return [0.0, 0.0, 0.0]

    vertices = np.array(vertices)

    # Mittelwert jeder Spalte (x, y, z) berechnen mit np.mean()
    center = np.mean(vertices, axis=0)

    return center.tolist()


def translate_to_center(vertices, center):
    """ is used to translate a 3D object so that it is located at the origin of the coordinate system (0, 0, 0) """
    vertices = np.array(vertices)
    center = np.array(center)

    # Vertices zum Mittelpunkt verschieben
    translated_vertices = vertices - center

    return translated_vertices.tolist()


def scale(vertices):
    """ Scale the vertices so that they are close to 1.0 """
    vertices = np.array(vertices)

    # maximalen absoluten Koordinatenwert zur Skalierung finden mit np.abs()
    # -> berechnet absoluten Wert eines Arrays, unabhängig vom Vorzeichen
    global_max = np.max(np.abs(vertices))

    # Skalierungsfaktor berechnen
    scaling_factor = global_max * 1.5

    # Vertices skalieren
    scaled_vertices = vertices / scaling_factor

    return scaled_vertices.tolist()


def load_obj(self, file_path):
    """ load object file"""
    vertices = []                           # Liste der Vertices
    normals = []                            # Liste der Normalen
    faces = []                              # Liste der Dreiecke

    with open(file_path, 'r') as file:      # Datei im Lesemodus öffnen
        for line in file:
            if line.startswith('v '):
                parts = line.split()
                # Vertex-Koordinaten der Liste hinzufügen
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif line.startswith('vn '):
                parts = line.split()
                # Normalen-Koordinaten der Liste hinzufügen
                normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif line.startswith('f '):
                parts = line.split()
                face_indices = []           # Liste der Face-Indizes
                for part in parts[1:]:
                    idx = part.split('//')  # Face-Teil in Vertex- und Normalen-Indizes teilen
                    face_indices.append((int(idx[0]) - 1, int(idx[1]) - 1))  # -1 weil Objekte bei Zeile 1 beginnen
                faces.append(face_indices)

    # Listen in numpy Arrays konvertieren (damit kann man besser arbeiten)
    vertices = np.array(vertices, dtype=np.float32)     # Standardtyp für Indizes in OpenGL
    faces = np.array(faces, dtype=np.int32)             # 32 Bits = 4 Bytes
    normals = calculate_vertex_normals(vertices, faces)

    return vertices, normals, faces
