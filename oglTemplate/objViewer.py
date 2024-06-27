"""
/*******************************************************************************
 *
 *            #, #,         CCCCCC  VV    VV MM      MM RRRRRRR
 *           %  %(  #%%#   CC    CC VV    VV MMM    MMM RR    RR
 *           %    %## #    CC        V    V  MM M  M MM RR    RR
 *            ,%      %    CC        VV  VV  MM  MM  MM RRRRRR
 *            (%      %,   CC    CC   VVVV   MM      MM RR   RR
 *              #%    %*    CCCCCC     VV    MM      MM RR    RR
 *             .%    %/
 *                (%.      Computer Vision & Mixed Reality Group
 *
 ******************************************************************************/
/**          @copyright:   Hochschule RheinMain,
 *                         University of Applied Sciences
 *              @author:   Prof. Dr. Ulrich Schwanecke
 *             @version:   0.91
 *                @date:   07.06.2022
 ******************************************************************************/
/**         oglTemplate.py
 *
 *          Simple Python OpenGL program that uses PyOpenGL + GLFW to get an
 *          OpenGL 3.2 core profile context and animate a colored triangle.
 ****
"""
import sys

import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import *

from mat4 import *
from objReader import load_obj, calculate_vertex_normals

EXIT_FAILURE = -1


