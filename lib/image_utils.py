# -*- coding: utf-8 -*-

from lib.math_utils import *
import numpy as np
import os
import PIL
from PIL import Image
from pprint import pprint
import sys

def containImage(img, w, h, resampleType="default", bgcolor=[0,0,0]):
    resampleType = Image.LANCZOS if resampleType=="default" else resampleType
    vw, vh = img.size

    if vw == w and vh == h:
        return img

    # create a base image
    w = roundInt(w)
    h = roundInt(h)
    if img.mode=="RGBA" and len(bgcolor)==3:
        bgcolor.append(0)
    baseImg = Image.new(mode=img.mode, size=(w, h), color=tuple(bgcolor))

    ratio = 1.0 * w / h
    vratio = 1.0 * vw / vh

    # first, resize video
    newW = w
    newH = h
    pasteX = 0
    pasteY = 0
    if vratio > ratio:
        newH = w / vratio
        pasteY = roundInt((h-newH) * 0.5)
    else:
        newW = h * vratio
        pasteX = roundInt((w-newW) * 0.5)

    # Lanczos = good for downsizing
    resized = img.resize((roundInt(newW), roundInt(newH)), resample=resampleType)
    baseImg.paste(resized, (pasteX, pasteY))
    return baseImg

def fillImage(img, w, h, resampleType="default", anchorX=0.5, anchorY=0.5):
    vw, vh = img.size
    resampleType = Image.LANCZOS if resampleType=="default" else resampleType

    if vw == w and vh == h:
        return img

    ratio = 1.0 * w / h
    vratio = 1.0 * vw / vh

    # first, resize video
    newW = w
    newH = h
    if vratio > ratio:
        newW = h * vratio
    else:
        newH = w / vratio
    # Lanczos = good for downsizing
    resized = img.resize((roundInt(newW), roundInt(newH)), resample=resampleType)

    # and then crop
    x = 0
    y = 0
    if vratio > ratio:
        x = roundInt((newW - w) * anchorX)
    else:
        y = roundInt((newH - h) * anchorY)
    x1 = x + w
    y1 = y + h
    cropped = resized.crop((x, y, x1, y1))

    return cropped


def pasteImage(im, clipImg, x, y):
    width, height = im.size
    # create a staging image at the same size of the base image, so we can blend properly
    stagingImg = Image.new(mode="RGBA", size=(width, height), color=(0, 0, 0, 0))
    stagingImg.paste(clipImg, (roundInt(x), roundInt(y)))
    im = Image.alpha_composite(im, stagingImg)
    return im

def readImage(fn):
    if not os.path.isfile(fn):
        print(f' Error: {fn} does not exist')
        return False
    try:
        im = Image.open(fn)
    except PIL.UnidentifiedImageError:
        print(f' Error: {fn} could not be opened')
        return False

    return im

def resizeImage(im, w, h, mode="fill", resampleType="default"):
    resampleType = Image.LANCZOS if resampleType=="default" else resampleType
    if mode=="warp":
        return im.resize((roundInt(w), roundInt(h)), resample=resampleType)
    elif mode=="contain":
        return containImage(im, w, h, resampleType=resampleType)
    else:
        return fillImage(im, w, h, resampleType=resampleType)

def resizeCanvas(im, cw, ch):
    canvasImg = Image.new(mode="RGBA", size=(cw, ch), color=(0, 0, 0, 0))
    w, h = im.size
    x = roundInt((cw - w) * 0.5)
    y = roundInt((ch - h) * 0.5)
    newImg = pasteImage(canvasImg, im, x, y)
    return newImg
