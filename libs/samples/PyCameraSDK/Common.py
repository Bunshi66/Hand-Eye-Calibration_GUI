from enum import IntEnum
if __package__ or "." in __name__:
    from . import gen3d
else:
    import gen3d


# "CamType" is used to instantiate the camera handle by API CreateCamera(). Only support CamPro currently.
class CamType(IntEnum):
    CamPro = 0,


# "CameraWorkMode" is used to define the current working mode of the camera.
class CameraWorkMode(IntEnum):
    Camera_SoftTrigger = 0,           # software trigger (default)
    Camera_GPIOTrigger = 1,           # hardware GPIO trigger
    Camera_SoftSingleAsyncTrigger = 3  # software single asynchronous trigger
    

# "ParamType" contains some parameters that can be SetValue/GetValue. 
# The hexadecimal enumeration value defined following is also the command value sent to the camera
class ParamType(IntEnum):
    Capture_WorkMode  = 0x0101, # @brief: camera's working mode          @range: [0,3]      @defalut: 0(Camera_SoftTrigger)  @value meaning: see CameraWorkMode above
    Capture_Delay     = 0x0102, # @brief: delay time(ms) before capture  @range: [0,65535]  @defalut: 0

    IR_Exposure       = 0x0200, # @brief: exposure time(ms) of IR camera      @range: [1, 100]  @defalut: 15 
    IR_Gain           = 0x0201, # @brief: gain of IR camera                   @range: [0, 15]   @defalut: 0
    IR_LightSource    = 0x0202, # @brief: light source of IR camera           @range: [0, 1]    @defalut: 0(MEMS laser)
    IR_HDRCnt         = 0x0203, # @brief: times of HDR of IR camera           @range: [1, 3]    @defalut: 1  @value meaning: HDRExposure2 and HDRExposure3 do not take effect when this parameter is set to 1
    IR_HDRExposure2   = 0x0204, # @brief: 2nd exposure time(ms) of IR camera  @range: [1, 100]  @defalut: 25
    IR_HDRExposure3   = 0x0205, # @brief: 3rd exposure time(ms) of IR camera  @range: [1, 100]  @defalut: 5
    IR_PixelType	  = 0x0206, # @brief: type of image pixel                 @range: {8, 10, 12}   @defalut: 8  @value meaning: The value only can be 8 , 10 or 12. The corresponding type is Mono8, Mono10 or Mono12 respectively.

    Rgb_BrightnessSet = 0x0300, # @brief: brightness setting of RGB camera    @range: [-64, 64]    @defalut: 0
    Rgb_Contrast      = 0x0301, # @brief: contrast of RGB camera              @range: [0, 100]     @defalut: 50
    Rgb_Saturation    = 0x0302, # @brief: saturation of RGB camera            @range: [0, 100]     @defalut: 64
    Rgb_Hue           = 0x0303, # @brief: hue of RGB camera                   @range: [-180, 180]  @defalut: 0
    Rgb_Gamma         = 0x0304, # @brief: Gamma coefficient of RGB camera     @range: [100, 500]   @defalut: 300
    Rgb_WhiteBalanceTemperature     = 0x0305, # @brief: white balance temperature of RGB camera            @range: [2800, 6500]  @defalut: 4600 @step: 10
    Rgb_Sharpness                   = 0x0306, # @brief: sharpness of RGB camera                            @range: [0, 100]      @defalut: 50
    Rgb_BacklightCompensation       = 0x0307, # @brief: backlight compensation of RGB camera               @range: [0, 2]        @defalut: 0
    Rgb_ExposureAbsolute            = 0x0308, # @brief: exposure time of RGB camera                        @range: [50, 10000]   @defalut: 350
    Rgb_WhiteBalanceTemperatureAuto = 0x0309, # @brief: antomatic white balance temperature of RGB camera  @range: [0, 1]        @defalut: 1   @value meaning: 1(Auto) 0(Manual)
    Rgb_ExposureAuto                = 0x030A, # @brief: automatic exposure of RGB camera                   @range: [1, 3]        @defalut: 3   @value meaning: 3(Auto) 1(Manual)

    Mems_TriggerDelay  = 0x0400, # @brief: MEMS laser trigger interval time(ms). It must be greater than the maximum IR exposure time.  @range: [1, 1000]  @defalut: 25
    Mems_LaserKValue   = 0x0401, # @brief: MEMS laser's power.  @range: [0, 200]  @defalut: 50

    Algo_DepthMapType          = 0x0500, # @brief: depth map type                       @range: [1, 2]            @defalut: 1   @value meaning: 1(texture alignment) 2(point cloud alignment)
    Algo_DilateKsize           = 0x0501, # @brief: size of the window to fill the hole  @range: {3, 5, 7, 9, 11}  @defalut: 11  @value meaning: More holes will be filled when the value is larger
    Algo_FillHole              = 0x0502, # @brief: enable switch of hole filling        @range: [0, 1]            @defalut: 0(disabled)
    Algo_KSize                 = 0x0503, # @brief: size of smoothing window             @range: {3, 5, 7, 9, 11, 13, 15, 17, 19, 21} @defalut: 11
    Algo_Sigma                 = 0x0504, # @brief: Gaussian smooth standard deviation   @range: [1, 7]            @defalut: 7   @value meaning: Larger value means harder smoothing
    Algo_Smooth                = 0x0505, # @brief: enable switch of smooth  @range: [0, 1]  @defalut: 0(disabled)
    Algo_SmoothType            = 0x0506, # @brief: smoothing type           @range: [0, 4]  @defalut: 2  @value meaning: 0(Gaussian smoothing), 1(bilateral smoothing), 2(Z-mean smoothing), 3(Z-bilateral smoothing), 4(Z-median smoothing)
    Algo_ZfRangeMax            = 0x0507, # @brief: filter out points where z-direction is greater than max (mm)   @range: [0, 4000]  @defalut: 3000 @DataType: float
    Algo_ZfRangeMin            = 0x0508, # @brief: filter out points where z-direction is less than min (mm)      @range: [0, 3000]  @defalut: 40   @DataType: float
    Algo_WrapphaseType         = 0x0509, # @brief: projection type of laser                     @range: [0, 10]   @defalut: based on system and mems version
    Algo_FilterType            = 0x050B, # @brief: filtering type  @range: {1, 3}  @defalut: 3  @value meaning:  1(gradient filtering), 3( piece segment match filtering)
    Algo_TriThreshold          = 0x050C, # @brief: filtering threshold of point cloud triangle  @range: [0, 300]  @defalut: 0
    Algo_ShadowThreshold       = 0x050F, # @brief: shadow threshold               @range: [0, 5]       @defalut: 0(disabled)
    Algo_GradNeedSerialNum     = 0x0510, # @brief: continuous effective phase     @range: [1, 5]       @defalut: 3   @remark: It takes effect when gradient filtering and multi-gradient matching are enabled.
    Algo_RecommendedZfRangeMax = 0x0511, # @brief: recommended maximum z-direction distance (mm)       @read and write properties: ReadOnly
    Algo_RecommendedZfRangeMin = 0x0512, # @brief: recommended minimum z-direction distance (mm)       @read and write properties: ReadOnly
    Algo_OutlierRemoval        = 0x0513, # @brief: outlier filtering              @range: [0, 1]       @defalut: 0(disabled)
    Algo_XfRangeMax            = 0x0514, # @brief: upper limit of x-direction coordinate value in point cloud ROI (mm)  @range: [-10000.0, 10000.0]  @defalut: 10000.0   @DataType: float
    Algo_XfRangeMin            = 0x0515, # @brief: lower limit of x-direction coordinate value in point cloud ROI (mm)  @range: [-10000.0, 10000.0]  @defalut: -10000.0  @DataType: float
    Algo_YfRangeMax            = 0x0516, # @brief: upper limit of y-direction coordinate value in point cloud ROI (mm)  @range: [-10000.0, 10000.0]  @defalut: 10000.0   @DataType: float
    Algo_YfRangeMin            = 0x0517, # @brief: lower limit of y-direction coordinate value in point cloud ROI (mm)  @range: [-10000.0, 10000.0]  @defalut: -10000.0  @DataType: float
    Algo_ImageFilterType       = 0x0518, # @brief: type of fringe image filtering  @range: [0, 1]     @defalut: 0   @value meaning: 0 means disabled and 1 means Gaussian filtering
    Algo_SmoothRadius          = 0x0519, # @brief: radius of Z smoothing           @range: [1, 5]     @defalut: 2   @value meaning: Larger value means harder smoothing
    Algo_ZSigma                = 0x051A, # @brief: scale factor in Z smoothing     @range: [20, 150]  @defalut: 20  @value meaning: Larger value means harder smoothing
    Algo_TextureMappingType    = 0x051C, # @brief: texture mapping type            @range: [0, 2]     @defalut: 1   @value meaning: 0 means disabled, 1 means RGB texture mapping; 2 means IR mapping
    Algo_LrCheck               = 0x051D, # @brief: left and right disparity consistency check switch  @ range: [0, 1]     @ defalut: 0   @ value meaning: 0 means disabled, 1 means enabling Consistency Check
    Algo_LrCheckThreshold      = 0x051E, # @brief: disparity constraint threshold  @DataType: float   @ range: [0.3, 2.0] @ defalut: 1.0 @ value meaning: Larger value means harder threshold


