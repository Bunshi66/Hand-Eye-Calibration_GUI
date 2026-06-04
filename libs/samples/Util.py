import ctypes
from tkinter import W
import numpy as np
import os
import datetime
import cv2 as cv
import math
import copy
import pyximport
pyximport.install()
import CyUtil

def create_outdir():
    t = datetime.datetime.now()
    path = os.path.join('.', '3DRecon', t.strftime('%Y%m%d'), t.strftime('%H%M%S'))

    isExists = os.path.exists(path)
    if not isExists:
        os.makedirs(path)
        print(path + ' create success.')
        return path
    else:
        print(path + ' directory is exists.')
        return path
    

def save_point2wrl(frameData, path):
    filePah = os.path.join(path, 't.wrl')
    CyUtil.save_point2Wrl(filePah.encode(), frameData.point3D, frameData.pointCount, frameData.pointUV,
                          frameData.pointCount, frameData.triangleIndices, frameData.triangleIndicesSize)


def save_ir(outputIR, camparam, path, isRemapTexture = False):
    irNum = camparam.irPerNum;
    pixelBytes = camparam.pixelBytes
    imageSubfix = '.bmp'
    if pixelBytes == 2:
        imageSubfix = '.tiff'
    
    lrMultiple = 2
    if camparam.reconstructionType == 2:  # 0: Binocular Reconstruction 2：Monocular Reconstruction
        lrMultiple = 1
    filePrefix = ''
    
    camparam.irHeight
    if (isRemapTexture):
        irNum = 2
        filePrefix = 'remap_'
        height = camparam.irHeight
        width = camparam.irWidth
    else:
        height = camparam.monoHeight
        width = camparam.monoWidth
    
    for i in range(irNum * lrMultiple):
        strFileName = filePrefix + 'L' + str(i + 1) + imageSubfix
        savePath = os.path.join(path, strFileName)
        if (lrMultiple == 2) :
            if i > (irNum - 1):
                strFileName = filePrefix + 'R' + str(i - irNum + 1) + imageSubfix
                savePath = os.path.join(path, strFileName)
        IRData = outputIR[i * pixelBytes * height *
                          width:(i + 1) * pixelBytes * height * width]
        if (pixelBytes == 1):
            dataType = np.uint8
        else:
            dataType = np.uint16
        matrix = np.frombuffer(IRData, dataType).reshape(height, width)    
        cv.imwrite(savePath, matrix)
        cv.waitKey(0)


def save_rgb(texture, camparam, path):
    filePah = os.path.join(path, 't.bmp')
    matrix = np.array(texture).reshape(camparam.textureHeight, camparam.textureWidth, 3)
    cv.imwrite(filePah, matrix)
    cv.waitKey(0)


DEPTH_MAP_ALIGN_RGB = 1

def save_deepmap(depthmap, camparam, path):
    width = camparam.textureWidth
    height = camparam.textureHeight
    if camparam.depthType != DEPTH_MAP_ALIGN_RGB:
        width = camparam.irWidth
        height = camparam.irHeight

    matrixDeep = np.array(depthmap).reshape(height, width)
    matrixDeepTmp = copy.deepcopy(matrixDeep)
    maskZero = matrixDeepTmp == 0
    matrixDeepTmp[maskZero] = 555555

    # Using numpy's built-in functions for matrices is much faster
    max = matrixDeep.max()
    min = matrixDeepTmp.min()
    if math.isclose(max, 0, rel_tol=1e-7):
        max = -555555
    if math.isclose(min, 0, rel_tol=1e-7):
        min = 555555
    print('max:', max)
    print('min:', min)

    maskValue = np.uint8((0 - min) * 255 / (max - min))
    matrixDeepTmp1 = np.uint8((matrixDeep - min) * 255 / (max - min))
    mask = matrixDeepTmp1 == maskValue
    matrixDeepTmp1[mask] = 255

    name = os.path.join(path, 'depth.bmp')
    name_gray = os.path.join(path, 'gray_depth.bmp')
    cv.imwrite(name_gray, matrixDeepTmp1)
    color = cv.applyColorMap(matrixDeepTmp1, cv.COLORMAP_RAINBOW)
    cv.imwrite(name, color)
    cv.waitKey(0)

from PIL import Image
from libtiff import TIFF

def save_deepmap2tiff(depthmap, camParam, path):
    width = camParam.textureWidth
    height = camParam.textureHeight
    if camParam.depthType != DEPTH_MAP_ALIGN_RGB:
        width = camParam.irWidth
        height = camParam.irHeight

    tiffPath = os.path.join(path, 'depth_t.tiff')
    matrixDeep = np.array(depthmap).reshape(height, width)
    im = Image.fromarray(matrixDeep)
    tif = TIFF.open(tiffPath, mode='w')
    tif.write_image(im, compression=None)
    tif.close()


