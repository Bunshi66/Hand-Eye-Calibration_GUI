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


##### Start ####
cam = Camera().CreateCamera()

ret, camInfoList = cam.DiscoverCameras()
PrintCamInfoList()

ret, camInfo = OpenOneCamera()

if ret == AC_OK:
    if cam.CameraGetVersion(camInfo) == AC_OK:
        print("cameraSystemVersion:\t", camInfo.cameraSystemVersion)
        print("algorithmVersion:\t", camInfo.algorithmVersion)
        print("memsVersion:\t\t", camInfo.memsVersion)
        print("cameraOSVersion:\t", camInfo.cameraOSVersion)
        print("sdkVersion:\t", camInfo.sdkVersion)
    cam.Close(camInfo)

##### End ####