class Scene:
    """
        OpenGL scene class
    """

    def __init__(self, width, height, objectPath, scenetitle="Computergrafik"):
        # Allgemeine Einstellungen
        self.scenetitle = scenetitle
        self.width = width
        self.height = height

        # Objekt-spezifische Einstellungen
        self.objectPath = objectPath    # Pfad zur Objektdatei
        self.indices = None             # Indizes der Dreiecke
        self.vertex_array = None        # Vertex-Array-Objekt

        # Kamera- und Blickrichtung
        self.fovy = 45.0                # Sichtfeld (field of view) in Grad
        self.translation_x = 0          # X-Translation der Kamera

        # Animationseinstellungen
        self.angle_rotation_increment = 30       # Inkrement für die Rotationswinkel
        self.angle_increment = 5                 # hier die Schnelligkeit der Rotation einstellen
        self.angle = 0
        self.rot_angle_x = 0                     # Rotationswinkel um die X-Achse
        self.rot_angle_y = 0                     # Rotationswinkel um die Y-Achse
        self.rot_angle_z = 0                     # Rotationswinkel um die Z-Achse
        self.animate = False                     # Flag für Animation

        # Mausinteraktion für Rotation
        self.prev_mouse_pos = None              # Vorherige Mausposition
        self.p1 = np.array([1, 1, 1])           # Erster Punkt für Mausrotation
        self.p2 = np.array([1, 1, 1])           # Zweiter Punkt für Mausrotation
        self.rotation_v = np.array([1, 1, 1])   # Rotationsachse für Mausrotation
        self.rotation_alpha = 0.0               # Rotationswinkel für Mausrotation
        self.first_click_done = False           # Flag, ob erster Klick erfolgt ist

        # Projektionstyp (perspektivisch oder orthographisch)
        self.projection_type = 'perspective'    # Aktueller Projektionstyp

    def init_GL(self):
        # setup buffer (vertices, colors, normals, ...)
        self.gen_buffers()  # erzeugt und initialisiert die Pufferobjekte
        # setup shader
        glBindVertexArray(self.vertex_array)
        vertex_shader = open("shader.vert", "r").read()
        fragment_shader = open("shader.frag", "r").read()
        # compileShader() liest und kompiliert die Shader und erstellt ein Shader-Programm
        vertex_prog = compileShader(vertex_shader, GL_VERTEX_SHADER)
        frag_prog = compileShader(fragment_shader, GL_FRAGMENT_SHADER)
        self.shader_program = compileProgram(vertex_prog, frag_prog)

        # unbind vertex array to bind it again in method draw
        glBindVertexArray(0)

    def gen_buffers(self):
        vertices, faces, normals, colors = load_obj(self, self.objectPath)
        if len(normals) == 0:
            normals = calculate_vertex_normals(vertices, faces)

        vertices = np.array(vertices, dtype=np.float32)
        normals = np.array(normals, dtype=np.float32)

        indices = []
        for face in faces:
            for idx in face:
                indices.append(idx)

        # generate vertex array object
        self.vertex_array = glGenVertexArrays(1)
        glBindVertexArray(self.vertex_array)

        # Vertex positions
        pos_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, pos_buffer)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)

        # Vertex normals
        farben = np.array(colors, dtype=np.float32).flatten()  # nicht Listen in Listen sondern nur eine Liste insg.
        norm_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, norm_buffer)
        glBufferData(GL_ARRAY_BUFFER, farben.nbytes, farben, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)

        # Index buffer
        # self.indices = np.array([0, 1, 2, 3, 0, 1], dtype=np.int32)
        # self.indices = np.array(faces, dtype=np.int32)
        # ind_buffer = glGenBuffers(1)
        # glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ind_buffer)
        # glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        # Index buffer
        self.indices = np.array(indices, dtype=np.int32)
        ind_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ind_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        # unbind buffers to bind again in draw()
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def set_size(self, width, height):
        self.width = width
        self.height = height

    def change_projection(self):
        if self.projection_type == 'perspective':
            self.projection_type = 'orthographic'
        else:
            self.projection_type = 'perspective'

    def projectOnSphere(self, x, y, r):
        """
            Arcball-Metapher
        """

        x, y = x - width / 2.0, height / 2.0 - y

        a = min(r * r, x ** 2 + y ** 2)
        z = np.sqrt(r * r - a)
        l = np.sqrt(x ** 2 + y ** 2 + z ** 2)
        if l == 0:
            return x, y, z
        else:
            return x / l, y / l, z / l

    def update_scene(self, win):
        x, y = glfw.get_cursor_pos(win)
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS:
            dx = x - self.prev_mouse_pos
            self.translation_x += dx * 0.002
            self.prev_mouse_pos = x
            self.draw()

            # Klausurrelevant
            # jeder 3D-Punkt hat eine 3D-Normale!
            # beim Flat-Shading bekommt das Face welche Normale? Der erste Vertex vom Dreieck der reinkommt, dessen Vertexnormale definiert die Farbe
            # beim Gouroud-Shading bekommt das Dreieck einen Farbverlauf über die barizentrischen Koordinaten im Dreieck
                # Beleuchtungsmodell wird trotzdem nur für ein Vertex ausgerechnet
            # beim Phong-Shading werden die Normalen auch barizentrisch berechnet -> eine Normale pro Pixel
                # Beleuchtungsmodell wird pro Pixel ausgerechnet

        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
            px, py, pz = self.projectOnSphere(x, y, 500)
            if not self.first_click_done:  # Erster Klick festlegen
                self.p1 = np.array([px, py, pz])
                self.p1 /= np.linalg.norm(self.p1)
                self.first_click_done = True

            else:  # Weitere Bewegungen nach dem ersten Klick
                self.p2 = np.array([px, py, pz])
                self.p2 /= np.linalg.norm(self.p2)
                cross_p1_p2 = np.cross(self.p1, self.p2)
                if not np.allclose(cross_p1_p2, [0, 0, 0]):
                    self.rotation_v = cross_p1_p2

                dot_product = np.dot(self.p1, self.p2)
                if dot_product > -1 and dot_product < 1:
                    alpha = np.arccos(dot_product)
                    if not np.isnan(alpha):
                        self.rotation_alpha = alpha * 100
                self.p2 = np.array([px, py, pz])

        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT) == glfw.RELEASE:
            px, py, pz = self.projectOnSphere(x, y, 1.0)
            self.p1 = np.array([px, py, pz])
            self.p1 /= np.linalg.norm(self.p1)
            self.first_click_done = False

    def draw(self):
        # Buffer löschen (da werden die Informationen reingeladen)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.animate:
            # increment rotation angle in each frame
            self.rot_angle_x += self.angle_increment

        # Perspektivische bzw orthographische Projektion einstellen
        if self.projection_type == 'perspective':
            projection = perspective(self.fovy, self.width / self.height, 1.0, 5.0)
        else:
            projection = ortho(-1.0, 1.0, -1.0, 1.0, -1.0, 5.0)

        # View Matrix einstellen
        view = look_at(0, 0, 2, 0, 0, 0, 0, 1, 0)

        # Modell-Rotations-Transformationen
        model_rotation_x_y_z = rotate_x(self.rot_angle_x) @ rotate_y(self.rot_angle_y) @ rotate_z(self.rot_angle_z)

        # Modell Translation und Rotation basierend auf Mausbewegungen → Matrixmanipulation für die Rotation
        model = translate(self.translation_x, 0, 0) @ rotate(self.rotation_alpha,
                                                             self.rotation_v) @ model_rotation_x_y_z

        # Model-View-Projection Matrix berechnen
        mvp_matrix = projection @ view @ model

        # enable shader & set uniforms
        glUseProgram(self.shader_program)

        # determine location of uniform variable varName
        varLocation = glGetUniformLocation(self.shader_program, 'modelview_projection_matrix')
        # pass value to shader
        glUniformMatrix4fv(varLocation, 1, GL_TRUE, mvp_matrix)

        # Vertex-Array binden und Linien zeichnen
        glBindVertexArray(self.vertex_array)
        # es gibt statt GL_TRIANGLES noch zusätzlich GL_LINE_STRIP (stand vorher drin) und GL_TRIANGLE_STRIP
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)           # auskommentieren, wenn man nicht nur die Dreiecke sehen will
        # glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        # unbind the shader and vertex array state
        glUseProgram(0)
        glBindVertexArray(0)


