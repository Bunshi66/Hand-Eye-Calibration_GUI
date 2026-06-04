from PyCameraSDK.GenericError import *
from PyCameraSDK.Camera import *
from PyCameraSDK.Common import *

import logging
import time

logger = logging.getLogger(__name__)

class ScapeCamera():
    """Оболочка над SDK камеры SCAPE"""

    def __init__(self):
        """
            Инициализация камеры.

            Args:
                connection_params: {
                    'ip': str или None (None = первая найденная камера)
                }
            """
        self._camera_ip = None
        self._cam = None  # объект Camera из SDK
        self._cam_info = None  # CameraInfo подключённой камеры
        self._cam_info_list = []  # список всех найденных камер
        self._connected = False

    def connect(self, camera_ip: str) -> bool:
        """Установить соединение с камерой."""
        logger = logging.getLogger(__name__)

        self._camera_ip = camera_ip
        self._cam = Camera().CreateCamera()
        self._cam.RegisterErrorCodeHandler(PyErrorCodeHandler().__disown__())

        # Ищем камеры в сети
        ret, self._cam_info_list = self._cam.DiscoverCameras()
        if not self._cam_info_list:
            logger.error("Камеры SCAPE не обнаружены в сети")
            return False, CameraInfo()

        # Логируем найденные камеры
        for i, info in enumerate(self._cam_info_list):
            logger.info(
                f"[{i}] {info.cameraIP} "
                f"v{info.cameraSystemVersion} "
                f"(err={info.errorCode})"
            )

        # Подключаемся к нужной (или первой найденной)
        for info in self._cam_info_list:
            if self._camera_ip is not None and info.cameraIP != self._camera_ip:
                continue
            if self._cam.Open(info) == AC_OK:
                self._cam_info = info
                self._connected = True
                logger.info(f"Подключено к камере {info.cameraIP}")
                return True, info

        logger.error(f"Не удалось открыть камеру (ip={self._camera_ip})")
        return False, CameraInfo()

    def disconnect(self):
        """Отключиться от камеры и освободить ресурсы."""
        if self._cam:
            if self._connected and self._cam_info:
                # Закрываем соединение в C++
                self._cam.Close(self._cam_info)

            self._connected = False
            # ПРИНУДИТЕЛЬНО удаляем ссылку на C++ объект до завершения скрипта
            self._cam = None
            logger.info("Камера отключена и ресурсы освобождены.")

    def is_connected(self) -> bool:
        """Проверка состояния подключения."""
        return self._connected

    def get_frame(self) -> dict:
        """Делает снимок и возвращает сырые numpy-массивы."""
        if not self._connected or not self._cam_info:
            logger.error("Ошибка захвата: Камера не подключена")
            return None

        frame_data = FrameData()

        ret = self._cam.Capture(self._cam_info, frame_data)

        if ret != 0:
            logger.error(f"Ошибка SDK при захвате кадра: код {ret}")
            return None

        result = {}

        params = self._cam_info.camParam

        # Разрешение для цветной картинки
        tex_w = params.textureWidth
        tex_h = params.textureHeight

        # Разрешение для карты глубины (зависит от настроек SDK)
        if params.depthType == 1:  # DEPTH_MAP_ALIGN_RGB
            depth_w = params.textureWidth
            depth_h = params.textureHeight
        else:  # Выровнено по инфракрасной камере
            depth_w = params.irWidth
            depth_h = params.irHeight

        # ==========================================
        # ПАРСИНГ ДАННЫХ
        # ==========================================
        # 1. 2D Изображение (RGB или Mono)
        if frame_data.textureSize > 0:
            channels = frame_data.textureSize // (tex_w * tex_h)
            shape = (tex_h, tex_w, channels) if channels > 1 else (tex_h, tex_w)

            # Обязательно .copy() для безопасности памяти!
            result['image'] = frame_data.texture.reshape(shape).copy()

        # 2. Карта Глубины (TIFF)
        if frame_data.depthmapSize > 0:
            result['depth'] = frame_data.depthmap.reshape((depth_h, depth_w)).copy()

        # 3. Облако точек (N, 3)
        if frame_data.point3DSize > 0:
            # Здесь ширина и высота вообще не нужны,
            # reshape(-1, 3) сам разобьет плоский массив на тройки [X, Y, Z]
            result['points'] = frame_data.point3D.reshape((-1, 3)).copy()

        return result

    def _configure_output_settings(self, send_texture=True, send_point3d=True, send_depthmap=True):
        """Включает/выключает потоки данных для экономии трафика."""
        # Выключаем лишнее, чтобы работало быстрее
        self._cam_info.outputSettings.sendTriangleIndices = False
        self._cam_info.outputSettings.sendNormals = False
        self._cam_info.outputSettings.sendRemapTexture = False
        self._cam_info.outputSettings.sendPointColor = False

        # Включаем нужное
        self._cam_info.outputSettings.sendTexture = send_texture
        self._cam_info.outputSettings.sendPoint3D = send_point3d
        self._cam_info.outputSettings.sendDepthmap = send_depthmap

    def get_camera_info(self) -> dict:
        """Получить информацию о камере (модель, серийник, параметры)."""
        pass

    def get_intrinsic(self, cam_info, cam_position):
        """
                Получает матрицу внутренних параметров камеры (3x3).
                :param cam_info: Объект CameraInfo из SDK
                :param cam_position: CAMERA_POSITION.CAM_LEFT | CAM_RGB | CAM_RIGHT
                :return: np.ndarray shape (3,3) или None при ошибке
                """
        cam_enum = {'left': CAMERA_POSITION.CAM_LEFT,
                    'right': CAMERA_POSITION.CAM_RIGHT,
                    'rgb': CAMERA_POSITION.CAM_RGB}
        try:
            ret, intrinsic_list = self._cam.Get3DCameraIntrinsic(cam_info, cam_enum[cam_position])
            if ret != 0:  # 0 = AC_OK
                logger.error(f"❌ SDK вернул ошибку интринсиков: code={ret}")
                return None
            if len(intrinsic_list) != 9:
                logger.error(f"❌ Неверный размер интринсиков: {len(intrinsic_list)} (ожидается 9)")
                return None
            #print(f'Отладочная печать: {intrinsic_list}')
            return np.array(intrinsic_list).reshape(3, 3)
        except Exception as e:
            logger.error(f"❌ Исключение при получении интринсиков: {e}")
            return None

    def get_extrinsic(self, cam_info, extrinsic_type):
        """
        Получает матрицу преобразования из облака точек в СК целевой камеры (4x4).
        :param cam_info: Объект CameraInfo из SDK
        :param extrinsic_type: EXTRINSIC_TYPE.POINT_TO_CAM_LEFT | POINT_TO_CAM_RGB | POINT_TO_CAM_RIGHT
        :return: np.ndarray shape (4,4) или None при ошибке
        """
        cam_enum = {'left': EXTRINSIC_TYPE.POINT_TO_CAM_LEFT,
                    'right': EXTRINSIC_TYPE.POINT_TO_CAM_RIGHT,
                    'rgb': EXTRINSIC_TYPE.POINT_TO_CAM_RGB}
        try:
            ret, extrinsic_list = self._cam.Get3DCameraExtrinsic(cam_info, cam_enum[extrinsic_type])
            if ret != 0:
                logger.error(f"❌ SDK вернул ошибку эксттринсиков: code={ret}")
                return None
            if len(extrinsic_list) != 16:
                logger.error(f"❌ Неверный размер эксттринсиков: {len(extrinsic_list)} (ожидается 16)")
                return None
            #print(f'Отладочная печать: {extrinsic_list}')
            return np.array(extrinsic_list).reshape(4, 4)
        except Exception as e:
            logger.error(f"❌ Исключение при получении эксттринсиков: {e}")
            return None

    def set_exposure(self, value: float):
        """Настройка экспозиции."""
        pass