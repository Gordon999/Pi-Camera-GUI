#!/usr/bin/env python3
import time
import pygame
from pygame.locals import *
import os, sys
import datetime
import subprocess
import signal
import cv2

# set displayed image size (must be less than screen size to allow for menu!!)
cwidth  = 640 
cheight = 480

# set default parameters
mode        = 1       # set camera mode ['off','auto','night'] 
speed       = 100000  # mS x 1000 
ISO         = 0       # 0 = auto or 100,200,400,800 
brightness  = 50      # set camera brightness
contrast    = 0       # set camera contrast
ev          = 0       # eV correction
blue        = 1.2     # blue balance
red         = 1.5     # red balance
extn        = 0       # still file type
vlen        = 10      # in seconds
fps         = 25      # video fps
vformat     = 4       # set video format
a_video     = 0       # set to 1 to annotate date and time on video
tduration   = 0
tinterval   = 60      # time between timelapse shots in seconds
tshots      = 20      # number fo timelapse shots
frame       = 0       # set to 1 for no frame
zx          = int(cwidth/2)
zy          = int(cheight/2)
zoom = 0
igw  = 2592
igh  = 1944

pic_dir     = "/home/pi/Pictures/"
vid_dir     = "/home/pi/Videos/"
config_file = "/home/pi/PiConfig1.txt"

# NOTE if you change any of the above parameters you need to delete /home/pi/PiCconfig5.txt and restart.

# set button sizes
bw = int(cwidth/8)
bh = int(cheight/12)
ft = int(cwidth/48)
fv = int(cwidth/44)

modes    = ['off','auto','night','sports']
extns    = ['jpg','png','bmp','gif']
vwidths  = [640,800,1280,1280,1440,1920]
vheights = [480,600, 720, 960,1080,1080]
vfpss    = [40 , 40,  40,  40,  40,  40] 

# check PiCconfig.txt exists, if not then write default values
if not os.path.exists(config_file):
    points = [mode,speed,ISO,brightness,contrast,frame,int(red*10),int(blue*10),ev,vlen,fps,vformat,a_video,tinterval,tshots,tduration,extn]
    with open(config_file, 'w') as f:
        for item in points:
            f.write("%s\n" % item)

# read PiCconfig.txt
config = []
with open(config_file, "r") as file:
   line = file.readline()
   while line:
      config.append(line.strip())
      line = file.readline()
config = list(map(int,config))

mode        = config[0]
speed       = config[1]
ISO         = config[2]
brightness  = config[3]
contrast    = config[4]
fullscreen  = config[5]
red         = config[6]/10
blue        = config[7]/10
ev          = config[8]
vlen        = config[9]
fps         = config[10]
vformat     = config[11]
a_video     = config[12]
tinterval   = config[13]
tshots      = config[14]
tduration   = config[15]
extn        = config[16]

vwidth    = vwidths[vformat]
vheight   = vheights[vformat]
vfps      = vfpss[vformat]
tduration = tinterval * tshots

parameters = [mode,0,2,speed,1000,5000000,ISO,0,800,brightness,0,100,contrast,-100,100,ev,-12,12,blue,0.1,8,red,0.1,8,extn,0,3]
vparas =     [vlen,1,999,fps,1,40,vformat,0,5,0,0,0,a_video,0,1,0,0,0,0,0,0,tduration,1,9999,tinterval,1,999,tshots,1,99]
pygame.init()
if frame == 0:
   windowSurfaceObj = pygame.display.set_mode((cwidth + (bw*2),cheight ), 0, 24)
else:
   windowSurfaceObj = pygame.display.set_mode((cwidth + bw,cheight), pygame.NOFRAME, 24)
pygame.display.set_caption('Pi Camera')

global greyColor, redColor, greenColor, blueColor, dgryColor, lgrnColor, blackColor, whiteColor, purpleColor, yellowColor,lpurColor,lyelColor
bredColor =   pygame.Color(255,   0,   0)
lgrnColor =   pygame.Color(162, 192, 162)
lpurColor =   pygame.Color(192, 162, 192)
lyelColor =   pygame.Color(192, 192, 162)
blackColor =  pygame.Color(  0,   0,   0)
whiteColor =  pygame.Color(200, 200, 200)
greyColor =   pygame.Color(128, 128, 128)
dgryColor =   pygame.Color( 64,  64,  64)
greenColor =  pygame.Color(  0, 255,   0)
purpleColor = pygame.Color(255,   0, 255)
yellowColor = pygame.Color(255, 255,   0)
blueColor =   pygame.Color(  0,   0, 255)
redColor =    pygame.Color(200,   0,   0)

def button(bcol,col,row, bColor):
   global cwidth,bw,bh
   colors = [greyColor, dgryColor,yellowColor,purpleColor,greenColor,whiteColor,lgrnColor,lpurColor,lyelColor]
   Color = colors[bColor]
   bx = cwidth + (col * bw)
   by = row * bh
   pygame.draw.rect(windowSurfaceObj,Color,Rect(bx,by,bw-1,bh))
   pygame.draw.line(windowSurfaceObj,colors[bcol],(bx,by),(bx+bw,by))
   pygame.draw.line(windowSurfaceObj,greyColor,(bx+bw-1,by),(bx+bw-1,by+bh))
   pygame.draw.line(windowSurfaceObj,colors[bcol],(bx,by),(bx,by+bh-1))
   pygame.draw.line(windowSurfaceObj,dgryColor,(bx,by+bh-1),(bx+bw-1,by+bh-1))
   pygame.display.update(bx, by, bw, bh)
   return

