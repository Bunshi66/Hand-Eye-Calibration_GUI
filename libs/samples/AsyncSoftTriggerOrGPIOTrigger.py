import threading
from time import sleep
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


def OutputOnlyPoint3D():
    OutputAll(False)
    camInfo.outputSettings.sendPoint3D = True


def SaveImages(camInfo, frameData):
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
    print("SaveImages OK")


def ConvertCPointToNumpyArray(frameData, ctypeFrameData):
    frameData.point3DSize = ctypeFrameData.point3DSize
    frameData.pointUVSize = ctypeFrameData.pointUVSize
    frameData.triangleIndicesSize = ctypeFrameData.triangleIndicesSize
    frameData.depthmapSize = ctypeFrameData.depthmapSize
    frameData.normalsSize = ctypeFrameData.normalsSize
    frameData.pointColorSize = ctypeFrameData.pointColorSize
    frameData.textureSize = ctypeFrameData.textureSize
    frameData.pointCount = ctypeFrameData.pointCount
    
    if frameData.point3DSize:
        frameData.point3D = np.frombuffer(
            (ctypes.c_float * frameData.point3DSize).from_address(int(ctypeFrameData.point3D)), np.float32)

    if frameData.pointUVSize:
        frameData.pointUV = np.frombuffer(
            (ctypes.c_float * frameData.pointUVSize).from_address(int(ctypeFrameData.pointUV)), np.float32)
        
    if frameData.triangleIndicesSize:
        frameData.triangleIndices = np.frombuffer(
            (ctypes.c_int32 * frameData.triangleIndicesSize).from_address(int(ctypeFrameData.triangleIndices)), np.int32)
        
    if frameData.depthmapSize:
        frameData.depthmap = np.frombuffer(
            (ctypes.c_float * frameData.depthmapSize).from_address(int(ctypeFrameData.depthmap)), np.float32)
    
    if frameData.normalsSize:
        frameData.normals = np.frombuffer(
            (ctypes.c_float * frameData.normalsSize).from_address(int(ctypeFrameData.normals)), np.float32)
        
    if frameData.pointColorSize:
        frameData.pointColor = np.frombuffer(
            (ctypes.c_uint8 * frameData.pointColorSize).from_address(int(ctypeFrameData.pointColor)), np.uint8)
    
    if frameData.textureSize:
        frameData.texture = np.frombuffer(
            (ctypes.c_uint8 * frameData.textureSize).from_address(int(ctypeFrameData.texture)), np.uint8)
                

class MyPyFrameDataHandler(PyFrameDataHandler):
    def Handle(self, camInfo, ctypeFrameData):
        frameData = FrameData()
        ConvertCPointToNumpyArray(frameData, ctypeFrameData)
        SaveImages(camInfo, frameData)


def AsyncSoftTriggerLoop():
    sleep(0.1)  # just for a nice input prompt
    while True:
        cmd = input("Press 'q' to exit, '1' to trigger once: ")
        if cmd == 'q': 
            break
        if cmd == '1':
            cam.CaptureDataAsync(camInfo)
        if cmd == '2':
            camInfo.outputSettings.sendTexture = True
        print("Continue...")


def GPIOTriggerLoop():
    sleep(0.1)  # just for a nice input prompt
    while True:
        cmd = input("Press 'q' to exit: ")
        if cmd == 'q':
            break
        print("Continue...")
        
        
##### Start ####
cam = Camera().CreateCamera()
cam.RegisterErrorCodeHandler(PyErrorCodeHandler().__disown__())
# default GPIO/Async trigger output data handler. You can override it to implement your own callback function.
cam.RegisterFrameDataHandler(MyPyFrameDataHandler().__disown__())

ret, camInfoList = cam.DiscoverCameras()
PrintCamInfoList()

ret, camInfo = OpenOneCamera()

if ret == AC_OK:
    #OutputAll()
    #OutputOnlyPoint3D() # Try to select your desired output, in order to reduce the overall capture time.
    ret = cam.SetValue(camInfo, "TriggerMode",
                       CameraWorkMode.Camera_SoftSingleAsyncTrigger)
    if ret == AC_OK:
        print("Enter Soft Single Async Trigger mode.")
        th = threading.Thread(target=AsyncSoftTriggerLoop)
        th.start()
        th.join()
        
    ret = cam.SetValue(camInfo, "TriggerMode",
                       CameraWorkMode.Camera_GPIOTrigger)
    if ret == AC_OK:
        print("Enter GPIO Trigger mode.")
        th = threading.Thread(target=GPIOTriggerLoop)
        th.start()
        th.join()
    
    cam.Close(camInfo)

##### End ####