class FrameInfo:
    frameIndex = 0
    frameTimestamp = 0.0
    frameTotalDuration = 0.0
    frameAcquisitionDuration = 0.0
    frameComputationDuration = 0.0
    frameTransferDuration = 0.0


# "FrameData" is the data structure used to store the frame data returned from the camera. It will automatically allocate and free memory
# If the item is empty, it means that the data does not to be output
# The length below does not include the number of bytes of the data type .
# point3D: the data storage method is x0y0z0xlylz1x2y2z2..., its length is point3DSize.
# pointUV: UV data, its length is irWidth * irHeight * 2.
# triangleIndices: Triangular patch data, its length is triangleIndicesSize, same as irWidth * irHeight * 6.
# depthmap: depth data, its length is textureWidth * textureHeight when "depthType = 1" in CameraParam. Its length is irWidth * irHeight when "depthType = 2".
# normals: normal vector data(normal[nx ny nz]), its length is irWidth * irHeight * 3.
# pointColor: Color data, its length is pointColorSize, same as irWidth * irHeight * 3.
# texture: raw texture data, its length is textureWidth * textureHeight * 3.
class FrameData:
    def __init__(self):
        # private: store the original ctype(swig) frame data
        self.ctypeFrameData = gen3d.FrameData()
        
        self.frameInfo = FrameInfo()
        self.point3D = []           # float[]  # 3D point cloud data([x, y, z]), length is pointCount * 3
        self.pointUV = []           # float[]  # UV data, length is pointCount * 2
        self.triangleIndices = []   # int32[]  # Triangle indices data, length is triangleIndicesSize
        self.depthmap = []          # float[]  # Depth map data, if align RGB, length is RGB resolution, if not, length is IR resolution
        self.normals = []           # float[]  # normal vector data (normal[nx ny nz curavture])
        self.pointColor = []        # uint8[]  # point color data
        self.texture = []           # uint8[]  # raw texture data (e.g. RGB or IR), if it is RGB, length is RGB resolution, if it is IR, length is IR resolution
        self.remapTexture = []      # uint8[]  # remaped texture(IR) data, it contains a bright and a normal picture for left and right(FYI: monocular camera doesn’t contain right) respectively. Each picture length is irWidth * irHeight.

        self.point3DSize = 0
        self.pointUVSize = 0
        self.triangleIndicesSize = 0
        self.depthmapSize = 0
        self.normalsSize = 0
        self.pointColorSize = 0
        self.textureSize = 0
        self.pointCount = 0
        self.remapTextureSize = 0


