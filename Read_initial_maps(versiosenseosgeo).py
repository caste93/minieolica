# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 16:37:39 2015
Script per calcular el recurs mini eolic
@author: daniel
"""
# Libraries
from PIL import Image

import numpy as np
import os.path
import math


# Find the different information (translation, rotation and scalefactor) needed to change pixels to coordinates 
def pixelsToCoordinatesIni(P1,P2):
    global transMatrix, transVector, scaleFactor, originPointPixel, originPointCoord
    #Initial coordinates of 2 points (lower and lefter points: 1 and 2)
    print 'Calculating the needed information (translation, rotation and scalefactor) to change coordinates-raster to pixel-velocity'
    #p1 = {  'x': 129515.0,
    #        'y': -29683.0   }
    #p2 = {  'x': 135770.0,
    #        'y': -14263.0   }           

    p1 = {  'x': 928133.272888,
            'y': 4587378.29794  }
    p2 = {  'x': 933192.459425,
            'y': 4603732.11196 }
    #Calculate de translation vector, P1 - T = p1            
    Tx = P1[0] - p1['x']
    Ty = P1[1] - p1['y']
    transVector = np.array([Tx,Ty])
       
    #Calculate the 2 vectors
    V = np.array(P2) - np.array(P1)
    v = np.array([p2['x']-p1['x'], p2['y']-p1['y']])
    
    #Calculate the 2 modules
    mod_V = np.sqrt(V.dot(V))
    mod_v = np.sqrt(v.dot(v))
    
    #Calculate the 2 norm vectors
    V_norm = V / mod_V
    v_norm = v / mod_v

    #Calculate the angle between them
    coseno = V_norm[0]*v_norm[0]+V_norm[1]*v_norm[1]
    seno = math.sqrt(1-coseno*coseno)
    
    #Calculate the rotation matrix (P)* [(cos,-sin),(sin,cos)] = (p)
    res = np.array([[coseno,-seno],[seno,coseno]])
    transMatrix = np.linalg.inv(res)
    
    #Calculate the scale factor, and the origin point to apply the scaling
    scaleFactor = mod_V / mod_v
    originPointPixel = np.array(P1)
    originPointCoord = np.array([p1['x'],p1['y']])
    

# Coordinates to pixels
def coordinatesToPixels(p):
#    p = [124660,-18945]
#    p = [129668,-29854]
#    p = [135757,-14281]
    #Change the point to an array
    if not isinstance(p, np.ndarray):
        p = np.array(p)
    
    #Find the vector p - origin    
    v = np.array(p) - np.array(originPointCoord)
    
    #Calculate the module
    mod_v = np.sqrt(v.dot(v))
    
    #Applying the rotation matrix
    #transMatrix_0 = np.linalg.inv(transMatrix)
    v_rotated =  transMatrix.dot(v)
    
    #Applying the scale factor
    if mod_v != 0 :
        mod_scaled_v = v_rotated * scaleFactor
    else:
        mod_scaled_v = v_rotated
    
    #The scaled point
    mod_scaled_p = mod_scaled_v + originPointCoord
    
    #Applying the translation            
    p_new = mod_scaled_p + transVector

    #Return the new value
    return p_new
    

# Reading velocity data (values are stored in a matrix called velArray)
def readInitialVelocityData(vel_from = 0, vel_to = 39):
    global velArray, edgePoints
    #rgb to number of yearly hours
    initial = 250
    step = 250
    rgb_colors_values = {
        '188, 249, 253': 0,
        '163, 225, 249': initial + 1*step,
        '135, 201, 247': initial + 2*step,
        '107, 183, 244': initial + 3*step,
        '78, 163, 241' : initial + 4*step,
        '44, 141, 238' : initial + 5*step,
        '23, 117, 227' : initial + 6*step,
        '23, 91, 213'  : initial + 7*step,
        '21, 70, 196'  : initial + 8*step,
        '17, 46, 178'  : initial + 9*step,
        '9, 23, 165'   : initial + 10*step,
        '0, 0, 147'    : initial + 11*step,
        '52, 52, 52'   : None,      #black
        '255, 255, 255': None       #white
    }
    edgePoints = {}
    #path_vel = '/home/daniel/Documentos/Ofertes/Recurs Eolic/Estudi/Dades inicials/Mapes minieolica/'
    path_vel = 'C:/Users/Pau/Documents/GitHub/arxius/mapes minieolica'
    for i in range(vel_from,vel_to):
        seq = (str(i),str(i+1))
        file = '-'.join(seq) + '.bmp'
        if os.path.isfile(path_vel + file):
            print 'Reading initial velocity from file %s' % file
            im = Image.open(path_vel + file)
            (width, height) = im.size
            width = int(width)
            width_25 = int(width*0.25)
            width_50 = int(width*0.5)
            width_75 = int(width*0.75)
            width_100 = int(width-1)
            height = int(height)
            rgb_im = im.convert('RGB')       
            # Insert the values into a 2D matrix (x= width, y=height)
            # and look for the reference points need to pixelToCoordinates
            pix_max_x = [0,0]
            pix_min_x = [width, height]
            velArray = np.empty((width,height+1))
            for x in range(width):
                for y in range(height):
                    r, g, b = rgb_im.getpixel((x, y))
                    if (r, g, b) == (52, 52, 52):
                        if x > pix_max_x[0]:
                            pix_max_x = [x,abs(y-height)]
                        if x < pix_min_x[0]:
                            pix_min_x = [x,abs(y-height)]
                    rgb = (str(r), str(g), str(b))
                    velArray[x,abs(y-height)] = rgb_colors_values[', '.join(rgb)]
                if (x == width_25) : print '25% done'
                if (x == width_50) : print '50% done'
                if (x == width_75) : print '75% done'
                if (x == width_100): print '100% done'
            edgePoints[i] = {'top-rigth': pix_max_x, 'bottom-left': pix_min_x}
            

# Reading geometry data from the raster file (values are stored in a matrix called geoArray)
def readRasterData(file = 'barcelona_raster_augusto_500x400.asc'):
    global geoArray, top_left_x, resolution_x, top_left_y, resolution_y
    #initial variables
    #path_geo = '/home/daniel/Documentos/Ofertes/Recurs Eolic/Estudi/Geo Raster/'
    path_geo = 'C:/Users/Pau/Documents/GitHub/arxius/'
    #ini_height = 386   # Value needed because the raster file is displaced in z
    if os.path.isfile(path_geo + file):
        print 'Reading initial geometry from file %s' % file       
        from numpy import genfromtxt
        fr = open(path_geo + file, 'r')
        cols = int(fr.readline().split(' ')[1])
        rows = int(fr.readline().split(' ')[1])
        top_left_x = float(fr.readline().split(' ')[1])
        top_left_y = float(fr.readline().split(' ')[1])
        resolution_x = float(fr.readline().split(' ')[1])
        resolution_y = -resolution_x
        top_left_y =   top_left_y + rows*resolution_x 
        NoDataValue = int(fr.readline().split(' ')[1])       
        geoArray = genfromtxt(path_geo + file, delimiter=' ',skip_header=6)
        # Changing NoDataValue into dataArray to nan
        geoArray[geoArray == NoDataValue] = np.nan  
        #How to calculate the mean excluding nan values
        #mdat = np.ma.masked_array(geoArray[1,],np.isnan(geoArray[1,]))
        #mm = np.mean(mdat)
        #mm1 = np.sum(mdat)
        #mm2 = np.std(mdat)
        #mm3 = np.min(mdat)
        #mm4 = np.max(mdat)
    else:
        print 'Reading initial geometry, file %s does not exist' % str(path_geo + file)

#Reading parcel data from the raster file (values are stored in a matrix called parcelArray)
def readRasterParcelData(file = 'raster_prova_new.asc'):
    global parcelArray
    #initial variables
    #path_geo = '/home/daniel/Documentos/Ofertes/Recurs Eolic/Estudi/Geo Raster/'
    path_geo = 'C:/Users/Pau/Documents/GitHub/arxius/'
    if os.path.isfile(path_geo + file):
        print 'Reading initial parcel from file %s' % file
        from numpy import genfromtxt
        fr = open(path_geo + file, 'r')
        cols = int(fr.readline().split(' ')[1])
        rows = int(fr.readline().split(' ')[1])
        top_left_x = float(fr.readline().split(' ')[1])
        top_left_y = float(fr.readline().split(' ')[1])
        resolution_x = float(fr.readline().split(' ')[1])
        resolution_y = -resolution_x
        top_left_y =   top_left_y + rows*resolution_x 
        NoDataValue = int(fr.readline().split(' ')[1])
        print cols, rows, top_left_x, top_left_y, resolution_x, resolution_y, NoDataValue
        parcelArray = genfromtxt(path_geo + file, delimiter=' ',skip_header=6)
        # Changing NoDataValue into dataArray to nan
        parcelArray[parcelArray == NoDataValue] = np.nan
    else:
        print 'Reading initial parcel, file %s does not exist' % str(path_geo + file)
   
# C
def calculateMeanParcelHeight():
    #parcelArray[parcelArray == ]
     
     
     
# Create the mesh of point where the calculations will be done meshCoordArray
def createMesh(cols = 400, rows = 400):
    # create a mesh over the raster geometry
    global meshCoordArray, meshCoordArrayResolution_x, meshCoordArrayResolution_y
    print 'Creating mesh over Raster geometry'
    dim_X , dim_Y = geoArray.shape
    meshCoordArrayResolution_x = resolution_x * dim_X / cols
    meshCoordArrayResolution_y = resolution_y * dim_Y / rows
    meshCoordArray = []
    for y in np.arange(top_left_y+meshCoordArrayResolution_y/2.0,top_left_y+resolution_y*dim_Y, meshCoordArrayResolution_y):
        row_list = []
        for x in np.arange(top_left_x+meshCoordArrayResolution_x/2.0, top_left_x+resolution_x*dim_X, meshCoordArrayResolution_x):
            row_list.append((x, y))
        meshCoordArray.append(row_list) 

    meshCoordArray = np.array(meshCoordArray)
    



#Return the distance between two points
def calculateDistance(p, centralPoint):
    if not isinstance(p, np.ndarray):
        p = np.array(p)
    if not isinstance(centralPoint, np.ndarray):
        centralPoint = np.array(centralPoint)
    v = p - centralPoint
    dist = np.sqrt(v.dot(v))
    return dist
    
    

#Calculate the mean velocity value over the pixel mesh
def calculateMeanVel():
    global meshMeanVelArray
    print('Calculating the mean velocities')
    dim_X , dim_Y, dim_Z = meshCoordArray.shape
    xMin = 0
    yMin = 0
    xMax, yMax = velArray.shape
    minDistance_V = coordinatesToPixels(meshCoordArray[0][0])-coordinatesToPixels(meshCoordArray[1][0])
    minDistance = np.sqrt(minDistance_V.dot(minDistance_V)) * 0.5
    meshMeanVelArray = np.empty((dim_X,dim_Y), dtype='f') 
    intervalPercentage = 10
    listPercentage = [int(dim_Y*x/100.0) for x in range(0,101,intervalPercentage)]
    t0 = time.time()
    for y in np.arange(dim_Y):
        for x in np.arange(dim_X):
            # Find the edges of the square in Coord and
            central_point_coord = meshCoordArray[x][y]
            point_top_left_coord = central_point_coord + np.array([-abs(meshCoordArrayResolution_x*0.5), abs(meshCoordArrayResolution_y*0.5)])
            point_bot_left_coord = central_point_coord + np.array([-abs(meshCoordArrayResolution_x*0.5), -abs(meshCoordArrayResolution_y*0.5)])
            point_top_righ_coord = central_point_coord + np.array([abs(meshCoordArrayResolution_x*0.5), abs(meshCoordArrayResolution_y*0.5)])
            point_bot_righ_coord = central_point_coord + np.array([abs(meshCoordArrayResolution_x*0.5), -abs(meshCoordArrayResolution_y*0.5)])
            #then transform it into Pixel
            central_point_pixel = coordinatesToPixels(central_point_coord)
            point_top_left_pixel = coordinatesToPixels(point_top_left_coord)
            point_bot_left_pixel = coordinatesToPixels(point_bot_left_coord)
            point_top_righ_pixel = coordinatesToPixels(point_top_righ_coord)
            point_bot_righ_pixel = coordinatesToPixels(point_bot_righ_coord)
            
            # Look for the points inside this square, first I look for the near points 
            x_min = int(min(point_top_left_pixel[0],point_bot_left_pixel[0],point_top_righ_pixel[0],point_bot_righ_pixel[0]))
            if x_min < xMin: 
                x_min = xMin
            elif x_min > xMax:
                x_min = xMax
            x_max = int(max(point_top_left_pixel[0],point_bot_left_pixel[0],point_top_righ_pixel[0],point_bot_righ_pixel[0]))
            if x_max > xMax: 
                x_max = xMax
            y_min = int(min(point_top_left_pixel[1],point_bot_left_pixel[1],point_top_righ_pixel[1],point_bot_righ_pixel[1]))           
            if y_min < yMin: 
                y_min = yMin
            elif y_min > yMax:
                y_min = yMax
            y_max = int(max(point_top_left_pixel[1],point_bot_left_pixel[1],point_top_righ_pixel[1],point_bot_righ_pixel[1]))           
            if y_max > yMax: 
                y_max = yMax
            #and then I look for the inside points and points over the edges using the windingNumber
            pointVelocity = []
            for px in np.arange(x_min,x_max,2):
                for py in np.arange(y_min,y_max,2):
                    vel = velArray[px][py]
                    if np.isnan(vel) == False:
                        distance = calculateDistance((px,py), central_point_pixel)
                        if distance <= minDistance:
                            pointVelocity.append(vel)
            meshMeanVelArray[x][y] = mean(pointVelocity)
        if y in listPercentage:
            print '%s%% done in %s seconds' % (str(y*100/dim_Y), str(round(time.time()-t0,0)))
            t0 = time.time()



def writeVelRaster(file='0-1.tiff'):
    #path = '/home/daniel/Documentos/Ofertes/Recurs Eolic/Estudi/Dades inicials/Mapes minieolica/'
    path= 'C:/Users/Pau/Documents/GitHub/arxius/mapes minieolica'
    path_file = path + file
    
    # My array lon / lat
    dim_X, dim_Y, dim_Z = meshCoordArray.shape
    latArray = np.empty((dim_X,dim_Y), dtype='f')
    lonArray = np.empty((dim_X,dim_Y), dtype='f')    
    for y in range(dim_Y):
        for x in range(dim_X):
            val = meshCoordArray[x][y].tolist()
            latArray[x][y] = val[1]
            lonArray[x][y] = val[0]
   
    # For each pixel I know it's latitude and longitude.
    # As you'll see below you only really need the coordinates of
    # one corner, and the resolution of the file.
    
    xmin,ymin,xmax,ymax = [lonArray.min(),latArray.min(),lonArray.max(),latArray.max()]
    nrows,ncols = dim_X, dim_Y
    xres = (xmax-xmin)/float(ncols)
    yres = (ymax-ymin)/float(nrows)
    geotransform=(xmin,xres,0,ymax,0, -yres)   
    # That's (top left x, w-e pixel resolution, rotation (0 if North is up), 
    #         top left y, rotation (0 if North is up), n-s pixel resolution)
    # I don't know why rotation is in twice???
    
    output_raster = gdal.GetDriverByName('GTiff').Create(path_file,ncols, nrows, 1 ,gdal.GDT_Float32)  # Open the file
    output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
    srs = osr.SpatialReference()                 # Establish its coordinate encoding
    srs.ImportFromEPSG(4326)                     # This one specifies WGS84 lat long.
                                                 # Anyone know how to specify the 
                                                 # IAU2000:49900 Mars encoding?
    output_raster.SetProjection( srs.ExportToWkt() )   # Exports the coordinate system 
                                                       # to the file
    output_raster.GetRasterBand(1).WriteArray(meshMeanVelArray)
    
    
#Calculate the new velocity value over each point        
def newCalculatedVelocity(height, meanVel, Zo_local):
        global newvel,Uubl,Zubl,Zo_ref
        print('Calculating new velocities')
        Zo_ref = 0.14
        Zubl = 200
        Uubl = meanVel*(log(Zubl/Zo_ref)/log(10/Zo_ref))
        newVel = Uubl*(log(height/Zo_local)/log(Zubl/Zo_local))
        
        return newVel  
        
#Calculate Medium height in each parcel             
def CalculateMediumHeight(height):
        global medheight
        medheight
        
        return medheight
        
#Calculate Buildings density in each parcel             
def CalculateBuildingDensity():
        
        
        return density        
        
#Calculate rugosity in each parcel             
def CalculateRugosity(medheight, density):
         global Zo
         density = 0.3
         medeight = 20
         print('Clasificating Parcel density')
        if 0.2 > density:
            print ('Low density')
            print('Clasificating Parcel Height')
                if 5 < medheight <= 7.5: 
                    print('Low range')
                    Zo = 0.3
                if 7.5 < medheight <= 12: 
                    print('Medium range')
                    Zo = 0.4
                if 12 < medheight <= 20:
                    print('Tall range')
                    Zo = 0.6
                if medheight > 20:
                    print('high-rise')
                    Zo = 0.8
                else: 
                    print('Land')
                    Zo = 0.14                     #We considered there is no construction
            
        elif 0.2 < density < 0.4:
            print ('Medium density')
            print('Clasificating Parcel Height')
                if 5 < medheight <= 7.5: 
                    print('Low range')
                    Zo = 0.6
                if 7.5 < medheight <= 12: 
                    print('Medium range')
                    Zo = 0.9
                if 12 < medheight <= 20:
                    print('Tall range')
                    Zo = 1.1
                if medheight > 20:
                    print('high-rise')
                    Zo = 1.4
                else: 
                    print('Land')
                    Zo = 0.14                     #We considered there is no construction
        elif 0.4 < density < 0.6:
            print ('High density')
            print('Clasificating Parcel Height')
                if 5 < medheight <= 7.5: 
                    print('Low range')
                    Zo = 0.7
                if 7.5 < medheight <= 12: 
                    print('Medium range')
                    Zo = 1
                if 12 < medheight <= 20:
                    print('Tall range')
                    Zo = 1.3
                if medheight > 20:
                    print('high-rise')
                    Zo = 1.7
                else: 
                    print('Land')
                    Zo = 0.14                     #We considered there is no construction
        elif 0.6 < density:
            print ('City center')
            print('Clasificating Parcel Height')
                if 5 < medheight <= 7.5: 
                    print('Low range')
                    Zo = 0.8
                if 7.5 < medheight <= 12: 
                    print('Medium range')
                    Zo = 1.2
                if 12 < medheight <= 20:
                    print('Tall range')
                    Zo = 1.6
                if medheight > 20:
                    print('high-rise')
                    Zo = 2
                else: 
                    print('Land')
                    Zo = 0.14                     #We considered there is no construction
        else: 
            print('Error Calculating Density')
       
        
       return Zo

""" Main Code """
readRasterData(file='barcelona_raster_augusto_3000x3000 v9.asc')
readRasterParcelData(file = 'raster_prova_new.asc')   #canviar per arxiu prova raster....
readInitialVelocityData(vel_from = 0, vel_to = 1)
pixelsToCoordinatesIni(edgePoints[0]['bottom-left'], edgePoints[0]['top-rigth'])
createMesh(cols = 400, rows = 400)
calculateMeanVel()
calculateMeanParcelHeight()

"""
# Create a jpeg file with the new interpolated velocity 
from osgeo import gdalnumeric
meshMeanVelArrayInteger = meshMeanVelArray.astype(gdalnumeric.uint8)
gdalnumeric.SaveArray(meshMeanVelArrayInteger, "/home/daniel/Documentos/Ofertes/Recurs Eolic/Estudi/vel2.jpeg", format='JPEG')
m_x = meshPixelArray[0:10,0:10,0]
m_y = meshPixelArray[0:10,0:10,1]
m_x.tofile("/home/daniel/Documentos/Ofertes/Recurs Eolic/Estudi/x_points.csv", sep=";")
m_y.tofile("/home/daniel/Documentos/Ofertes/Recurs Eolic/Estudi/y_points.csv", sep=";")
meshMeanVelArray.tofile("/home/daniel/Documentos/Ofertes/Recurs Eolic/Estudi/vel_points.csv", sep=";")
"""