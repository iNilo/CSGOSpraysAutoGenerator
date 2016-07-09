# imports
import os.path
import io
import ctypes
import array
from PIL import Image
import math
import array

# structs
class SVTFCreateOptions(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('uiVersion', ctypes.c_uint * 2),
                ('ImageFormat', ctypes.c_uint),
                ('uiFlags', ctypes.c_uint),
                ('uiStartFrame', ctypes.c_uint),
                ('sBumpScale', ctypes.c_float),
                ('sReflectivity', ctypes.c_float * 3),
                ('bMipmaps', ctypes.c_bool),
                ('MipmapFilter', ctypes.c_uint),
                ('MipmapSharpenFilter', ctypes.c_uint),
                ('bThumbnail', ctypes.c_bool),
                ('bReflectivity', ctypes.c_bool),
                ('bResize', ctypes.c_bool),
                ('ResizeMethod', ctypes.c_uint),
                ('ResizeFilter', ctypes.c_uint),
                ('ResizeSharpenFilter', ctypes.c_uint),
                ('uiResizeWidth', ctypes.c_uint),
                ('uiResizeHeight', ctypes.c_uint),
                ('bResizeClamp', ctypes.c_bool),
                ('uiResizeClampWidth', ctypes.c_uint),
                ('uiResizeClampHeight', ctypes.c_uint),
                ('bGammaCorrection', ctypes.c_bool),
                ('sGammaCorrection', ctypes.c_float),
                ('bNormalMap', ctypes.c_bool),
                ('KernelFilter', ctypes.c_uint),
                ('HeightConversionMethod', ctypes.c_uint),
                ('NormalAlphaResult', ctypes.c_uint),
                ('bNormalMinimumZ', ctypes.c_ubyte),
                ('sNormalScale', ctypes.c_float),
                ('bNormalWrap', ctypes.c_bool),
                ('bNormalInvertX', ctypes.c_bool),
                ('bNormalInvertY', ctypes.c_bool),
                ('bNormalInvertZ', ctypes.c_bool),
                ('bSphereMap', ctypes.c_bool)]

# funcs
def pause():
    input('Press enter to continue...')

def printerror(stuff, ext):
    print('  Error %s %s file:\n\n%s\n' % (stuff, ext, VTFLib.vlGetLastError().decode('utf-8')))

def is_power_2(num):
    return num > 0 and ((num & (num - 1)) == 0)

def power_closest(n):
    bigger = 2**(n-1).bit_length()
    smaller = int(bigger / 2)

    if (n - smaller) < (bigger - n):
        return smaller
    else:
        return bigger

# consts
VTFLIB_DIR = './VTFLib.dll'
IMGS_DIR = './imgs/'

# global vars
g_files = []
uiVTFImage = ctypes.c_uint()
uiVMTMaterial = ctypes.c_uint()
uiProcessed = 0
uiCompleted = 0

# main progress
# initialize VTFLib
try:
    VTFLib = ctypes.windll.LoadLibrary(VTFLIB_DIR)
except OSError:
    print('Error loading VTFLib.dll! Please make sure VTFLib.dll is located at the same path as me.')
    exit(1)

VTFLib.vlGetLastError.restype = ctypes.c_char_p
VTFLib.vlImageCreateSingle.restype = ctypes.c_bool
VTFLib.vlMaterialSave.restype = ctypes.c_bool

VTFLib.vlInitialize() # Initialize VTFLib
VTFLib.vlCreateImage(ctypes.byref(uiVTFImage))
VTFLib.vlBindImage(uiVTFImage)
VTFLib.vlCreateMaterial(ctypes.byref(uiVMTMaterial))
VTFLib.vlBindMaterial(uiVMTMaterial)
print('CS:GO Sprays Auto Generator')
print('by mkpoli, 2016')
print()
print('=== Please make sure all img files are in ./imgs/ ===')
pause()
print('=== File list ===')
if not os.path.isdir('./imgs/'):
    print('./imgs/ is not a dir! Exiting...')
    os.makedirs('./imgs/')
    exit(1)
for subdir, dirs, files in os.walk(IMGS_DIR):
    for file in files:
        uiProcessed += 1
        print(str(uiProcessed) + '. ' + file)
        g_files.append(os.path.join(subdir, file))
pause()
if not os.path.isdir('./materials/decals/sprays/'):
    os.makedirs('./materials/decals/sprays/')
print('=== Start Processing == ')
for file in g_files:
    print('Processing "%s"...' % file)
    # open image
    try:
        img = Image.open(file)
    except IOError:
        print(' Error loading input file.\n')
        continue
    
    # display information
    print(' Information:')
    print('  Format: %s' % img.format)
    print('  Size: %d * %d' % img.size)
    print('  Mode: %s' % img.mode)
    print()

    if not is_power_2(img.width) or not is_power_2(img.height):
        print(' Bad Size, Resizing...')
        img = img.resize((power_closest(img.width), power_closest(img.height)), Image.LANCZOS)
        print('  Resized: %d * %d' % img.size)

    oriMod = img.mode
    # creating texture (.vtf)
    print(' Creating texture:')

    # process image
    img = img.convert('RGBA')

    rawdata = img.tobytes()
    data = ctypes.c_char_p(rawdata)
    CreateOptions = SVTFCreateOptions()

    VTFLib.vlImageCreateDefaultCreateStructure(CreateOptions)
    if oriMod == 'RGBA':
        CreateOptions.ImageFormat = 15
    else:
        CreateOptions.ImageFormat = 13
    
    if not VTFLib.vlImageCreateSingle(ctypes.c_uint(img.width), ctypes.c_uint(img.height), data, CreateOptions):
	    printerror('creating', 'vtf')
	    continue
    vtffile = os.path.abspath(os.path.join('./materials/decals/sprays/', os.path.basename(file)[:-3] + 'vtf'))

    print('  Writing "%s"...' % vtffile)
    if not VTFLib.vlImageSave(vtffile.encode('utf-8')):
        printerror('saving', 'vtf')
        continue
    print('  "%s" written.\n' % vtffile)

    # creating materials (.vmt)
    vmtfile = os.path.abspath(os.path.join('./materials/decals/sprays/', os.path.basename(file)[:-3] + 'vmt'))
    VTFLib.vlMaterialCreate(ctypes.c_char_p(b'LightmappedGeneric'))
    VTFLib.vlMaterialGetFirstNode()
    VTFLib.vlMaterialAddNodeString(ctypes.c_char_p(b'$basetexture'), ctypes.c_char_p(vmtfile[12:-4].encode('utf-8')))
    VTFLib.vlMaterialAddNodeInteger(b'$translucent', ctypes.c_uint(1))
    VTFLib.vlMaterialAddNodeInteger(b'$decal', ctypes.c_uint(1))
    VTFLib.vlMaterialAddNodeSingle(b'$decalscale', ctypes.c_float(0.5))
    
    print('  Writing "%s"...' % vmtfile)
    if not VTFLib.vlMaterialSave(vmtfile.encode('utf-8')):
        printerror('saving', 'vmt')
        break
    print('  "%s" written.\n' % vmtfile)
    print()
    print()
    uiCompleted += 1
print('=== Output in ./materials/decals/sprays  ===')

VTFLib.vlDeleteMaterial(uiVMTMaterial);
VTFLib.vlDeleteImage(uiVTFImage);
VTFLib.vlShutdown() # Shutdown VTFLib
print("%d / %d files completed.\n" % (uiCompleted, uiProcessed))
pause()