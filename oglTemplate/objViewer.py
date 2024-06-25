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
import numpy as np

from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO
from OpenGL.GL.shaders import *

from mat4 import *
from oglTemplate.objReader import load_obj

EXIT_FAILURE = -1


class Scene:
    """
        OpenGL scene class
    """

    def __init__(self, width, height, objPath, scenetitle="Computergrafik"):
        self.objPath = objPath
        self.scenetitle = scenetitle
        self.width = width  # Breite des Fensters
        self.height = height  # Höhe des Fensters
        self.angle = 0  # Winkel der Rotation
        self.angle_increment = 1  # Inkrement für die Rotation
        self.animate = False  # steuert die Animation

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
        vertices, normals, faces = load_obj(self, self.objPath)

        indices = []
        for face in faces:
            for idx in face:
                indices.append(idx[0])

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
        norm_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, norm_buffer)
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)

        # Index buffer
        self.indices = np.array(indices, dtype=np.int32)
        ind_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ind_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

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

    def draw(self):
        # TODO:
        # 1. Render geometry 
        #    (a) just as a wireframe model and 
        #    with 
        #    (b) a shader that realize Gouraud Shading
        #    (c) a shader that realize Phong Shading
        # 2. Rotate object around the x, y, z axis using the keys x, y, z
        # 3. Rotate object with the mouse by realizing the arcball metaphor as 
        #    well as scaling an translation
        # 4. Realize Shadow Mapping
        #

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.animate:
            # increment rotation angle in each frame
            self.angle += self.angle_increment

        # setup matrices
        projection = perspective(45.0, self.width / self.height, 1.0, 5.0)
        view = look_at(0, 0, 2, 0, 0, 0, 0, 1, 0)
        model = rotate_y(self.angle)
        mvp_matrix = projection @ view @ model

        # enable shader & set uniforms
        glUseProgram(self.shader_program)

        # determine location of uniform variable varName
        varLocation = glGetUniformLocation(self.shader_program, 'modelview_projection_matrix')
        # pass value to shader
        glUniformMatrix4fv(varLocation, 1, GL_TRUE, mvp_matrix)

        # enable vertex array & draw triangle(s)
        glBindVertexArray(self.vertex_array)
        # es gibt statt GL_TRIANGLES noch zusätzlich GL_LINE_STRIP (stand vorher drin) und GL_TRIANGLE_STRIP
        glDrawElements(GL_TRIANGLES,len(self.indices), GL_UNSIGNED_INT, None)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)           # auskommentieren, wenn man nicht nur die Dreiecke sehen will
        # glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)         # statt GL_LINE

        # unbind the shader and vertex array state
        glUseProgram(0)
        glBindVertexArray(0)


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

    def on_mouse_button(self, win, button, action, mods):
        print("mouse button: ", win, button, action, mods)
        # TODO: realize arcball metaphor for rotations as well as
        #       scaling and translation paralell to the image plane,
        #       with the mouse.

    def on_keyboard(self, win, key, scancode, action, mods):
        print("keyboard: ", win, key, scancode, action, mods)
        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            if key == glfw.KEY_A:
                self.scene.animate = not self.scene.animate
            if key == glfw.KEY_P:
                # TODO:
                print("toggle projection: orthographic / perspective ")
            if key == glfw.KEY_S:
                # TODO:
                print("toggle shading: wireframe, grouraud, phong")
            if key == glfw.KEY_X:
                # TODO:
                print("rotate: around x-axis")
            if key == glfw.KEY_Y:
                # TODO:
                print("rotate: around y-axis")
            if key == glfw.KEY_Z:
                # TODO:
                print("rotate: around z-axis")

    def on_size(self, win, width, height):
        self.scene.set_size(width, height)

    def run(self):
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # poll for and process events
            glfw.poll_events()

            # setup viewport
            width, height = glfw.get_framebuffer_size(self.window)
            glViewport(0, 0, width, height)

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
