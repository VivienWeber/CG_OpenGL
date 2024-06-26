import numpy as np


def load_obj(self, file_path):
    """
    Simple function to load an OBJ file and preprocess its vertices,
    returning vertices, faces, and vertex normals.
    """
    vertices = []                           # Liste der Vertices
    normals = []                            # Liste der Normalen
    faces = []                              # Liste der Dreiecke

    with open(file_path, 'r') as file:      # Datei im Lesemodus öffnen
        for line in file:
            if line.startswith('#') or line in ['\n', '\r\n']:
                continue
            stripped_line = line.strip()
            if stripped_line.startswith('v '):
                vertex = list(map(float, stripped_line[2:].split()))
                vertices.append(vertex)
            elif stripped_line.startswith('f '):
                face = stripped_line[2:].split()
                face_indices = [int(index.split('/')[0]) - 1 for index in face]
                faces.append(face_indices)
            elif stripped_line.startswith('vn '):
                normal = list(map(float, stripped_line[3:].split()))
                normals.append(normal)

    # Liste der Vertices in Numpy Array konvertieren
    vertices = np.array(vertices, dtype=np.float32) # Standardtyp für Indizes in OpenGL

    # Mittelpunkt der Vertices berechnen und skalieren
    center = calculate_center(vertices)

    # Vertices zum Mittelpunkt verschieben
    vertices = translate_to_center(vertices, center)

    # Vertices
    vertices = scale(vertices)

    # Vertex-Normalen berechnen
    # normals = calculate_vertex_normals(vertices, faces)

    # Faces als Array
    faces = np.array(faces, dtype=np.int32)

    return vertices, faces, normals


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
