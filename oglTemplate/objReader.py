import numpy
import numpy as np


def read_obj(self, file):
    vertices = []
    faces = []
    normals = []

    with open(file, 'r') as f:
        for line in f:
            if line.startswith('#') or line in ['\n', '\r\n']:
                continue
            stripped_line = line.strip()
            if stripped_line.startswith('v '):  # Vertices
                vertex = list(map(float, stripped_line[2:].split()))
                vertices.append(vertex)
            elif stripped_line.startswith('f '):  # Faces
                face = stripped_line[2:].split()
                face_indices = [int(index.split('/')[0]) - 1 for index in face]
                faces.append(face_indices)
            elif stripped_line.startswith('vn '):  # Normals
                normal = list(map(float, stripped_line[3:].split()))
                normals.append(normal)

    center = calculate_center(vertices)

    vertices = translate_to_center(vertices, center)
    
    vertices = scale(vertices)

    return vertices, faces, normals

def scale(vertices):
    x_max = max(vertice[0] for vertice in vertices)
    y_max = max(vertice[1] for vertice in vertices)
    z_max = max(vertice[2] for vertice in vertices)

    global_max = max(x_max, y_max, z_max)

    scaling_factor = global_max * 1.5

    for vertice in vertices:
        vertice[0] /= scaling_factor
        vertice[1] /= scaling_factor
        vertice[2] /= scaling_factor

    return vertices


def calculate_normals(vertices, faces):
    normals = []

    for face in faces:
        a_idx, b_idx, c_idx = face
        a = numpy.array(vertices[a_idx])
        b = numpy.array(vertices[b_idx])
        c = numpy.array(vertices[c_idx])

        v1 = b - a
        v2 = c - a

        normal = np.cross(v1, v2)
        normal /= np.linalg.norm(normal)

        normals.append(normal)
    return normals


def calculate_center(vertices):
    num_vertices = len(vertices)
    if num_vertices == 0:
        return [0.0, 0.0, 0.0]

    sum_x, sum_y, sum_z = 0.0, 0.0, 0.0
    for vertex in vertices:
        sum_x += vertex[0]
        sum_y += vertex[1]
        sum_z += vertex[2]

    center_x = sum_x / num_vertices
    center_y = sum_y / num_vertices
    center_z = sum_z / num_vertices

    return [center_x, center_y, center_z]


def translate_to_center(vertices, center):
    translated_vertices = []
    for vertex in vertices:
        translated_vertex = [
            vertex[0] - center[0],
            vertex[1] - center[1],
            vertex[2] - center[2]
        ]
        translated_vertices.append(translated_vertex)

    return translated_vertices
