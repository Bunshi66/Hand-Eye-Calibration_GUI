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
    if (camInfo.rgbStatus == AC_E_NOT_EXIST):
        camInfo.outputSettings.sendTexture = False
        camInfo.outputSettings.sendPointColor = False


def OutputOnlyPoint3D():
    OutputAll(False)
    camInfo.outputSettings.sendPoint3D = True


def SaveImages():
    filePath = create_outdir()
    if frameData.textureSize:
        save_rgb(frameData.texture, camInfo.camParam, filePath)
    if frameData.depthmapSize:
        save_deepmap2tiff(frameData.depthmap, camInfo.camParam, filePath)
    if frameData.textureSize and frameData.pointUVSize:
        save_rgb_align_depth(frameData.texture, frameData.pointUV,
                             camInfo.camParam, filePath)
    if frameData.point3DSize and frameData.pointUVSize and frameData.triangleIndicesSize:
        save_point2wrl(frameData, filePath)
    if frameData.point3DSize:
        save_point2pcd(frameData, filePath)
    if frameData.depthmapSize:
        save_deepmap(frameData.depthmap, camInfo.camParam, filePath)
    if frameData.point3DSize and frameData.triangleIndicesSize:
        save_point2ply(frameData, filePath)
    if frameData.point3DSize and frameData.normalsSize:
        save_point2ply_normal_color(frameData, filePath)


def PrintErrorAndExit(ret, optType):
    if ret != AC_OK:
        print(optType, "failed, errorCode:", ret)
        cam.Close(camInfo)
        exit()
        

##### Start ####
cam = Camera().CreateCamera()

ret, camInfoList = cam.DiscoverCameras()
PrintCamInfoList()

ret, camInfo = OpenOneCamera()

if ret == AC_OK:
    #OutputAll()
    OutputOnlyPoint3D() # Try to select your desired output, in order to reduce the overall capture time.
    ret = cam.SetValue(camInfo, ParamType.Algo_WrapphaseType, 9)
    if ret == AC_E_OUT_OF_RANGE:  # current mems version doesn't support 9
        ret = cam.SetValue(camInfo, ParamType.Algo_WrapphaseType, 5)
        PrintErrorAndExit(ret, "Set Algo_WrapphaseType")

    betterPixelFormat = 12
    ret, pixelFormatJson = cam.GetNodeAttributeJson(camInfo, "PixelFormat")
    if ret == AC_OK:
        if pixelFormatJson.find("Mono12") == -1:
            betterPixelFormat = 10
    if ret == AC_OK:
        ret = cam.SetValue(camInfo, "PixelFormat", betterPixelFormat)
        PrintErrorAndExit(ret, "Set PixelFormat")

    ret, value = cam.GetValue(camInfo, "Exposure")
    if ret == AC_OK and value <= 30:
        ret = cam.SetValue(camInfo, "Exposure", 30)
        PrintErrorAndExit(ret, "Set Exposure")
        
    frameData = FrameData()
    ret = cam.Capture(camInfo, frameData)
    if ret == AC_OK:
        SaveImages()

    cam.Close(camInfo)

##### End ####