from PyCameraSDK.GenericError import *
from PyCameraSDK.Common import *
from PyCameraSDK.Camera import *
from Util import *


def PrintCamInfoList():
    for i in range(len(camInfoList)):
        print("index", i, "is:", camInfoList[i].cameraIP, "ret:",
              camInfoList[i].errorCode, "cameraVersion:", camInfoList[i].cameraSystemVersion)


def OpenOneCamera(strWantedIP=None):
    for i in range(len(camInfoList)):
        if (strWantedIP != None and camInfoList[i].cameraIP != strWantedIP):
            continue
        if(cam.Open(camInfoList[i]) == AC_OK):
            print("\033[1;32m", "Open",
                  camInfoList[i].cameraIP, "OK", "\033[0m")
            return AC_OK, camInfoList[i]
    print("\033[1;31m" "Can't Open any camera.", "\033[0m")
    return AC_E_NO_CAMERA, CameraInfo()


def OutputAll(isSend=True):
    camInfo.outputSettings.sendPoint3D = isSend
    camInfo.outputSettings.sendPointUV = isSend
    camInfo.outputSettings.sendTriangleIndices = isSend
    camInfo.outputSettings.sendDepthmap = isSend
    camInfo.outputSettings.sendNormals = isSend
    camInfo.outputSettings.sendPointColor = isSend
    camInfo.outputSettings.sendTexture = isSend
    camInfo.outputSettings.sendRemapTexture = isSend
    if (camInfo.rgbStatus == AC_E_NOT_EXIST):
        camInfo.outputSettings.sendTexture = False
        camInfo.outputSettings.sendPointColor = False    
    
##### Start ####
cam = Camera().CreateCamera()

ret, camInfoList = cam.DiscoverCameras()
PrintCamInfoList()

ret, camInfo = OpenOneCamera()

if ret == AC_OK:
    ret , cameraIntrinsic = cam.Get3DCameraIntrinsic(camInfo, CAMERA_POSITION.CAM_LEFT)
    if ret == AC_OK:
        print('CAM_In', cameraIntrinsic)
    ret , cameraExtrinsic = cam.Get3DCameraExtrinsic(camInfo, EXTRINSIC_TYPE.POINT_TO_CAM_LEFT)
    if ret == AC_OK:
        print('CAM_Ex', cameraExtrinsic)
    
    letfPoints = [[897.63, 848.37], [896.557, 818.848], [895.443, 789.152]]
    rightPoints = [[1035, 848.382], [1034.09, 818.564], [1033.25, 789.067]]
    ret, points = cam.ReconstructPoints(camInfo, letfPoints, rightPoints)
    if ret == AC_OK:
        print(points)
    
    cam.Close(camInfo)

##### End ####