def switch_projection_type():
    """
        Switches the projection type between perspective and orthographic.
    """

    if scene.projection_type == 'perspective':
        print("Wechsel zu Orhogonal-Projektion")
        scene.projection_type = 'orthographic'
    else:
        scene.projection_type = 'perspective'
        print("Wechsel zu Zentral-Projektion")


#def rotation_matrix(self, axis, theta):
#    axis = axis / np.sqrt(np.dot(axis, axis))
#    a = np.cos(theta / 2.0)
#    b, c, d = -axis * np.sin(theta / 2.0)
#    return np.array([[a * a + b * b - c * c - d * d, 2 * (b * c + a * d), 2 * (b * d - a * c)],
#                     [2 * (b * c - a * d), a * a + c * c - b * b - d * d, 2 * (c * d + a * b)],
#                     [2 * (b * d + a * c), 2 * (c * d - a * b), a * a + d * d - b * b - c * c]])


class RenderWindow:
    """
        GLFW Rendering window class
    """

    def __init__(self, scene):
        # initialize GLFW
        if not glfw.init():
            sys.exit(EXIT_FAILURE)

        # request window with old OpenGL 3.2
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)

        # make a window
        self.width, self.height = scene.width, scene.height
        self.aspect = self.width / self.height
        self.window = glfw.create_window(self.width, self.height, scene.scenetitle, None, None)
        if not self.window:
            glfw.terminate()
            sys.exit(EXIT_FAILURE)

        # Make the window's context current
        glfw.make_context_current(self.window)

        # initialize GL
        self.init_GL()

        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.on_mouse_button)
        glfw.set_key_callback(self.window, self.on_keyboard)
        glfw.set_window_size_callback(self.window, self.on_size)

        # set scroll callback
        glfw.set_scroll_callback(self.window, self.on_mouse_scroll)

        # create scene
        self.scene = scene
        if not self.scene:
            glfw.terminate()
            sys.exit(EXIT_FAILURE)

        self.scene.init_GL()

        # exit flag
        self.exitNow = False

    def init_GL(self):
        # debug: print GL and GLS version
        # print('Vendor       : %s' % glGetString(GL_VENDOR))
        # print('OpenGL Vers. : %s' % glGetString(GL_VERSION))
        # print('GLSL Vers.   : %s' % glGetString(GL_SHADING_LANGUAGE_VERSION))
        # print('Renderer     : %s' % glGetString(GL_RENDERER))

        # set background color to black
        glClearColor(0, 0, 0, 0)

        # Enable depthtest
        glEnable(GL_DEPTH_TEST)

    def reduce_field_of_vision(self, zoomFactor):
        """ Zoom in """
        if self.scene.fovy - zoomFactor > 0:
            self.scene.fovy -= zoomFactor
        self.scene.draw()

    def enlarge_field_of_vision(self, zoomFactor):
        """ Zoom out """
        if self.scene.fovy < 180:
            self.scene.fovy += zoomFactor
            self.scene.draw()
        else:
            print("Verhindern, dass das Objekt gespiegelt und wieder größer wird")

    # für Touchpad-User ": #" wegnehmen
    def on_mouse_scroll(self, yOffset, scrollPos, scrollNeg):
        if yOffset == 0.0 or scrollNeg == -0.1: # für mac-user
            self.enlarge_field_of_vision(1)
        else:
            self.reduce_field_of_vision(1)

    def on_mouse_button(self, win, button, action, mods):
        print("mouse button: ", win, button, action, mods)

        if button == glfw.MOUSE_BUTTON_RIGHT:
            x, _ = glfw.get_cursor_pos(win)
            if action == glfw.PRESS:
                self.scene.prev_mouse_pos = x  # Setzen der x-maus koordinate

            # if button == glfw.MOUSE_BUTTON_MIDDLE and action == glfw.PRESS:
            #     x, y = glfw.get_cursor_pos(win)
            #     self.scene.prev_mouse_pos = (x, y)
            # elif button == glfw.MOUSE_BUTTON_MIDDLE and action == glfw.RELEASE:
            #     self.scene.prev_mouse_pos = None

    def on_keyboard(self, win, key, scancode, action, mods):
        print("keyboard: ", win, key, scancode, action, mods)
        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            if key == glfw.KEY_A:
                self.scene.animate = not self.scene.animate
            if key == glfw.KEY_P:
                switch_projection_type()
            if key == glfw.KEY_S:
                # TODO:
                print("toggle shading: wireframe, grouraud, phong")
            if key == glfw.KEY_X:
                self.scene.rot_angle_x += self.scene.angle_rotation_increment
                self.scene.draw()
                print("Rotiere um die x-Achse")
            if key == glfw.KEY_Y:
                self.scene.rot_angle_y += self.scene.angle_rotation_increment
                self.scene.draw()
                print("Rotiere um die y-Achse")
            if key == glfw.KEY_Z:
                self.scene.rot_angle_z += self.scene.angle_rotation_increment
                self.scene.draw()
                print("Rotiere um die Z-Achse")
            if key == glfw.KEY_I:
                self.reduce_field_of_vision(5)
            if key == glfw.KEY_O:
                self.enlarge_field_of_vision(5)

    def on_size(self, win, width, height):
        self.scene.set_size(width, height)

    def run(self):
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # poll for and process events
            glfw.poll_events()

            # setup viewport
            width, height = glfw.get_framebuffer_size(self.window)
            glViewport(0, 0, width, height)

            # Update the scene based on mouse movement
            self.scene.update_scene(self.window)

            # call the rendering function
            self.scene.draw()

            # swap front and back buffer
            glfw.swap_buffers(self.window)

        # end
        glfw.terminate()


# main function

# TODO PROGRAMM IN KONSOLE AUSFÜHREN:
# cd CG -> cd oglTemplate -> python3 objViewer.py ../models/squirrel.obj
if __name__ == '__main__':

    if len(sys.argv) < 3:
        objectPath = sys.argv[1]
        print("presse 'a' to toggle animation...")

        # set size of render viewport
        width, height = 640, 480

        # instantiate a scene
        scene = Scene(width, height, objectPath)

        # pass the scene to a render window ...
        rw = RenderWindow(scene)

        # ... and start main loop
        rw.run()
    else:
        print("Objectpath doesn't exist")