def text(col,row,fColor,top,upd,msg,fsize,bcolor):
   global bh,cwidth,fv
   colors =  [dgryColor, greenColor, yellowColor, redColor, purpleColor, blueColor, whiteColor, greyColor, blackColor, purpleColor,lgrnColor,lpurColor,lyelColor]
   Color  =  colors[fColor]
   bColor =  colors[bcolor]
   bx = cwidth + (col * bw)
   by = row * bh
   if os.path.exists ('/usr/share/fonts/truetype/freefont/FreeSerif.ttf'): 
       fontObj =       pygame.font.Font('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', int(fsize))
   else:
       fontObj =       pygame.font.Font(None, int(fsize))
   msgSurfaceObj = fontObj.render(msg, False, Color)
   msgRectobj =    msgSurfaceObj.get_rect()
   if top == 0:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+1,by+10,bw-4,int(bh/2.2)))
       msgRectobj.topleft = (bx + 5, by + 10)
   elif msg == "Timelapse":
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+2,by+int(bh/1.8),int(bw/2),int(bh/2.2)-1))
       msgRectobj.topleft = (bx+13,  by + int(bh/1.8))
   elif top == 1:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+29,by+int(bh/1.8),int(bw/2),int(bh/2.2)-2))
       msgRectobj.topleft = (bx + 29, by + int(bh/1.8)) #-int(bh/20))
   elif top == 2:
       if bcolor == 1:
           pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,0,cwidth,fv*2))
       msgRectobj.topleft = (0,row * fsize)
                    
   windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
   if upd == 1 and top == 2:
      pygame.display.update(0,0,cwidth,fv*2)
   if upd == 1:
      pygame.display.update(bx, by, bw, bh)

def draw_bar(col,row,color,value):
    global bw,bh,cwidth,parameters
    pygame.draw.rect(windowSurfaceObj,color,Rect(cwidth + col*bw,row * bh,bw-1,10))
    if parameters[((row-1)*3) + 1] > -1: 
        j = value / (parameters[((row-1)*3) + 2] - parameters[((row-1)*3) + 1])  * bw
    else:
        j = int(bw/2) + (value / (parameters[((row-1)*3) + 2] - parameters[((row-1)*3) + 1])  * bw)
    j = min(j,bw-5)
    pygame.draw.rect(windowSurfaceObj,(0,200,0),Rect(cwidth + (col*bw) + 2,row * bh,j+1,10))
    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(cwidth + (col*bw) + j ,row * bh,4,10))
    pygame.display.update()

def draw_Vbar(col,row,color,value):
    global bw,bh,cwidth,vparas
    pygame.draw.rect(windowSurfaceObj,color,Rect(cwidth + col*bw,row * bh,bw-1,10))
    if vparas[((row-1)*3) + 1] > -1: 
        j = value / (vparas[((row-1)*3) + 2] - vparas[((row-1)*3) + 1])  * bw
    else:
        j = int(bw/2) + (value / (vparas[((row-1)*3) + 2] - vparas[((row-1)*3) + 1])  * bw)
    j = min(j,bw-5)
    pygame.draw.rect(windowSurfaceObj,(150,120,150),Rect(cwidth + (col*bw) + 2,row * bh,j+1,10))
    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(cwidth + (col*bw) + j ,row * bh,4,10))
    pygame.display.update()

def preview():
    global p, brightness,contrast,modes,mode,red,blue,ISO,speed,ev,cwidth,cheight,zoom,igw,igh
    speed2 = speed
    if speed2 > 6000000:
        speed2 = 6000000
    rpistr = "raspistill  -w " + str(cwidth) + " -h " + str(cheight) + " -o /run/shm/test.jpg -co " + str(contrast) + " -br " + str(brightness)
    rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
    if modes[mode] != 'off':
        rpistr += " -t 0 -tl 0 -ex " + modes[mode]
    else:
        rpistr += " -t 0 -tl 0 -ss " + str(speed2)
    if ISO > 0:
        rpistr += " -ISO " + str(ISO)
    if ev != 0:
        rpistr += " -ev " + str(ev)
    rpistr += " -n"
    if speed2 > 1000000 and modes[mode] == 'off':
        rpistr += " -bm"
    if zoom == 1:
        zxo = ((zx -((cwidth/2) / (igw/cwidth)))/cwidth)
        zyo = ((zy -((cheight/2) / (igh/cheight)))/cheight)
        rpistr += " -roi " + str(zxo) + "," + str(zyo) + "," + str(cwidth/igw) + "," + str(cheight/igh)
    p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)

# draw buttons
for d in range(1,11):
        button(4,0,d,6)
for d in range(1,6):
        button(3,1,d,7)
for d in range(8,11):
        button(2,1,d,8)
button(4,0,0,0)
button(3,1,0,0)
button(2,1,7,0)
button(5,0,11,0)
button(5,1,11,0)

