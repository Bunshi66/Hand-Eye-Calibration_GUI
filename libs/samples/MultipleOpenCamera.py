from PyCameraSDK.GenericError import *
from PyCameraSDK.Common import *
from PyCameraSDK.Camera import *
from Util import *


def PrintCamInfoList():
    for i in range(len(camInfoList)):
        print("index", i, "is:", camInfoList[i].cameraIP, "ret:",
              camInfoList[i].errorCode, "cameraVersion:", camInfoList[i].cameraSystemVersion)


def OpenCamera():
    ret = cam.Open(camInfo)
    if ret == AC_OK:
        print("\033[1;32m", "Open",
            camInfo.cameraIP, "OK", "\033[0m")
    else:
        print("\033[1;31m" "Error. Can't Open",
            camInfo.cameraIP, "\033[0m")
        exit()
        
##### Start ####
cam = Camera().CreateCamera()

ret, camInfoList = cam.DiscoverCameras()
if ret != AC_OK:
    print("DiscoverCameras failed")
PrintCamInfoList()

defaultCameraIndex = 0
if len(camInfoList) > 0 :    
    camInfo = camInfoList[defaultCameraIndex]
    OpenCamera()
    cam.Close(camInfo)

ret, camInfoList = cam.DiscoverCameras()
if ret != AC_OK:
    print("DiscoverCameras failed")
PrintCamInfoList()

if len(camInfoList) > 0 :
    camInfo = camInfoList[defaultCameraIndex]
    OpenCamera()

    ret, exposure = cam.GetValue(camInfo, "Exposure")
    print("ret:", ret, "Get Exposure:", exposure)

    cam.Close(camInfo)

##### End ####