def save_point2tiff(point3D, camparam, path):
    width = camparam.irWidth
    height = camparam.irHeight
    matrixCloud = np.array(point3D).reshape(height, width, 3)

    tiffPath = os.path.join(path, 'depth_t.tiff')
    im = Image.fromarray(matrixCloud)
    tif = TIFF.open(tiffPath, mode='w')
    tif.write_image(im, compression=None)
    tif.close()


def save_rgb_align_depth(texture, pointUV, camparam, path):
    ir_width = camparam.irWidth
    ir_height = camparam.irHeight
    rgb_width = camparam.textureWidth
    rgb_height = camparam.textureHeight

    alignTmp = CyUtil.save_rgb_align_depth(
        texture, pointUV, ir_height, ir_width, rgb_height, rgb_width)
       
    savepath = os.path.join(path, 'align.bmp')
    cv.imwrite(savepath, alignTmp)
    cv.waitKey(0)

def save_point2pcd(frameData, path):
    filePah = os.path.join(path, 't.pcd')
    CyUtil.save_point2pcd(filePah.encode(), frameData.point3D, frameData.pointCount)

def save_point2pcd_b(frameData, path):
    filePah = os.path.join(path, 't.pcd')
    CyUtil.save_point2pcd_b(filePah.encode(), frameData.point3D, frameData.pointCount)

def save_point2obj(frameData, path):
    objPath = os.path.join(path, 't.obj')
    mtlPath = os.path.join(path, 't.mtl')
    CyUtil.save_point2obj(objPath.encode(), mtlPath.encode(), frameData.point3D, frameData.pointCount, frameData.pointUV,
                          frameData.pointCount, frameData.triangleIndices, frameData.triangleIndicesSize)

def save_point2ply(frameData, path):
    filePah = os.path.join(path, 't.ply')
    CyUtil.save_point2ply(filePah.encode(), frameData.point3D, frameData.pointCount,
                          frameData.triangleIndices, frameData.triangleIndicesSize)

def save_point2ply_b(frameData, path):
    filePah = os.path.join(path, 't.ply')

    CyUtil.save_point2ply_b(filePah.encode(), frameData.point3D, frameData.pointCount, frameData.triangleIndices, frameData.triangleIndicesSize)

def save_point2stl(frameData, path):
    filePah = os.path.join(path, 't.stl')

    CyUtil.save_point2stl(filePah.encode(), frameData.point3D, frameData.pointCount, frameData.triangleIndices,
                            frameData.triangleIndicesSize)

def save_point2stl_b(frameData, path):
    filePah = os.path.join(path, 't.stl')

    CyUtil.save_point2stl_b(filePah.encode(), frameData.point3D, frameData.pointCount, frameData.triangleIndices,
                            frameData.triangleIndicesSize)


def save_point2ply_normal_color(frameData, path):
    if frameData.normalsSize and frameData.point3DSize:
        plyPath = path + "/nt.ply"
        fp = open(plyPath, "wb")
        fp.write(b"ply\n")
        fp.write(b"format ascii 1.0\n")
        fp.write(b"element vertex %d\n" % frameData.pointCount)
        fp.write(b"property float x\n")
        fp.write(b"property float y\n")
        fp.write(b"property float z\n")
        fp.write(b"property float nx\n")
        fp.write(b"property float ny\n")
        fp.write(b"property float nz\n")
        fp.write(b"property uchar red\n")
        fp.write(b"property uchar green\n")
        fp.write(b"property uchar blue\n")
        fp.write(b"element face 0\n")
        fp.write(b"property list uchar int vertex_indices\n")
        fp.write(b"end_header\n")

        if frameData.pointColorSize:
            # map pointColor RGB
            for i in range(frameData.pointCount):
                fp.write(b"%f %f %f %f %f %f %d %d %d\n" % (frameData.point3D[i * 3 + 0], frameData.point3D[i * 3 + 1], frameData.point3D[i * 3 + 2], frameData.normals[i *
                        3 + 0], frameData.normals[i * 3 + 1], frameData.normals[i * 3 + 2], frameData.pointColor[i * 3 + 2], frameData.pointColor[i * 3 + 1], frameData.pointColor[i * 3]))              
        else:
            # map gray texture
            for i in range(frameData.pointCount):
                fp.write(b"%f %f %f %f %f %f %d %d %d\n" % (frameData.point3D[i * 3 + 0], frameData.point3D[i * 3 + 1],
                        frameData.point3D[i * 3 + 2], frameData.normals[i * 3 + 0], frameData.normals[i * 3 + 1], frameData.normals[i * 3 + 2], 128, 128, 128))
        fp.close()