# write button texts
text(0,0,1,0,1,"CAPTURE",ft,7)
text(0,0,1,1,1,"Still",ft,7)
text(1,0,1,0,1,"CAPTURE",ft,7)
text(1,0,1,1,1,"Video",ft,7)
text(0,1,5,0,1,"Mode",ft,10)
text(0,1,3,1,1,modes[mode],fv,10)
if mode == 0:
    if speed < 1000000:
        text(0,2,5,0,1,"Shutter mS",ft,10)
        text(0,2,3,1,1,str(int(speed/1000)),fv,10)
    else:
        text(0,2,5,0,1,"Shutter S",ft,10)
        text(0,2,3,1,1,str(int(speed/100000)/10),fv,10)
else:
    if speed < 1000000:
        text(0,2,5,0,1,"Shutter mS",ft,10)
        text(0,2,0,1,1,str(int(speed/1000)),fv,10)
    else:
        text(0,2,5,0,1,"Shutter S",ft,10)
        text(0,2,0,1,1,str(int(speed/100000)/10),fv,10)
text(0,3,5,0,1,"ISO",ft,10)
if ISO != 0:
    text(0,3,3,1,1,str(ISO),fv,10)
else:
    text(0,3,3,1,1,"Auto",fv,10)
text(0,4,5,0,1,"Brightness",ft,10)
text(0,4,3,1,1,str(brightness),fv,10)
text(0,5,5,0,1,"Contrast",ft,10)
text(0,5,3,1,1,str(contrast),fv,10)
text(0,8,5,0,1,"Red",ft,10)
text(0,8,3,1,1,str(red)[0:3],fv,10)
text(0,7,5,0,1,"Blue",ft,10)
text(0,7,3,1,1,str(blue)[0:3],fv,10)
text(0,9,5,0,1,"File",ft,10)
text(0,9,3,1,1,extns[extn],fv,10)
text(0,10,5,0,1,"Zoom",ft,10)
text(0,6,5,0,1,"eV",ft,10)
if mode != 0:
    text(0,6,3,1,1,str(ev),fv,10)
else:
    text(0,6,0,1,1,str(ev),fv,10)
text(1,1,5,0,1,"V_Length",ft,11)
text(1,2,5,0,1,"V_FPS",ft,11)
text(1,2,3,1,1,str(fps),fv,11)
text(1,1,3,1,1,str(vlen),fv,11)
text(1,3,5,0,1,"V_width",ft,11)
text(1,3,3,1,1,str(vwidth),fv,11)
text(1,4,5,0,1,"V_height",ft,11)
text(1,4,3,1,1,str(vheight),fv,11)
text(1,5,5,0,1,"V_Annotate",ft,11)
if a_video == 0:
    text(1,5,3,1,1,"OFF",fv,11)
else:
    text(1,5,3,1,1,"ON",fv,11)
text(1,7,1,0,1,"CAPTURE",ft,7)
text(1,7,1,1,1,"Timelapse",ft,7)
text(1,8,5,0,1,"Duration S",ft,12)
text(1,8,3,1,1,str(tduration),fv,12)
text(1,9,5,0,1,"Interval S",ft,12)
text(1,9,3,1,1,str(tinterval),fv,12)
text(1,10,5,0,1,"Shots",ft,12)
text(1,10,3,1,1,str(tshots),fv,12)
text(0,11,2,0,1,"Save Config",fv,7)
text(1,11,2,0,1,"EXIT",fv,7)

# draw sliders
for k in range(3,len(parameters)-3,3):
    draw_bar(0,int(k/3) + 1,lgrnColor,parameters[k])
draw_Vbar(1,1,lpurColor,vlen)
draw_Vbar(1,2,lpurColor,fps)
draw_Vbar(1,8,lyelColor,tduration)
draw_Vbar(1,9,lyelColor,tinterval)
draw_Vbar(1,10,lyelColor,tshots)

text(0,0,6,2,1,"Please Wait, checking camera",int(fv* 1.7),1)
pygame.display.update()

# Check for Pi Camera version
if os.path.exists('test.jpg'):
   os.rename('test.jpg', 'oldtest.jpg')
rpistr = "raspistill -n -o test.jpg -t 100"
os.system(rpistr)
time.sleep(2)
if os.path.exists('test.jpg'):
   imagefile = 'test.jpg'
   image = pygame.image.load(imagefile)
   igw = image.get_width()
   igh = image.get_height()
   if igw == 2592:
      Pi_Cam = 1
      max_speed = 6000000
   elif igw == 3280:
      Pi_Cam = 2
      max_speed = 10000000
   else:
      Pi_Cam = 3
      max_speed = 239000000
else:
   Pi_Cam = 0
   max_speed = 6000000
if Pi_Cam > 0:
    text(0,0,6,2,1,"Found Pi Camera v" + str(Pi_Cam),int(fv*1.7),1)
else:
    text(0,0,6,2,1,"No Pi Camera found",int(fv*1.7),1)

# set maximum speed, based on camera version    
parameters[5] = max_speed
if speed > max_speed:
    speed = max_speed
    if mode == 0:
        if speed < 1000000:
            text(0,2,5,0,1,"Shutter mS",ft,12)
            text(0,2,3,1,1,str(int(speed/1000)),fv,12)
        else:
            text(0,2,5,0,1,"Shutter S",ft,12)
            text(0,2,3,1,1,str(int(speed/100000)/10),fv,12)
    else:
        if speed < 1000000:
            text(0,2,5,0,1,"Shutter mS",ft,12)
            text(0,2,0,1,1,str(int(speed/1000)),fv,12)
        else:
            text(0,2,5,0,1,"Shutter S",ft,12)
            text(0,2,0,1,1,str(int(speed/100000)/10),fv,12)