# "CameraParam" contains some important camera parameters. It is especially useful when saving images.
class CameraParam(gen3d.CameraParam):
    textureWidth   = 2592
    textureHeight  = 1944
    irWidth    = 1280
    irHeight   = 1024
    monoWidth    = 1280
    monoHeight   = 1024
    irPerNum   = 12
    hdrCnt     = 1
    pixelBytes = 1
    depthType = 1  # DEPTH_MAP_ALIGN_RGB
    reconstructionType = 0  # 0: Binocular Reconstruction 2：Monocular Reconstruction


# Select the desired output, in order to reduce the overall capture time. All chosen outputs will be transported from the Device
class OutputSettings(gen3d.OutputSettings):
    sendPoint3D = True
    sendPointUV = False
    sendTriangleIndices = False
    sendDepthmap = False
    sendNormals = False
    sendPointColor = False
    sendTexture = False
    sendRemapTexture = False


# "CameraInfo" is a data structure of camera information. Equivalent to "handle". Most APIs require it as the first parameter.
class CameraInfo(gen3d.CameraInfo):
    errorCode = 0
    cameraName = ''
    model = ''
    cameraModel = ''
    cameraIP = ''
    port = 60000
    userIP = ''
    serialNum = ''
    macAddr = ''
    cameraSystemVersion = ''      
    algorithmVersion = ''         
    memsVersion = ''               
    cameraOSVersion = ''           
    sdkVersion = ''      
    rgbStatus = 0            # 0 is ok, other errorcode is bad.
    memsStatus = ''            # "-999" is bad, other is mems's temperature
    isDHCP = False
    moduleID = ''
    algoType = 0
    camParam = CameraParam()
    outputSettings = OutputSettings()


# "PyErrorCodeHandler" is an example class for setting the errorCode callback function in GPIO or Async mode. You can override it to implement your own callback function.
class PyErrorCodeHandler(gen3d.ErrorCodeHandler):
    
    def __init__(self):
        gen3d.ErrorCodeHandler.__init__(self)

    def Handle(self, errorCode):
        print("Python ErrorCodeHandler recv error code:", errorCode)


# "PyFrameDataHandler" is an example class for setting the data processing callback function in GPIO or Async mode. You can override it to implement your own callback function.
class PyFrameDataHandler(gen3d.FrameDataHandler):

    def __init__(self):
        gen3d.FrameDataHandler.__init__(self)

    def Handle(self, camInfo, frameData):
        print("Python FrameDataHandler recv from:", camInfo.cameraIP)


# "CAMERA_POSITION" is used for Get3DCameraIntrinsic().
class CAMERA_POSITION(IntEnum):
    CAM_LEFT = 0,
    CAM_RGB = 1,
    CAM_RIGHT = 2


# "EXTRINSIC_TYPE" is used to represent the target coordinate system.
class EXTRINSIC_TYPE(IntEnum):
    POINT_TO_CAM_LEFT = 0,
    POINT_TO_CAM_RGB = 1,
    POINT_TO_CAM_RIGHT = 2
