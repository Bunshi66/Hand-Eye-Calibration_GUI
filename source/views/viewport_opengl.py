import pyqtgraph.opengl as gl
from OpenGL import GL
from pyqtgraph.opengl import shaders
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np
import pyqtgraph as pg

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QComboBox, QFormLayout,
                             QLineEdit, QTableWidget, QHeaderView, QProgressBar,
                             QDoubleSpinBox, QAbstractItemView, QMessageBox,
                             QTableWidgetItem, QFileDialog)

from PyQt5.QtGui import QVector3D


class CustomShadedShader(shaders.ShaderProgram):
    def __init__(self):
        vert_shader = shaders.VertexShader("""
            uniform mat4 u_mvp;
            uniform mat3 u_normal;
            attribute vec4 a_position;
            attribute vec3 a_normal;
            attribute vec4 a_color;
            varying vec4 v_color;
            varying vec3 v_normal;
            void main() {
                v_normal = normalize(u_normal * a_normal);
                v_color = a_color;
                gl_Position = u_mvp * a_position;
            }
        """)

        frag_shader = shaders.FragmentShader("""
            #ifdef GL_ES
            precision mediump float;
            #endif
            varying vec4 v_color;
            varying vec3 v_normal;
            void main() {
                // Свет направлен из камеры (вдоль оси Z)
                vec3 lightDir = vec3(0.0, 0.0, 1.0);
                float NdotL = abs(dot(v_normal, lightDir));

                // 30% ambient, 70% diffuse для яркого освещения
                float ambient = 0.35;
                float diffuse = NdotL * 0.65;
                float intensity = ambient + diffuse;

                vec3 rgb = v_color.rgb * intensity;
                gl_FragColor = vec4(rgb, v_color.a);
            }
        """)

        super().__init__('cad_shader', [vert_shader, frag_shader])


# Регистрируем шейдер глобально
cad_shader = CustomShadedShader()
shaders.ShaderProgram.names['cad_shader'] = cad_shader

class CustomAxisItem(gl.GLAxisItem):
    """
    Кастомные оси координат с возможностью менять цвета и толщину линий.
    """

    def __init__(self, size=None, width=2.0,
                 color_x=(1, 0, 0, 1),
                 color_y=(0, 1, 0, 1),
                 color_z=(0, 0, 1, 1)):

        # 1. Вызываем родителя. Он попытается дернуть updateLines, но мы защитились (см. ниже)
        super().__init__(size=size)

        # 2. Теперь безопасно присваиваем наши параметры
        self.line_width = width
        self.color_x = color_x
        self.color_y = color_y
        self.color_z = color_z

        # 3. И теперь принудительно вызываем обновление уже с нашими цветами
        self.updateLines()

    def updateLines(self):
        # ЗАЩИТА 1: Убеждаемся, что объект линии уже создан родителем
        if getattr(self, 'lineplot', None) is None:
            return

        # ЗАЩИТА 2: Убеждаемся, что наши цвета уже объявлены (спасает от ошибки при инициализации)
        if not hasattr(self, 'color_z'):
            return

        x, y, z = self.size()

        # Координаты вершин
        pos = np.array([
            [0, 0, 0], [0, 0, z],  # Z axis
            [0, 0, 0], [0, y, 0],  # Y axis
            [0, 0, 0], [x, 0, 0],  # X axis
        ], dtype=np.float32)

        # Цвета
        colors = np.array([
            self.color_z,
            self.color_y,
            self.color_x
        ], dtype=np.float32)

        colors = np.repeat(colors, 2, axis=0)

        # Передаем данные с толщиной
        self.lineplot.setData(pos=pos, color=colors, width=self.line_width)


