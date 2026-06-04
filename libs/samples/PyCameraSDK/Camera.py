import ctypes
import numpy as np

if __package__ or "." in __name__:
    from . import gen3d
    from . import Common
else:
    import gen3d
    import Common

class Camera:
    def __init__(self):
        self.cam = None
        pass
    
    def __del__(self):
        if self.cam != None:
            gen3d.DestoryCamera(self.cam)

    #! CreateCamera():
	#  brief: Create the camera object. Called only once when the program starts
	#  param type: the default type is CamPro
	#  return: the self to the class Camera.
    def CreateCamera(self, type=gen3d.CamPro):
        self.cam = gen3d.CreateCamera(gen3d.CamPro)
        return self
 
    # ! DiscoverCameras():
	#  brief: Discover camera(s) by broadcasting.
	#  param timeout: Set the timeout(unit: ms) of discovering.
	#  return: ret, camInfoList. 
    #          ret: Success, return AC_OK. Failure, return error code(e.g. AC_E_NO_CAMERA).
    #          camInfoList: Store the discovered camera(s) in vector.
    def DiscoverCameras(self, timeOut=1000):
        camInfoVector = gen3d.CameraInfoVector()
        ret = self.cam.DiscoverCameras(camInfoVector, timeOut)
        camInfoList = []
        for i in range(len(camInfoVector)):
            camInfoList.append(camInfoVector[i])
        return ret, camInfoList

    #! Open():
	#  brief: Open a camera and get some parameters from camera into cameraInfo.
	#  param cameraInfo: a struct of camera info.
	#  param timeout: Set the timeout(unit: ms) of the operation.
	#  return: Success, return AC_OK. Failure, return error code.
    def Open(self, cameraInfo, timeout=60000):
        return self.cam.Open(cameraInfo, timeout)

    #! Capture():
	# @ brief: Capture the data of the camera.
    # @ param frameData: A struct be used to restore the data. The struct will automatically allocate memory and automatically release memory at the end of its life cycle.
	# @ return: ret(ErrorCode)
    def Capture(self, cameraInfo, frameData):
        ret = self.cam.Capture(cameraInfo, frameData.ctypeFrameData)
        if ret == 0:
            frameData.frameInfo = frameData.ctypeFrameData.frameInfo
            frameData.point3DSize = frameData.ctypeFrameData.point3DSize
            frameData.pointUVSize = frameData.ctypeFrameData.pointUVSize
            frameData.triangleIndicesSize = frameData.ctypeFrameData.triangleIndicesSize
            frameData.depthmapSize = frameData.ctypeFrameData.depthmapSize
            frameData.normalsSize = frameData.ctypeFrameData.normalsSize
            frameData.pointColorSize = frameData.ctypeFrameData.pointColorSize
            frameData.textureSize = frameData.ctypeFrameData.textureSize
            frameData.pointCount = frameData.ctypeFrameData.pointCount
            frameData.remapTextureSize = frameData.ctypeFrameData.remapTextureSize
            
            if frameData.point3DSize:
                frameData.point3D = np.frombuffer(
                    (ctypes.c_float * frameData.point3DSize).from_address(int(frameData.ctypeFrameData.point3D)), np.float32)
                
            if frameData.pointUVSize:
                frameData.pointUV = np.frombuffer(
                    (ctypes.c_float * frameData.pointUVSize).from_address(int(frameData.ctypeFrameData.pointUV)), np.float32)
                
            if frameData.triangleIndicesSize:
                frameData.triangleIndices = np.frombuffer(
                    (ctypes.c_int32 * frameData.triangleIndicesSize).from_address(int(frameData.ctypeFrameData.triangleIndices)), np.int32)
                
            if frameData.depthmapSize:
                frameData.depthmap = np.frombuffer(
                    (ctypes.c_float * frameData.depthmapSize).from_address(int(frameData.ctypeFrameData.depthmap)), np.float32)
            
            if frameData.normalsSize:
                frameData.normals = np.frombuffer(
                    (ctypes.c_float * frameData.normalsSize).from_address(int(frameData.ctypeFrameData.normals)), np.float32)
                
            if frameData.pointColorSize:
                frameData.pointColor = np.frombuffer(
                    (ctypes.c_uint8 * frameData.pointColorSize).from_address(int(frameData.ctypeFrameData.pointColor)), np.uint8)
            
            if frameData.textureSize:
                frameData.texture = np.frombuffer(
                    (ctypes.c_uint8 * frameData.textureSize).from_address(int(frameData.ctypeFrameData.texture)), np.uint8)
                
            if frameData.remapTextureSize:
                frameData.remapTexture = np.frombuffer(
                    (ctypes.c_uint8 * frameData.remapTextureSize).from_address(int(frameData.ctypeFrameData.remapTexture)), np.uint8)
        
        return ret
    
    #! RegisterErrorCodeHandler():
	#  brief: Register the ErrorCode Handler. So that you can handle the real-time error code in Trigger mode(contains Camera_GPIOTrigger Camera_SoftContinuousTrigger Camera_SoftSingleAsyncTrigger).
	#  param errorCodeHandler: The ErrorCode Handler. Customize your Handler by overloading class 'ErrorCodeHandler'.
	#  return: none
    def RegisterErrorCodeHandler(self, errorCodeHandler):
        self.cam.RegisterErrorCodeHandler(errorCodeHandler)
        
    #! RegisterFrameDataHandler():
	#  brief: Register the FrameData Handler. So that you can handle the real-time FrameData in Trigger mode(contains Camera_GPIOTrigger Camera_SoftContinuousTrigger Camera_SoftSingleAsyncTrigger).
	#  param frameDataHandler: The FrameData Handler. Customize your Handler by overloading class 'FrameDataHandler'.
	#  param timeout: Set The timeout in ms of waiting data.
    #  return: none
    def RegisterFrameDataHandler(self, frameDataHandler, timeOut=0xFFFFFFFF):
        self.cam.RegisterFrameDataHandler(frameDataHandler, timeOut)
    
	#! CaptureDataAsync() :
	#  brief: Single asynchronous trigger, the working mode (CameraWorkMode) needs to be set to Camera_SoftSingleAsyncTrigger, and data is obtained through the GPIODataCallBack interface.
    def CaptureDataAsync(self, cameraInfo):
        return self.cam.CaptureDataAsync(cameraInfo)
    
	#! SetCameraIP() :
	#  brief: Set the camera's IP to a static IP.
    def SetCameraIP(self, cameraIP):
        self.cam.SetCameraIP(cameraIP)
        
    #! SetCameraToDHCP() :
	#  brief: Set the camera's network to DHCP.
    def SetCameraToDHCP(self, cameraInfo):
        self.cam.SetCameraToDHCP(cameraInfo)

    #! CameraGetStatus() :
	#  brief: Get some real-time info from camera and update into cameraInfo.
    def CameraGetStatus(self, cameraInfo):
        return self.cam.CameraGetStatus(cameraInfo)
    
    #! SetValue/GetValue():
	#  brief: Set/Get the value into/from camera by ParamType or string.
	#    When Set/Get by ParamType, the value's data type must match ParamType according to the 'DataType: ' explained in Common.py. Defalut 'DataType' is 'int'.
	#  return: SetValue() return ErrorCode, GetValue() return ret(ErrorCode) , value
    def SetValue(self, cameraInfo, key, value):
        if (type(key) == str):
            return self.cam.SetValue(cameraInfo, key, value)
        else:
            if key in [Common.ParamType.Algo_XfRangeMax, Common.ParamType.Algo_XfRangeMin,
                        Common.ParamType.Algo_YfRangeMax, Common.ParamType.Algo_YfRangeMin, Common.ParamType.Algo_ZfRangeMax, 
                        Common.ParamType.Algo_ZfRangeMin, Common.ParamType.Algo_LrCheckThreshold]:
                value = float(value)
            else:
                value = int(value)
            return self.cam.SetValue(cameraInfo, int(key), value)

    def GetValue(self, cameraInfo, key):
        if (type(key) == str):
            value = -1.0
            return self.cam.GetValue(cameraInfo, key, value)
        else:
            value = -1
            if key in [Common.ParamType.Algo_XfRangeMax, Common.ParamType.Algo_XfRangeMin,
                        Common.ParamType.Algo_YfRangeMax, Common.ParamType.Algo_YfRangeMin, Common.ParamType.Algo_ZfRangeMax,
                        Common.ParamType.Algo_ZfRangeMin, Common.ParamType.Algo_LrCheckThreshold]:
                value = -1.0
    
            return self.cam.GetValue(cameraInfo, int(key), value)
  
    #! SendMemsCommands():
	#  brief: Send original hexadecimal string commands to MEMS laser.
    def SendMemsCommands(self, cameraInfo, strCommands):
        return self.cam.SendMemsCommands(cameraInfo, strCommands)
    
    #! SendAndRecvMemsCommands():
	#  brief: Send original hexadecimal string commands to MEMS laser and receive the result.
    #  return: ErrorCode, strRecv.
    def SendAndRecvMemsCommands(self, cameraInfo, strCommands):
        strRecv = ''
        return self.cam.SendAndRecvMemsCommands(cameraInfo, strCommands, strRecv)
    
    #! CameraGetVersion():
	#  brief: Get the version information from camera. We will call the function in Open() automatically.
    def CameraGetVersion(self, cameraInfo):
        return self.cam.CameraGetVersion(cameraInfo)
    
    #! CameraSet/SetTriggerOutParam():
	# brief: Set/Get the param values of the GPIO(Trigger) mode.
	# param mode: GPIO trigger mode.
	# param cycleNumValue: Number of output square waves.
	# param cycleLenValue: The length of the output square wave, in ms.
    def CameraSetTriggerOutParam(self, cameraInfo,  mode,  cycleNumValue, cycleLenValue):
        return self.cam.CameraSetTriggerOutParam(cameraInfo, mode, cycleNumValue, cycleLenValue)
    
    def CameraGetTriggerOutParam(self, cameraInfo):
        mode = 0
        cycleNumValue = 0
        cycleLenValue = 0
        return self.cam.CameraGetTriggerOutParam(cameraInfo, mode, cycleNumValue, cycleLenValue)
    
    #! CameraReboot():
	#  brief: Send the reboot command to camera. You will lose the camera's current operation handle. Pelease reopen.
    def CameraReboot(self, cameraInfo):
        return self.cam.CameraReboot(cameraInfo)
    
    # ! AddParamGroup():
	#  brief:  Add a new param group to camera.
    #  param paramGroupName: The name of this param group.
	#  return: ret: Success, return AC_OK. Failure, return error code.
    def AddParamGroup(self, cameraInfo, paramGroupName):
        return self.cam.AddParamGroup(cameraInfo, paramGroupName)
    
    # ! GetParamGroups():
	#  brief: Get all of the param groups in camera.
	#  return: ret, paramGroupNamesList.
    #          ret: Success, return AC_OK. Failure, return error code.
    #          paramGroupNamesList: The names of all param groups in camera.
    def GetParamGroups(self, cameraInfo):
        paramGroupNames = gen3d.StringVector()
        ret = self.cam.GetParamGroups(cameraInfo, paramGroupNames)
        paramGroupNamesList = []
        for i in range(len(paramGroupNames)):
            paramGroupNamesList.append(paramGroupNames[i])
        return ret, paramGroupNamesList
    
    # ! DeleteParamGroup():
	#  brief: Delete a param group in camera.
    #  param paramGroupName: The name of the param group in camera.
	#  return: ret: Success, return AC_OK. Failure, return error code.
    def DeleteParamGroup(self, cameraInfo, paramGroupName):
        return self.cam.DeleteParamGroup(cameraInfo, paramGroupName)
    
    # ! ApplyParamGroup():
	#  brief:  Apply a param group in camera.
    #  param paramGroupName: The name of the param group in camera.
	#  return: ret: Success, return AC_OK. Failure, return error code.
    def ApplyParamGroup(self, cameraInfo, paramGroupName):
        return self.cam.ApplyParamGroup(cameraInfo, paramGroupName)
    
    # ! ReconstructPoints():
	#  brief:  Reconstruct points for hand-eye calibration.
    #  param leftPoints: left picture feature points.
    #  param rightPoints: right picture feature points.
	#  return: ret, matrix.
    #          ret: Success, return AC_OK. Failure, return error code.
    #          matrix: Store the result.
    def ReconstructPoints(self, cameraInfo, leftPoints, rightPoints):
        points2f = gen3d.Point2f()
        leftPointsVector = gen3d.Point2fVector()
        rightPointsVector = gen3d.Point2fVector()
        for point in leftPoints:
            points2f.x = point[0]
            points2f.y = point[1]
            leftPointsVector.push_back(points2f)
        for point in rightPoints:
            points2f.x = point[0]
            points2f.y = point[1]
            rightPointsVector.push_back(points2f)
        cplusPointsVector = gen3d.Point3fVector()
        
        ret = self.cam.ReconstructPoints(
            cameraInfo, leftPointsVector, rightPointsVector, cplusPointsVector)
        
        points = []
        for point3f in range(len(cplusPointsVector)):
            points.append([cplusPointsVector[point3f].x, cplusPointsVector[point3f].y, cplusPointsVector[point3f].z])             
        return ret, points
    
    #! GetAttributeTreeJson():
	#  brief: Get the attribute tree json of camera.
    #  return: ErrorCode, strAttributeTreeJson.
    def GetAttributeTreeJson(self, cameraInfo):
        strAttributeTreeJson = ''
        return self.cam.GetAttributeTreeJson(cameraInfo, strAttributeTreeJson)

	#! GetNodeAttributeJson():
	#  brief: Get the node's attribute json by key.
	#  param key: the key of the node
    #  return: ErrorCode, strNodeAttributeJson.
    def GetNodeAttributeJson(self, cameraInfo, key):
        strNodeAttributeJson = ''
        return self.cam.GetNodeAttributeJson(cameraInfo, key, strNodeAttributeJson)
    
    #! Get3DCameraIntrinsic():
	#  brief: Obtain the 3D camera internal parameter matrix, and the customer obtains Z through depth maps and calculates x, y, and z based on the internal parameters provided by the interface.
    #  param cameraPosition: Camera position.
    #  return: ErrorCode, cameraIntrinsic.
    #  cameraIntrinsic: 3D camera internal parameter matrix:
        #  a 3x3 matrix
        #  |.|.|.|
        #  | --|---|---|
        #  | fx|  0| cx|
        #  |  0| fy| cy|
        #  |  0|  0|  1|
    def Get3DCameraIntrinsic(self, cameraInfo, cameraPosition):
        cplusCameraIntrinsic = gen3d.DoubleVector()
        ret = self.cam.Get3DCameraIntrinsic(cameraInfo, cameraPosition, cplusCameraIntrinsic)
        cameraIntrinsic = []
        for i in range(len(cplusCameraIntrinsic)):
            cameraIntrinsic.append(cplusCameraIntrinsic[i])
        return ret, cameraIntrinsic
    
    #! Get3DCameraExtrinsic():
	#  brief: Calculate the transformation matrix from point cloud to target camera coordinate system.
    #  param extrinsicType: Type of point cloud to target camera coordinate system.
    #  return: ErrorCode, cameraExtrinsic.
    #  cameraExtrinsic: Transformation matrix:
        #  a 4x4 matrix
        #  |. | . | . | .|
        #  |--- | ---- | ---- | ---|
        #  |r11 | r12 | r13 | t1|
        #  |r21 | r22 | r23 | t2|
        #  |r31 | r32 | r33 | t3|
        #  |0   | 0   | 0   |  1|
    def Get3DCameraExtrinsic(self, cameraInfo, extrinsicType):
        cplusCameraExtrinsic = gen3d.DoubleVector()
        ret = self.cam.Get3DCameraExtrinsic(
            cameraInfo, extrinsicType, cplusCameraExtrinsic)
        cameraExtrinsic = []
        for i in range(len(cplusCameraExtrinsic)):
            cameraExtrinsic.append(cplusCameraExtrinsic[i])
        return ret, cameraExtrinsic

	#! GetDistortionCoefficients():
	#  brief: Obtain the 3D camera distortion coefficients.
    #  param position [IN] : Camera position.
    #  return: ErrorCode, distortionCoefficients.
    #  distortionCoefficients: 3D camera distortion coefficients:
        #  a 1x5 matrix, contains two radial distortion coefficients and three tangential distortion coefficients
        #  | p1| p2| k1| k2| k3|
    def GetDistortionCoefficients(self, cameraInfo, cameraPosition):
        cplusDistortionCoefficients = gen3d.DoubleVector()
        ret = self.cam.GetDistortionCoefficients(
            cameraInfo, cameraPosition, cplusDistortionCoefficients)
        distortionCoefficients = []
        for i in range(len(cplusDistortionCoefficients)):
            distortionCoefficients.append(cplusDistortionCoefficients[i])
        return ret, distortionCoefficients
    
    #! Close():
	#  brief: Close and disconnect from the camera.
    def Close(self, cameraInfo):
        return self.cam.Close(cameraInfo)
    
