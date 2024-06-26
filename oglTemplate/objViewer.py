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
from oglTemplate.objReader import load_obj, calculate_vertex_normals

EXIT_FAILURE = -1


class Scene:
    """
        OpenGL scene class
    """

    def __init__(self, width, height, objPath, scenetitle="Computergrafik"):
        # Allgemeine Einstellungen
        self.scenetitle = scenetitle
        self.width = width
        self.height = height

        # Objekt-spezifische Einstellungen
        self.objPath = objPath          # Pfad zur Objektdatei
        self.indices = None             # Indizes der Dreiecke
        self.vertex_array = None        # Vertex-Array-Objekt

        # Kamera- und Blickrichtung
        self.fovy = 45.0                # Sichtfeld (field of view) in Grad
        self.translation_x = 0          # X-Translation der Kamera

        # Animationseinstellungen
        self.angle_rotation_increment = 15  # Inkrement für die Rotationswinkel
        self.angle_increment = 1
        self.angle = 0
        self.angleX = 0                     # Rotationswinkel um die X-Achse
        self.angleY = 0                     # Rotationswinkel um die Y-Achse
        self.angleZ = 0                     # Rotationswinkel um die Z-Achse
        self.animate = False                # Flag für Animation

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
        # TODO: 
        # 1. Load geometry from file and calc normals if not available
        vertices, faces, normals = load_obj(self, self.objPath)
        if len(normals) == 0:
            normals = calculate_vertex_normals(vertices, faces)

        vertices = np.array(vertices, dtype=np.float32)
        normals = np.array(normals, dtype=np.float32)

        # 2. Load geometry and normals in buffer objects
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
        colors = np.array([
                            0.0, 0.0, 1.0,  # 0. color
                            0.0, 0.0, 1.0,  # 1. color
                            0.0, 0.0, 1.0,  # 2. color
                            0.0, 0.0, 0.0,  # 3. color
                           ], dtype=np.float32)
        col_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, col_buffer)
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)

        # Kanten werden farbig mit diesem Code statt mit colors
        # normals = np.array(normals, dtype=np.float32)
        # norm_buffer = glGenBuffers(1)
        # glBindBuffer(GL_ARRAY_BUFFER, norm_buffer)
        # glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
        # glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        # glEnableVertexAttribArray(1)

        # Index buffer
        # self.indices = np.array([0, 1, 2, 3, 0, 1], dtype=np.int32)
        self.indices = np.array(faces, dtype=np.int32)
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
        # Buffer löschen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.animate:
            # increment rotation angle in each frame
            self.angleX += self.angle_increment

        # Perspektivische oder orthographische Projektion einstellen
        if self.projection_type == 'perspective':
            projection = perspective(self.fovy, self.width / self.height, 1.0, 5.0)
        else:
            projection = ortho(-1.0, 1.0, -1.0, 1.0, -1.0, 5.0)

        # View Matrix einstellen
        view = look_at(0, 0, 2, 0, 0, 0, 0, 1, 0)

        # Modell-Rotations-Transformationen
        model_rotation_x_y_z = rotate_x(self.angleX) @ rotate_y(self.angleY) @ rotate_z(self.angleZ)

        # Modell Translation und Rotation basierend auf Mausbewegungen -> Matrixmanipulation für die Rotation
        model = translate(self.translation_x, 0, 0) @ rotate(self.rotation_alpha, self.rotation_v) @ model_rotation_x_y_z

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
        glDrawElements(GL_TRIANGLES, self.indices.nbytes // 4, GL_UNSIGNED_INT, None)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)           # auskommentieren, wenn man nicht nur die Dreiecke sehen will
        # glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        # unbind the shader and vertex array state
        glUseProgram(0)
        glBindVertexArray(0)


def switch_projection():
    if scene.projection_type == 'perspective':
        print("switch to perspective orthographic")
        scene.projection_type = 'orthographic'
    else:
        scene.projection_type = 'perspective'
        print("switch to perspective perspective")


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
        glClearColor(1, 1, 1, 1)

        # Enable depthtest
        glEnable(GL_DEPTH_TEST)

    def zoom_in(self, zoomFactor):
        if self.scene.fovy - zoomFactor > 0:
            self.scene.fovy -= zoomFactor
        self.scene.draw()

    def zoom_out(self, zoomFactor):
        self.scene.fovy += zoomFactor
        self.scene.draw()

    def on_mouse_scroll(self, yOffset, scrollPos, scrollNeg):
        if yOffset == 0.0: # or scrollNeg == -0.1: für mac-user
            self.zoom_out(1)
        else:
            self.zoom_in(1)

    def on_mouse_button(self, win, button, action, mods):
        print("mouse button: ", win, button, action, mods)

        if button == glfw.MOUSE_BUTTON_RIGHT:
            x, _ = glfw.get_cursor_pos(win)
            if action == glfw.PRESS:
                self.scene.prev_mouse_pos = x  # Setzen der x-maus koordinate

    def on_keyboard(self, win, key, scancode, action, mods):
        print("keyboard: ", win, key, scancode, action, mods)
        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            if key == glfw.KEY_A:
                self.scene.animate = not self.scene.animate
            if key == glfw.KEY_P:
                switch_projection()
            if key == glfw.KEY_S:
                # TODO:
                print("toggle shading: wireframe, grouraud, phong")
            if key == glfw.KEY_X:
                self.scene.angleX += self.scene.angle_rotation_increment
                self.scene.draw()
                print("rotate: x-axis")
            if key == glfw.KEY_Y:
                self.scene.angleY += self.scene.angle_rotation_increment
                self.scene.draw()
                print("rotate: y-axis")
            if key == glfw.KEY_Z:
                self.scene.angleZ += self.scene.angle_rotation_increment
                self.scene.draw()
                print("rotate: z-axis")
            if key == glfw.KEY_I:
                self.zoom_in(5)
            if key == glfw.KEY_O:
                self.zoom_out(5)


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
if __name__ == '__main__':

    if len(sys.argv) < 2:
        # objectPath = sys.argv[1]
        print("presse 'a' to toggle animation...")

        # set size of render viewport
        width, height = 640, 480

        # instantiate a scene
        scene = Scene(width, height, objPath="../models/bunny.obj")

        # pass the scene to a render window ...
        rw = RenderWindow(scene)

        # ... and start main loop
        rw.run()
    else:
        print("Objectpath doesn't exist")