class GlobalViewport(gl.GLViewWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Базовые настройки
        self.setBackgroundColor('k')

        # Сетка
        self.grid = gl.GLGridItem()
        self.grid.setSize(x=2000, y=2000, z=0)
        self.grid.setSpacing(x=40, y=40)
        self.addItem(self.grid)

        # Оси
        self.axis = CustomAxisItem(
            size=QVector3D(200, 200, 200),
            width=5.0,
            color_x=(1, 0.2, 0.2, 1),
            color_y=(0.2, 1, 0.2, 1),
            color_z=(0.2, 0.2, 1, 1)
        )
        self.addItem(self.axis)

        # Облако точек
        self.scatter = gl.GLScatterPlotItem(pos=np.zeros((1, 3)), color=(0, 1, 0, 1), size=2)
        self.addItem(self.scatter)

        # CAD Mesh - используем встроенный шейдер 'shaded' без краев
        self.cad_mesh_item = gl.GLMeshItem(
            smooth=True,
            shader='cad_shader',  # Встроенный шейдер с освещением
            drawEdges=True,  # Отключаем края полигонов
            drawFaces=True,  # Рисуем грани
            glOptions='opaque',
            computeNormals=True
        )
        self.cad_mesh_item.hide()
        self.addItem(self.cad_mesh_item)

        # Параметры камеры
        self.default_cam_pos = pg.Vector(0, 0, 0)
        self.default_cam_dist = 100
        self.default_cam_elev = -90
        self.default_cam_azim = -90

        self.reset_view()

    def mouseMoveEvent(self, ev):
        # Вычисляем, насколько сдвинулась мышь
        diff = ev.pos() - self.mousePos
        self.mousePos = ev.pos()

        if ev.buttons() == Qt.LeftButton:
            # СВОБОДНОЕ ВРАЩЕНИЕ (Без лимитов от -90 до +90)
            # Коэффициент 0.5 делает вращение более плавным
            self.opts['azimuth'] -= diff.x() * 0.25
            self.opts['elevation'] += diff.y() * 0.25
            self.update()

        elif ev.buttons() == Qt.RightButton:
            # Сдвиг сцены (Pan)
            self.pan(diff.x(), diff.y(), 0, relative='view')

        elif ev.buttons() == Qt.MiddleButton:
            # Плавный Зум (или просто крутите колесико мыши)
            self.opts['distance'] += diff.y() * 0.5
            self.update()

    def reset_view(self):
        """Возвращает камеру в сохраненную стартовую позицию"""
        # Внутри GLViewWidget метод называется setCameraPosition
        self.setCameraPosition(
            pos=self.default_cam_pos,
            distance=self.default_cam_dist,
            elevation=self.default_cam_elev,
            azimuth=self.default_cam_azim
        )

    def display_point_cloud(self, frame_data: dict):
        """Отрисовывает облако точек и центрирует камеру"""
        points = frame_data.get('points')
        real_colors = frame_data.get('colors')

        if points is None or len(points) == 0:
            return

        if self.cad_mesh_item is not None:
            self.cad_mesh_item.hide()

        self.scatter.show()

        # --- Рассчет цветов ---
        if real_colors is not None and len(real_colors) == len(points):
            colors = np.ones((len(points), 4))
            colors[:, :3] = real_colors
        else:
            z = points[:, 2]
            z_min, z_max = z.min(), z.max()
            z_range = z_max - z_min if (z_max - z_min) > 0 else 1.0
            z_norm = (z - z_min) / z_range

            pos = np.array([0.0, 0.5, 1.0])
            color_array = np.array([
                [0, 20, 80, 255], [0, 100, 200, 255], [0, 255, 255, 255]
            ], dtype=np.ubyte)

            cmap = pg.ColorMap(pos, color_array)
            colors = cmap.map(z_norm) / 255.0

        # Отрисовка
        self.scatter.setData(pos=points, color=colors, size=2, pxMode=True)

        # --- НАСТРОЙКА ИДЕАЛЬНОЙ КАМЕРЫ ---
        centroid = np.mean(points, axis=0)
        max_dist = np.max(np.linalg.norm(points - centroid, axis=1))

        self.default_cam_pos = pg.Vector(centroid[0], centroid[1], centroid[2])
        dist_to_origin = np.linalg.norm(centroid)
        self.default_cam_dist = max(max_dist * 2.5, dist_to_origin * 1.5)

        #self.reset_view()

    def display_mesh(self, mesh_data: dict):
        vertices = mesh_data.get('vertices')
        faces = mesh_data.get('faces')

        if vertices is None or len(vertices) == 0:
            self.cad_mesh_item.hide()
            return

        # 1. Создаем структуру данных
        mesh_data_obj = gl.MeshData(vertexes=vertices, faces=faces)

        # 2. ПРОСТО ОБНОВЛЯЕМ ДАННЫЕ в существующем объекте (Старая модель исчезнет сама)
        self.cad_mesh_item.setMeshData(meshdata=mesh_data_obj)

        # 3. Задаем светлый материал (Светло-светло серый/белый с RGBA)
        self.cad_mesh_item.setColor((0.85, 0.85, 0.85, 1.0)) # (0.85, 0.85, 0.85, 1.0)(1.0, 1.0, 1.0, 1.0)
        self.cad_mesh_item.show()

        # 4. Центрируем камеру
        centroid = np.mean(vertices, axis=0)
        max_dist = np.max(np.linalg.norm(vertices - centroid, axis=1))

        self.default_cam_pos = pg.Vector(centroid[0], centroid[1], centroid[2])
        dist_to_origin = np.linalg.norm(centroid)
        self.default_cam_dist = max(max_dist * 2.5, dist_to_origin * 1.5)

        #self.reset_view()

class ViewportPanel(QWidget):
    """Обертка, которая объединяет кнопки управления и сам OpenGL виджет"""
    request_test_shot = pyqtSignal()
    request_show_cad = pyqtSignal()
    request_show_cad_mesh = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_internal_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Убираем рамки

        # --- ПАНЕЛЬ КНОПОК ---
        view_control_layout = QHBoxLayout()
        view_control_layout.setContentsMargins(0, 0, 0, 0)

        btn_style = "background-color: #555; color: white; border-radius: 4px; padding: 5px;"

        self.btn_reset_view = QPushButton("⟲ Reset View")
        self.btn_reset_view.setFixedWidth(120)
        self.btn_reset_view.setStyleSheet(btn_style)

        self.btn_test_shot = QPushButton("📷 Test Shot")
        self.btn_test_shot.setFixedWidth(120)
        self.btn_test_shot.setStyleSheet(btn_style)

        self.btn_show_cad = QPushButton("👁 CAD PCD")
        self.btn_show_cad.setFixedWidth(120)
        self.btn_show_cad.setStyleSheet(btn_style)

        self.btn_show_cad_mesh = QPushButton("👁 CAD Mesh")
        self.btn_show_cad_mesh.setFixedWidth(120)
        self.btn_show_cad_mesh.setStyleSheet(btn_style)
        #self.btn_show_cad.setCheckable(True)  # Делаем кнопку переключателем (Вкл/Выкл)

        # Выравниваем кнопки слева направо
        view_control_layout.addWidget(self.btn_reset_view)
        view_control_layout.addWidget(self.btn_test_shot)
        view_control_layout.addWidget(self.btn_show_cad)
        view_control_layout.addWidget(self.btn_show_cad_mesh)
        view_control_layout.addStretch()

        layout.addLayout(view_control_layout)

        # --- САМ 3D ВИДЖЕТ ---
        self.gl_widget = GlobalViewport()
        layout.addWidget(self.gl_widget)

    def _connect_internal_signals(self):
        self.btn_reset_view.clicked.connect(self.gl_widget.reset_view)
        self.btn_test_shot.clicked.connect(self.request_test_shot.emit)
        self.btn_show_cad.clicked.connect(self.request_show_cad.emit)
        self.btn_show_cad_mesh.clicked.connect(self.request_show_cad_mesh.emit)