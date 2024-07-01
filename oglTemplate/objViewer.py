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

# To run with python .\objViewer.py ../models/cow.obj

import glfw
import sys

from OpenGL.GL import *
from OpenGL.GL.shaders import *

from objReader import read_obj
from objReader import calculate_normals

from mat4 import *

EXIT_FAILURE = -1


class Scene:
    """
        OpenGL scene class that render a RGB colored tetrahedron.
    """

    def __init__(self, width, height, objPath, scenetitle="Hello Triangle"):
        self.objPath = objPath
        self.prev_mouse_pos = None
        self.scenetitle = scenetitle
        self.width = width
        self.height = height
        self.angle_rotation_increment = 15
        self.angle = 0
        self.angleX = 0
        self.angleY = 0
        self.angleZ = 0
        self.angle_increment = 1
        self.animate = False
        self.fovy = 45.0
        self.translation_x = 0
        self.p1 = np.array([1, 1, 1])
        self.p2 = np.array([1, 1, 1])
        self.rotation_v = np.array([1, 1, 1])
        self.rotation_alpha = 0.0
        self.first_click_done = False
        self.projection_type = 'perspective'
        self.rotation_model = rotate(0, np.array([1,1,1]))

    def init_GL(self):
        # setup buffer (vertices, colors, normals, ...)
        self.gen_buffers()

        # setup shader
        glBindVertexArray(self.vertex_array)
        vertex_shader = open("shader.vert", "r").read()
        fragment_shader = open("shader.frag", "r").read()
        vertex_prog = compileShader(vertex_shader, GL_VERTEX_SHADER)
        frag_prog = compileShader(fragment_shader, GL_FRAGMENT_SHADER)
        self.shader_program = compileProgram(vertex_prog, frag_prog)

        # unbind vertex array to bind it again in method draw
        glBindVertexArray(0)

    def gen_buffers(self):
        # TODO: 
        # 1. Load geometry from file and calc normals if not available
        vertices, faces, normals = read_obj(self, self.objPath)
        if len(normals) == 0:
            normals = calculate_normals(vertices, faces)

        # 2. Load geometry and normals in buffer objects

        # generate vertex array object
        self.vertex_array = glGenVertexArrays(1)
        glBindVertexArray(self.vertex_array)

        # generate and fill buffer with vertex positions (attribute 0)
        positions = np.array(vertices, dtype=np.float32)
        #vbo-buffer
        pos_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, pos_buffer)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)

        # generate and fill buffer with vertex colors (attribute 1)
        colors = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        col_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, col_buffer)
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)

        # generate index buffer (for triangle strip)
        # self.indices = np.array([0, 1, 2, 3, 0, 1], dtype=np.int32)
        self.indices = np.array(faces, dtype=np.int32)
        ind_buffer_object = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ind_buffer_object)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        # unbind buffers to bind again in draw()
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def set_size(self, width, height):
        self.width = width
        self.height = height

    def switch_projection(self):
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
        x, _ = glfw.get_cursor_pos(win)

        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS:
            dx = x - self.prev_mouse_pos
            self.translation_x += dx * 0.002
            self.prev_mouse_pos = x
            self.draw()

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
            self.angleX += self.angle_increment

        if self.projection_type == 'perspective':
            projection = perspective(self.fovy, self.width / self.height, 1.0, 5.0)
        else:
            projection = ortho(-1.0, 1.0, -1.0, 1.0, -1.0, 5.0)

        # setup matrices
        view = look_at(0, 0, 2, 0, 0, 0, 0, 1, 0)

        model_rotation_x_y_z = rotate_x(self.angleX) @ rotate_y(self.angleY) @ rotate_z(self.angleZ)

        model = translate(self.translation_x, 0, 0) @ model_rotation_x_y_z @ self.rotation_model  #matrixmultiplikation 

        #print(self.rotation_alpha)
        mvp_matrix = projection @ view @ model

        # enable shader & set uniforms
        glUseProgram(self.shader_program)

        # determine location of uniform variable varName
        varLocation = glGetUniformLocation(self.shader_program, 'modelview_projection_matrix')
        # pass value to shader
        glUniformMatrix4fv(varLocation, 1, GL_TRUE, mvp_matrix)

        # enable vertex array & draw triangle(s)
        glBindVertexArray(self.vertex_array)

        #Possibilities to change: GL_POINTS, GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP
        #GL_TRIANGLES, GL_LINE_STRIP, GL_TRIANGLE_STRIP
        glDrawElements(GL_TRIANGLES, self.indices.nbytes // 4, GL_UNSIGNED_INT, None)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)  #Adjust here for Fill-Mode like GL_FILL or GL_LINE

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
        glfw.set_scroll_callback(self.window, self.on_mouse_scroll)
        glfw.set_cursor_pos_callback(self.window, self.on_mouse_move)

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
        if (self.scene.fovy - zoomFactor > 0):
            self.scene.fovy -= zoomFactor
        self.scene.draw()

    def zoom_out(self, zoomFactor):
        if self.scene.fovy < 180:
            self.scene.fovy += zoomFactor
            self.scene.draw()

    def on_mouse_scroll(self, win, xOffset, yOffset):
        if (yOffset == -1):
            self.zoom_out(1)
        else:
            self.zoom_in(1)

    def switch_projection(self):
        if scene.projection_type == 'perspective':
            scene.projection_type = 'orthographic'
        else:
            scene.projection_type = 'perspective'

    def on_mouse_button(self, win, button, action, mods):
       # print("mouse button: ", win, button, action, mods)

        if button == glfw.MOUSE_BUTTON_RIGHT:
            x, _ = glfw.get_cursor_pos(win)
            if action == glfw.PRESS:
                self.scene.prev_mouse_pos = x  # Setzen der x-maus koordinate

        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                x, y = glfw.get_cursor_pos(win)
                px, py, pz = scene.projectOnSphere(x, y, 1000)
                scene.p1 = np.array([px, py, pz])
                scene.p1 /= np.linalg.norm(scene.p1)
                scene.first_click_done = True
            
            if action == glfw.RELEASE:
                scene.first_click_done = False



    def on_mouse_move(self, win, x, y):
        if scene.first_click_done:
            px, py, pz = scene.projectOnSphere(x, y, 1000)
            scene.p2 = np.array([px, py, pz])
            scene.p2 /= np.linalg.norm(scene.p2)

            cross_p1_p2 = np.cross(scene.p1, scene.p2)

            if not np.allclose(cross_p1_p2, [0, 0, 0]):
                scene.rotation_v = cross_p1_p2
                dot_product = np.dot(scene.p1, scene.p2)

                alpha = np.arccos(dot_product)
                scene.rotation_alpha = alpha * 10
                scene.p2 = np.array([px, py, pz])

                scene.rotation_model =  rotate(scene.rotation_alpha, scene.rotation_v) @ scene.rotation_model

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
                self.switch_projection()
                # TODO:
                print("toggle projection: orthographic / perspective ")
            if key == glfw.KEY_S:
                # TODO:
                print("toggle shading: wireframe, grouraud, phong")
            if key == glfw.KEY_X:
                self.scene.angleX += self.scene.angle_rotation_increment
                self.scene.draw()
                print("rotate: around x-axis")
            if key == glfw.KEY_Y:
                self.scene.angleY += self.scene.angle_rotation_increment
                self.scene.draw()
                print("rotate: around y-axis")
            if key == glfw.KEY_Z:
                self.scene.angleZ += self.scene.angle_rotation_increment
                self.scene.draw()
                print("rotate: around z-axis")
            if key == glfw.KEY_1:
                self.zoom_in(5)
            if key == glfw.KEY_2:
                self.zoom_out(5)

    def on_size(self, win, width, height):
        self.scene.set_size(width, height)

    def run(self):
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # poll for and process events
            glfw.poll_events()

            # setup viewport
            width, height = glfw.get_framebuffer_size(self.window)
            glViewport(0, 0, width, height);

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
    print("presse 'a' to toggle animation...")

    if len(sys.argv) > 1:
        objPath = sys.argv[1]

        # set size of render viewport
        width, height = 640, 480

        # instantiate a scene
        scene = Scene(width, height, objPath)

        # pass the scene to a render window ...
        rw = RenderWindow(scene)

        # ... and start main loop
        rw.run()
    else:
        print(".obj path not given.")