pygame.display.update()
time.sleep(1)
text(0,0,6,2,1,"Please Wait for preview...",int(fv*1.7),1)

# start preview
preview()

# main loop
while True:
    # load preview image
    if os.path.exists('/run/shm/test.jpg'):
        image = pygame.image.load('/run/shm/test.jpg')
        os.rename('/run/shm/test.jpg', '/run/shm/oldtest.jpg')
        windowSurfaceObj.blit(image, (0, 0))
        if zoom == 1:
            image2 = pygame.surfarray.pixels3d(image)
            crop2 = image2[zy-50:zy+50,zx-50:zx+50]
            gray = cv2.cvtColor(crop2,cv2.COLOR_RGB2GRAY)
            foc = cv2.Laplacian(gray, cv2.CV_64F).var()
            text(20,0,3,2,0,"FOC: " + str(int(foc)),fv* 2,0)
            xx = int(cwidth/2)
            xy = int(cheight/2)
            pygame.draw.line(windowSurfaceObj,redColor,(xx-25,xy),(xx+25,xy),1)
            pygame.draw.line(windowSurfaceObj,redColor,(xx,xy-25),(xx,xy+25),1)
        else:
            text(0,0,6,2,0,"Preview",fv* 2,0)
            zxp = (zx -((cwidth/2) / (igw/cwidth)))
            zyp = (zy -((cheight/2) / (igh/cheight)))
            zxq = (zx - zxp) * 2
            zyq = (zy - zyp) * 2
            if zxp + zxq > cwidth:
                zx = cwidth - int(zxq/2)
                zxp = (zx -((cwidth/2) / (igw/cwidth)))
                zxq = (zx - zxp) * 2
            if zyp + zyq > cheight:
                zy = cheight - int(zyq/2)
                zyp = (zy -((cheight/2) / (igh/cheight)))
                zyq = (zy - zyp) * 2
            if zxp < 0:
                zx = int(zxq/2) + 1
                zxp = 0
                zxq = (zx - zxp) * 2
            if zyp < 0:
                zy = int(zyq/2) + 1
                zyp = 0
                zyq = (zy - zyp) * 2
            pygame.draw.rect(windowSurfaceObj,redColor,Rect(zxp,zyp,zxq,zyq),1)
            pygame.draw.line(windowSurfaceObj,redColor,(zx-25,zy),(zx+25,zy),1)
            pygame.draw.line(windowSurfaceObj,redColor,(zx,zy-25),(zx,zy+25),1)
        pygame.display.update()
    restart = 0
    # read mouse buttons
    buttonx = pygame.mouse.get_pressed()
    if buttonx[0] != 0 :
        time.sleep(0.1)
        pos = pygame.mouse.get_pos()
        mousex = pos[0]
        mousey = pos[1]
        if mousex > cwidth:
            x = int((mousex-cwidth)/int(bw/2))
            y = int((mousey)/bh)
            g = (y*4) + x
            if g == 9 or g == 8:
                if mode == 0:
                    if mousey < (y*bh) + 10:
                        speed = int(((mousex-cwidth) / bw) * (parameters[((y-1)*3) + 2] - parameters[((y-1)*3) + 1])) 
                    elif mousey < (y*bh) + (bh/1.2):
                        if mousex < cwidth + (bw/2):
                            if speed > 5000000:
                                speed +=1000000
                            elif speed > 1000000:
                                speed +=100000
                            elif speed > 100000:
                                speed +=10000
                            else:
                                speed +=1000
                            speed = min(speed,max_speed)
                        else:
                            if speed > 5000000:
                                speed -=1000000
                            elif speed > 1000000:
                                speed -=100000
                            elif speed > 100000:
                                speed -=10000
                            else:
                                speed -=1000
                            speed = max(speed,parameters[4])
                            
                    if speed < 1000000:
                        text(0,2,5,0,1,"Shutter mS",ft,10)
                        text(0,2,3,1,1,str(int(speed/1000)),fv,10)
                    else:
                        text(0,2,5,0,1,"Shutter S",ft,10)
                        text(0,2,3,1,1,str(int(speed/100000)/10),fv,10)
                    draw_bar(0,2,lgrnColor,speed)
                    if mode == 0 and speed < 6000001:
                        tinterval = max(tinterval,int((speed/1000000) * 6.33))
                    if mode == 0 and speed > 6000000:
                        tinterval = max(tinterval,int((speed/1000000)))
                    text(1,9,3,1,1,str(tinterval),fv,12)
                    draw_Vbar(1,7,lyelColor,tinterval)
                    tduration = tinterval * tshots
                    text(1,8,3,1,1,str(tduration),fv,12)
                    draw_Vbar(1,8,lyelColor,tduration)
                    restart = 1
               
            elif g == 12 or g == 13 :
                if mousey < (y*bh) + 10:
                    ISO = int(((mousex-cwidth) / bw) * (parameters[((y-1)*3) + 2] - parameters[((y-1)*3) + 1]))
                    if ISO < 100:
                        ISO = 0
                    elif ISO < 200:
                        ISO = 100
                    elif ISO < 400:
                        ISO = 200
                    elif ISO < 700:
                        ISO = 400
                    else:
                        ISO = 800
                elif mousey < (y*bh) + (bh/1.2):
                    if mousex < cwidth + (bw/2):
                        if ISO == 100:
                            ISO -=100
                        else:
                            ISO = int(ISO / 2)
                        ISO = max(ISO,parameters[7])
                    else:
                        if ISO == 0:
                            ISO +=100
                        else:
                            ISO = ISO * 2
                        ISO = min(ISO,parameters[8])
                if ISO != 0:
                   text(0,3,3,1,1,str(ISO),fv,10)
                else:
                    text(0,3,3,1,1,"Auto",fv,10)
                time.sleep(.25)
                draw_bar(0,3,lgrnColor,ISO)
                restart = 1
                
            elif g == 17 or g == 16:
                if mousey < (y*bh) + 10:
                    brightness = int(((mousex-cwidth) / bw) * (parameters[((y-1)*3) + 2] - parameters[((y-1)*3) + 1])) 
                elif mousey < (y*bh) + (bh/1.2):
                    if mousex > cwidth + (bw/2):
                        brightness +=1
                        brightness = min(brightness,parameters[11])
                    else:
                        brightness -=1
                        brightness = max(brightness,parameters[10])
                text(0,4,3,1,1,str(brightness),fv,10)
                draw_bar(0,4,lgrnColor,brightness)
                restart = 1
                
            elif g == 21 or g == 20:
                if mousey < (y*bh) + 10:
                    contrast = int(((mousex-cwidth) / bw) * (parameters[((y-1)*3) + 2] - parameters[((y-1)*3) + 1])) - 100
                elif mousey < (y*bh) + (bh/1.2):
                    if mousex > cwidth + (bw/2):
                        contrast +=1
                        contrast = min(contrast,parameters[14])
                    else:
                        contrast -=1
                        contrast = max(contrast,parameters[13])
                text(0,5,3,1,1,str(contrast),fv,10)
                draw_bar(0,5,lgrnColor,contrast)
                restart = 1
                
            elif (g == 25 and mode != 0) or (g == 24 and mode != 0):
                if mousey < (y*bh) + 10:
                    ev = int(((mousex-cwidth) / bw) * (parameters[((y-1)*3) + 2] - parameters[((y-1)*3) + 1])) - 12
                elif mousey < (y*bh) + (bh/1.2):
                    if mousex > cwidth + (bw/2):
                        ev +=1
                        ev = min(ev,parameters[17])
                    else:
                        ev -=1
                        ev = max(ev,parameters[16])
                text(0,6,3,1,1,str(ev),fv,10)
                draw_bar(0,6,lgrnColor,ev)
                restart = 1

            elif g == 7 or g == 6:
                if mousey < (y*bh) + 10:
                    vlen = int(((mousex-cwidth - bw) / bw) * (vparas[((y-1)*3) + 2] - vparas[((y-1)*3) + 1]))
                elif mousey < (y*bh) + (bh/1.2):
                    if mousex > cwidth + bw + (bw/2):
                        vlen +=1
                        vlen = min(vlen,vparas[2])
                    else:
                        vlen -=1
                        vlen = max(vlen,vparas[1])
                vlen = min(vlen,vparas[2])
                text(1,1,3,1,1,str(vlen),fv,11)
                draw_Vbar(1,1,lpurColor,vlen)
                restart = 1
                
            elif g == 39 or g == 38 :
                if mousey < (y*bh) + 10:
                    tinterval = int(((mousex-cwidth-bw) / bw) * (vparas[((y-1)*3) + 2] - vparas[((y-1)*3) + 1]))
                elif mousey < (y*bh) + (bh/1.2):
                    if mousex > cwidth + bw + (bw/2):
                        tinterval +=1
                        tinterval = min(tinterval,vparas[26])
                        if mode == 0 and speed < 6000001:
                            tinterval = max(tinterval,int((speed/1000000) * 6.33))
                        if mode == 0 and speed > 6000000:
                            tinterval = max(tinterval,int((speed/1000000)))
                    else:
                        tinterval -=1
                        tinterval = max(tinterval,vparas[25])
                text(1,9,3,1,1,str(tinterval),fv,12)
                draw_Vbar(1,9,lyelColor,tinterval)
                tduration = tinterval * tshots
                text(1,8,3,1,1,str(tduration),fv,12)
                draw_Vbar(1,8,lyelColor,tduration)

            elif g == 35 or g == 34:
                if mousey < (y*bh) + 10:
                    tduration = int(((mousex-cwidth - bw) / bw) * (vparas[((y-1)*3) + 2] - vparas[((y-1)*3) + 1])) 
                elif mousey < (y*bh) + (bh/1.2):
                    if mousex > cwidth + bw + (bw/2):
                        tduration +=1
                        tduration = min(tduration,vparas[23])
                    else:
                        tduration -=1
                        tduration = max(tduration,vparas[22])
                text(1,8,3,1,1,str(tduration),fv,12)
                draw_Vbar(1,8,lyelColor,tduration)
                tshots = int(tduration / tinterval)
                text(1,10,3,1,1,str(tshots),fv,12)
                draw_Vbar(1,10,lyelColor,tshots)
                
            elif g == 43 or g == 42:
                if mousey < (y*bh) + 10:
                    tshots = int(((mousex-cwidth-bw) / bw) * (vparas[((y-1)*3) + 2] - vparas[((y-1)*3) + 1]))
                elif mousey < (y*bh) + (bh/1.2):
                    if mousex > cwidth + bw + (bw/2):
                        tshots +=1
                        tshots = min(tshots,vparas[29])
                    else:
                        tshots -=1
                        tshots = max(tshots,vparas[28])
                text(1,10,3,1,1,str(tshots),fv,12)
                draw_Vbar(1,10,lyelColor,tshots)
                tduration = tinterval * tshots
                text(1,8,3,1,1,str(tduration),fv,12)
                draw_Vbar(1,8,lyelColor,tduration)

            elif g == 46 or g ==47:
                   os.killpg(p.pid, signal.SIGTERM)
                   pygame.display.quit()
                   sys.exit()
                   
            elif g == 14 or g == 18 or g == 15 or g == 19:
                if mousex < cwidth + bw + (bw/2):
                    vformat -=1
                    vformat = max(vformat,vparas[7])
                else:
                    vformat +=1
                    vformat = min(vformat,vparas[8])
                vwidth  = vwidths[vformat]
                vheight = vheights[vformat]
                vfps    = vfpss[vformat]
                text(1,3,3,1,1,str(vwidth),fv,11)
                text(1,4,3,1,1,str(vheight),fv,11)
                time.sleep(.25)

            elif g == 5 or g == 4 :
                if mousex > cwidth + (bw/2):
                    mode +=1
                    mode = min(mode,parameters[2])
                else:
                    mode -=1
                    mode = max(mode,parameters[1])
                if mode != 0:
                    text(0,6,3,1,1,str(ev),fv,10)
                else:
                    text(0,6,0,1,1,str(ev),fv,10)
                if mode == 0:
                    if speed < 1000000:
                        text(0,2,5,0,1,"Shutter mS",ft,10)
                        text(0,2,3,1,1,str(int(speed/1000)),fv,10)
                    else:
                        text(0,2,5,0,1,"Shutter S",ft,10)
                        text(0,2,3,1,1,str(int(speed/100000)/10),fv,10)
                else:
                    if speed < 1000000:
                        text(0,2,5,0,1,"Shutter mS",ft,10)
                        text(0,2,0,1,1,str(int(speed/1000)),fv,10)
                    else:
                        text(0,2,5,0,1,"Shutter S",ft,10)
                        text(0,2,0,1,1,str(int(speed/100000)/10),fv,10)
                text(0,1,3,1,1,modes[mode],fv,10)
                draw_bar(0,2,lgrnColor,speed)
                if mode == 0 and speed < 6000001:
                    tinterval = max(tinterval,int((speed/1000000) * 6.33))
                if mode == 0 and speed > 6000000:
                    tinterval = max(tinterval,int((speed/1000000)))
                text(1,9,3,1,1,str(tinterval),fv,12)
                draw_Vbar(1,9,lyelColor,tinterval)
                tduration = tinterval * tshots
                text(1,8,3,1,1,str(tduration),fv,12)
                draw_Vbar(1,8,lyelColor,tduration)
                time.sleep(.25)
                restart = 1
                   
            elif g == 11  or g == 10:
                   if mousey < (y*bh) + 10:
                       fps = int(((mousex-cwidth-bw) / bw) * (vparas[((y-1)*3) + 2] - vparas[((y-1)*3) + 1]))
                   elif mousey < (y*bh) + (bh/1.2):
                       if mousex > cwidth + bw + (bw/2):
                           fps +=1
                           fps = min(fps,vfps)
                       else:
                           fps -=1
                           fps = max(fps,vparas[4])
                   text(1,2,3,1,1,str(fps),fv,11)
                   draw_Vbar(1,2,lpurColor,fps)
                   
            elif g == 32 or g == 33 :
                   if mousey < (y*bh) + 10:
                       red = (((mousex-cwidth) / bw) * (parameters[((y-1)*3) + 2] - parameters[((y-1)*3) + 1])) 
                   elif mousey < (y*bh) + (bh/1.2):
                       if mousex < cwidth + (bw/2):
                           red -=0.1
                           red = max(red,parameters[22])
                       else:
                           red +=0.1
                           red = min(red,parameters[23])
                   text(0,8,3,1,1,str(red)[0:3],fv,10)
                   draw_bar(0,8,lgrnColor,red)
                   time.sleep(.25)
                   restart = 1

            elif g == 28 or g == 29:
                   if mousey < (y*bh) + 10:
                       blue = (((mousex-cwidth) / bw) * (parameters[((y-1)*3) + 2] - parameters[((y-1)*3) + 1])) 
                   elif mousey < (y*bh) + (bh/1.2):
                       if mousex < cwidth + (bw/2):
                           blue -=0.1
                           blue = max(blue,parameters[19])
                       else:
                           blue +=0.1
                           blue = min(blue,parameters[20])
                   text(0,7,3,1,1,str(blue)[0:3],fv,10)
                   draw_bar(0,7,lgrnColor,blue)
                   time.sleep(.25)
                   restart = 1

            elif g == 36 or g == 37:
                if mousex < cwidth + (bw/2):
                   extn -=1
                   extn = max(extn,parameters[25])
                else:
                   extn +=1
                   extn = min(extn,parameters[26]) 
                text(0,9,3,1,1,extns[extn],fv,10)
                time.sleep(.25)

            elif g == 22 or g == 23:
                   a_video +=1
                   if a_video > 1:
                       a_video = 0
                   if a_video == 0:
                       text(1,5,3,1,1,"OFF",fv,11)
                   else:
                       text(1,5,3,1,1,"ON",fv,11)
                   time.sleep(.5)

            elif g == 40 or g == 41:
                   zoom +=1
                   if zoom > 1:
                       zoom = 0
                       button(4,0,10,6)
                       text(0,10,5,0,1,"Zoom",ft,10)
                   if zoom == 1:
                       button(4,0,10,1)
                       text(0,10,2,0,1,"ZOOMED",ft,0)
                   time.sleep(.25)
                   restart = 1
                       
            elif g == 44 or g ==45:
                   # save config
                   text(0,11,3,0,1,"Save Config",fv,7)
                   config[0] = mode
                   config[1] = speed
                   config[2] = ISO
                   config[3] = brightness
                   config[4] = contrast
                   config[5] = frame
                   config[6] = int(red*10)
                   config[7] = int(blue*10)
                   config[8] = ev
                   config[9] = vlen
                   config[10] = fps
                   config[11] = vformat
                   config[12] = a_video
                   config[13] = tinterval
                   config[14] = tshots
                   config[15] = tduration
                   config[16] = extn
                   with open(config_file, 'w') as f:
                       for item in config:
                           f.write("%s\n" % item)
                   time.sleep(1)
                   text(0,11,2,0,1,"Save Config",fv,7)
    if restart > 0:
        if restart == 1:
            os.killpg(p.pid, signal.SIGTERM)
        text(0,0,6,2,1,"Waiting for preview ...",int(fv*1.7),1)
        preview()
        
    #check for any mouse button presses
    for event in pygame.event.get():
        if event.type == QUIT:
           os.killpg(p.pid, signal.SIGTERM)
           pygame.quit()
        elif (event.type == MOUSEBUTTONUP):
           restart = 0
           mousex, mousey = event.pos
           if mousex < cwidth and zoom == 0:
               zx = mousex
               zy = mousey
           if mousex > cwidth:
               e = int((mousex-cwidth)/int(bw/2))
               f = int(mousey/bh)
               g = (f*4) + e    
               if g == 0 or g == 1:
                   # still
                   os.killpg(p.pid, signal.SIGTERM)
                   button(4,0,0,1)
                   text(0,0,2,0,1,"CAPTURE",ft,0)
                   text(1,0,0,0,1,"CAPTURE",ft,7)
                   text(1,0,0,1,1,"Video",ft,7)
                   text(1,7,0,0,1,"CAPTURE",ft,7)
                   text(1,7,0,1,1,"Timelapse",ft,7)
                   text(0,0,6,2,1,"Please Wait, taking still ...",int(fv*1.7),1)
                   now = datetime.datetime.now()
                   timestamp = now.strftime("%y%m%d%H%M%S")
                   fname =  pic_dir + str(timestamp) + '.' + extns[extn]
                   if speed < 6000001:
                       rpistr = "raspistill -o " + str(fname) + " -e " + extns[extn] + " -co " + str(contrast) + " -br " + str(brightness)
                       rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                       if modes[mode] != 'off':
                           rpistr += " -t 800 -ex " + modes[mode]
                       else:
                           rpistr += " -t 500 -ss " + str(speed)
                       if ISO > 0 and modes[mode] != 'off':
                          rpistr += " -ISO " + str(ISO)
                       if ev != 0 and modes[mode] != 'off':
                          rpistr += " -ev " + str(ev)
                   else:
                       rpistr = "raspistill -t 10 -md 3 -bm -ex off -ag 1 -ss " + str(speed) + " -st -o " + fname + " -e " + extns[extn]
                       rpistr += " -co " + str(contrast) + " -br " + str(brightness)
                       rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                   rpistr += " -n "
                   os.system(rpistr)
                   while not os.path.exists(fname):
                       pass
                   image = pygame.image.load(fname)
                   catSurfacesmall = pygame.transform.scale(image, (cwidth,cheight))
                   windowSurfaceObj.blit(catSurfacesmall, (0, 0))
                   text(0,0,6,2,1,fname,int(fv*1.5),1)
                   pygame.display.update()
                   time.sleep(2)
                   button(4,0,0,0)
                   text(0,0,1,0,1,"CAPTURE",ft,7)
                   text(1,0,1,0,1,"CAPTURE",ft,7)
                   text(1,0,1,1,1,"Video",ft,7)
                   text(0,0,1,1,1,"Still",ft,7)
                   text(1,7,1,0,1,"CAPTURE",ft,7)
                   text(1,7,1,1,1,"Timelapse",ft,7)
                   restart = 2
                                     
               elif g == 2 or g == 3:
                   # video
                   os.killpg(p.pid, signal.SIGTERM)
                   button(3,1,0,1)
                   text(1,0,2,0,1,"CAPTURE",ft,0)
                   text(0,0,0,0,1,"CAPTURE",ft,7)
                   text(0,0,0,1,1,"Still",ft,7)
                   text(1,7,0,0,1,"CAPTURE",ft,7)
                   text(1,7,0,1,1,"Timelapse",ft,7)
                   text(0,0,6,2,1,"Please Wait, taking video ...",int(fv*1.7),1)
                   now = datetime.datetime.now()
                   timestamp = now.strftime("%y%m%d%H%M%S")
                   vname =  vid_dir + str(timestamp) + '.h264'
                   rpistr = "raspivid -t " + str(vlen * 1000) + " -w " + str(vwidth) + " -h " + str(vheight)
                   rpistr += " -p 0,0," + str(cwidth) + "," + str(cheight) + " -fps " + str(fps) + " -o " + vname + " -co " + str(contrast) + " -br " + str(brightness)
                   rpistr += " -awb off -awbg " + str(red) + "," + str(blue) +  " -ISO " + str(ISO)
                   if a_video == 1:
                       rpistr += " -a 12 -a '%Y-%m-%d %Z%z %p:%X' -ae 32,0x8080ff" 
                   speed2 = speed
                   if mode == 0:
                       rpistr +=" -ex off -ss " + str(speed2)
                   else:
                       rpistr +=" -ex " + str(modes[mode]) + " -ev " + str(ev)
                   os.system(rpistr)
                   text(0,0,6,2,1,vname,int(fv*1.5),1)
                   time.sleep(1)
                   button(3,1,0,0)
                   text(0,0,1,0,1,"CAPTURE",ft,7)
                   text(0,0,1,1,1,"Still",ft,7)
                   text(1,0,1,0,1,"CAPTURE",ft,7)
                   text(1,0,1,1,1,"Video",ft,7)
                   text(1,7,1,0,1,"CAPTURE",ft,7)
                   text(1,7,1,1,1,"Timelapse",ft,7)
                   restart = 2
                   
               elif g == 30 or g == 31:
                   # timelapse
                   os.killpg(p.pid, signal.SIGTERM)
                   button(2,1,7,1)
                   text(0,0,0,0,1,"CAPTURE",ft,7)
                   text(1,0,0,0,1,"CAPTURE",ft,7)
                   text(1,0,0,1,1,"Video",ft,7)
                   text(0,0,0,1,1,"Still",ft,7)
                   text(1,7,2,0,1,"CAPTURE",ft,0)
                   text(1,7,2,1,1,"Timelapse",ft,0)
                   tcount = 0
                   if tinterval < 20:
                       text(0,0,6,2,1,"Please Wait, taking Timelapse ...",int(fv*1.7),1)
                       rpistr = "raspistill -n -t " + str(tduration * 1000) + " -tl " + str(tinterval * 1000) + " -o /home/pi/Pictures/%04d.jpg -dt"
                       rpistr += " -bm -co " + str(contrast) + " -br " + str(brightness)
                       rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                       if modes[mode] != 'off':
                           rpistr += " -ex " + modes[mode]
                       else:
                           rpistr += " -ss " + str(speed)
                       if ISO > 0 and modes[mode] != 'off':
                           rpistr += " -ISO " + str(ISO)
                       if ev != 0 and modes[mode] != 'off':
                           rpistr += " -ev " + str(ev)
                       os.system(rpistr)
                   else:
                     while tcount < tshots:
                       tstart = time.monotonic()
                       text(0,0,6,2,1,"Please Wait, taking Timelapse ...",int(fv*1.7),1)
                       now = datetime.datetime.now()
                       timestamp = now.strftime("%y%m%d%H%M%S")
                       fname =  pic_dir + str(timestamp) + '_' + str(tcount) + '.jpg'
                       if speed < 6000001:
                           rpistr = "raspistill  -p 0,0," + str(cwidth) + "," + str(cheight) + " -o " + str(fname) + " -co " + str(contrast) + " -br " + str(brightness)
                           rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                           if modes[mode] != 'off':
                               rpistr += " -t 800 -ex " + modes[mode]
                           else:
                               rpistr += " -t 500 -ss " + str(speed)
                           if ISO > 0 and modes[mode] != 'off':
                               rpistr += " -ISO " + str(ISO)
                           if ev != 0 and modes[mode] != 'off':
                               rpistr += " -ev " + str(ev)
                       else:
                           rpistr = "raspistill -t " + str(tcount) + " -tl " + str(tinterval) + " -md 3 -bm -ex off -ag 1 -ss " + str(speed) + " -st -o " + fname
                           rpistr += " -co " + str(contrast) + " -br " + str(brightness)
                           rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                       rpistr += " -n "
                       os.system(rpistr)
                       while not os.path.exists(fname):
                          pass
                       image = pygame.image.load(fname)
                       catSurfacesmall = pygame.transform.scale(image, (cwidth,cheight))
                       windowSurfaceObj.blit(catSurfacesmall, (0, 0))
                       text(0,0,6,2,1,fname,int(fv*1.5),1)
                       pygame.display.update()
                       tcount +=1
                       while time.monotonic() - tstart < tinterval and tcount < tshots:
                           for event in pygame.event.get():
                               if (event.type == MOUSEBUTTONUP):
                                  mousex, mousey = event.pos
                                  if mousex > cwidth:
                                      e = int((mousex-cwidth)/int(bw/2))
                                      f = int(mousey/bh)
                                      g = (f*4) + e
                                      if g == 30 or g == 31:
                                           tcount = tshots
                   button(2,1,7,0)
                   text(0,0,1,0,1,"CAPTURE",ft,7)
                   text(1,0,1,0,1,"CAPTURE",ft,7)
                   text(1,0,1,1,1,"Video",ft,7)
                   text(0,0,1,1,1,"Still",ft,7)
                   text(1,7,1,0,1,"CAPTURE",ft,7)
                   text(1,7,1,1,1,"Timelapse",ft,7)
                   restart = 2
    if restart > 0:
        if restart == 1:
            os.killpg(p.pid, signal.SIGTERM)
        text(0,0,6,2,1,"Waiting for preview ...",int(fv*1.7),1)
        preview()






                      
