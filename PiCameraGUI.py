#!/usr/bin/env python3
import time
import pygame
from pygame.locals import *
import os, sys
import datetime
import subprocess
import signal
import cv2

# version 17


# set displayed preview image size (must be less than screen size to allow for menu!!)
# recommended 640x480, 800x600, 1280x960
preview_width  = 640 
preview_height = 480

# set default limits
mode        = 1       # set camera mode ['off','auto','night' etc] 
speed       = 13      # position in shutters list
ISO         = 0       # 0 = auto or 100,200,400,800 
brightness  = 50      # set camera brightness
contrast    = 0       # set camera contrast
ev          = 0       # eV correction
blue        = 1.2     # blue balance
red         = 1.5     # red balance
extn        = 0       # still file type
vlen        = 10      # video length in seconds
fps         = 25      # video fps
vformat     = 4       # set video format
a_video     = 0       # set to 1 to annotate date and time on video, set to 2 for showing shutter speed etc
tinterval   = 60      # time between timelapse shots in seconds
tshots      = 20      # number of timelapse shots
frame       = 0       # set to 1 for no frame (i.e. if using Pi 7" touchscreen)
effect      = 0       # picture effects
meter       = 0       # metering mode
awb         = 0       # auto white balance mode
flicker     = 0       # reduce mains flicker, 0-3 = off, auto, 50Hz, 60Hz
drc         = 0       # dynamic range compression, 0-3 = off,low,med,high

# NOTE if you change any of the above still_limits you need to delete the config_file and restart.

# default directories and files
pic_dir     = "/home/pi/Pictures/"
vid_dir     = "/home/pi/Videos/"
config_file = "/home/pi/PiConfig5.txt"

# inital parameters
zx          = int(preview_width/2)
zy          = int(preview_height/2)
zoom        = 0
igw         = 2592
igh         = 1944
zwidth      = igw 
zheight     = igh
tduration   = tinterval * tshots
# set button sizes
bw = int(preview_width/8)
bh = int(preview_height/13)
ft = int(preview_width/52)
fv = int(preview_width/52)

# data
modes        = ['off','auto','night','nightpreview','backlight','spotlight','sports','snow','beach','verylong','fixedfps','antishake','fireworks']
extns        = ['jpg','png','bmp','gif']
vwidths      = [640,800,1280,1280,1440,1920]
vheights     = [480,600, 720, 960,1080,1080]
v_max_fps    = [90 , 40,  40,  40,  40,  30]
shutters     = [-2000,-1600,-1250,-1000,-800,-640,-500,-400,-320,-288,-250,-240,-200,-160,-144,-125,-120,-100,-96,-80,-60,-50,-48,-40,-30,-25,-20,-15,-13,-10,-8,-6,-5,-4,-3,
                0.4,0.5,0.6,0.8,1,2,3,4,5,6,7,8,9,10,15,20,25,30,40,50,60,75,100,120,150,200,220,239]
effects      = ['none','negative','solarise','posterise','whiteboard','blackboard','sketch','denoise','emboss','oilpaint','hatch','gpen','pastel','watercolour','film','blur','saturation']
meters       = ['average','spot','backlit','matrix']
awbs         = ['off','auto','sun','cloud','shade','tungsten','fluorescent','incandescent','flash','horizon','greyworld']
flickers     = ['off','auto','50Hz','60Hz']
drcs         = ['off','low','med','high']
still_limits = ['mode',0,len(modes)-1,'speed',0,len(shutters)-1,'ISO',0,800,'brightness',0,100,'contrast',-100,100,'ev',-12,12,'blue',0.1,8,'red',0.1,8,'extn',0,len(extns)-1,'effect',0,len(effects)-1,'meter',0,len(meters)-1,'awb',0,len(awbs)-1]
video_limits = ['vlen',1,999,'fps',2,40,'vformat',0,len(vwidths)-1,'0',0,0,'a_video',0,2,'zoom',0,4,'Focus',0,1,'tduration',1,9999,'tinterval',1,999,'tshots',1,999,'flicker',0,3,'drc',0,3]

# check PiCconfigX.txt exists, if not then write default values
if not os.path.exists(config_file):
    points = [mode,speed,ISO,brightness,contrast,frame,int(red*10),int(blue*10),ev,vlen,fps,vformat,a_video,tinterval,tshots,tduration,extn,zx,zy,zoom,effect,meter,awb,flicker,drc]
    with open(config_file, 'w') as f:
        for item in points:
            f.write("%s\n" % item)

# read PiCconfigX.txt
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
zx          = config[17]
zy          = config[18]
zoom        = config[19]
effect      = config[20]
meter       = config[21]
awb         = config[22]
flicker     = config[23]
drc         = config[24]

vwidth    = vwidths[vformat]
vheight   = vheights[vformat]
vfps      = v_max_fps[vformat]
tduration = tinterval * tshots

shutter = shutters[speed]
if shutter < 0:
    shutter = abs(1/shutter)
sspeed = int(shutter * 1000000)
if (shutter * 1000000) - int(shutter * 1000000) > 0.5:
    sspeed +=1

pygame.init()
if frame == 0:
   windowSurfaceObj = pygame.display.set_mode((preview_width + (bw*2),preview_height ), 0, 24)
else:
   windowSurfaceObj = pygame.display.set_mode((preview_width + bw,preview_height), pygame.NOFRAME, 24)
pygame.display.set_caption('Pi Camera GUI')

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

def button(col,row, bkgnd_Color,border_Color):
   global preview_width,bw,bh
   colors = [greyColor, dgryColor,yellowColor,purpleColor,greenColor,whiteColor,lgrnColor,lpurColor,lyelColor]
   Color = colors[bkgnd_Color]
   bx = preview_width + (col * bw)
   by = row * bh
   pygame.draw.rect(windowSurfaceObj,Color,Rect(bx,by,bw-1,bh))
   pygame.draw.line(windowSurfaceObj,colors[border_Color],(bx,by),(bx+bw,by))
   pygame.draw.line(windowSurfaceObj,greyColor,(bx+bw-1,by),(bx+bw-1,by+bh))
   pygame.draw.line(windowSurfaceObj,colors[border_Color],(bx,by),(bx,by+bh-1))
   pygame.draw.line(windowSurfaceObj,dgryColor,(bx,by+bh-1),(bx+bw-1,by+bh-1))
   pygame.display.update(bx, by, bw, bh)
   return

def text(col,row,fColor,top,upd,msg,fsize,bkgnd_Color):
   global bh,preview_width,fv
   colors =  [dgryColor, greenColor, yellowColor, redColor, purpleColor, blueColor, whiteColor, greyColor, blackColor, purpleColor,lgrnColor,lpurColor,lyelColor]
   Color  =  colors[fColor]
   bColor =  colors[bkgnd_Color]
   bx = preview_width + (col * bw)
   by = row * bh
   if os.path.exists ('/usr/share/fonts/truetype/freefont/FreeSerif.ttf'): 
       fontObj = pygame.font.Font('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', int(fsize))
   else:
       fontObj = pygame.font.Font(None, int(fsize))
   msgSurfaceObj = fontObj.render(msg, False, Color)
   msgRectobj = msgSurfaceObj.get_rect()
   if top == 0:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+1,by+10,bw-4,int(bh/2.8)))
       msgRectobj.topleft = (bx + 5, by + 8)
   elif msg == "Timelapse" or msg == "Config":
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+2,by+int(bh/1.8),int(bw/2),int(bh/2.2)-1))
       msgRectobj.topleft = (bx+10,  by + int(bh/1.8))
   elif top == 1:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+20,by+int(bh/1.8),int(bw-21),int(bh/2.2)-1))
       msgRectobj.topleft = (bx + 20, by + int(bh/1.8)) 
   elif top == 2:
       if bkgnd_Color == 1:
           pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,0,preview_width,fv*2))
       msgRectobj.topleft = (0,row * fsize)
                    
   windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
   if upd == 1 and top == 2:
      pygame.display.update(0,0,preview_width,fv*2)
   if upd == 1:
      pygame.display.update(bx, by, bw, bh)

def draw_bar(col,row,color,msg,value):
    global bw,bh,preview_width,still_limits,max_speed
    for f in range(0,len(still_limits)-1,3):
        if still_limits[f] == msg:
            pmin = still_limits[f+1]
            pmax = still_limits[f+2]
    if msg == "speed":
        pmax = max_speed
    pygame.draw.rect(windowSurfaceObj,color,Rect(preview_width + col*bw,row * bh,bw-1,10))
    if pmin > -1: 
        j = value / (pmax - pmin)  * bw
    else:
        j = int(bw/2) + (value / (pmax - pmin)  * bw)
    j = min(j,bw-5)
    pygame.draw.rect(windowSurfaceObj,(0,200,0),Rect(preview_width + (col*bw) + 2,row * bh,j+1,10))
    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(preview_width + (col*bw) + j ,row * bh,4,10))
    pygame.display.update()

def draw_Vbar(col,row,color,msg,value):
    global bw,bh,preview_width,video_limits
    for f in range(0,len(video_limits)-1,3):
        if video_limits[f] == msg:
            pmin = video_limits[f+1]
            pmax = video_limits[f+2]
    pygame.draw.rect(windowSurfaceObj,color,Rect(preview_width + col*bw,row * bh,bw-1,10))
    if pmin > -1: 
        j = value / (pmax - pmin)  * bw
    else:
        j = int(bw/2) + (value / (pmax - pmin)  * bw)
    j = min(j,bw-5)
    pygame.draw.rect(windowSurfaceObj,(150,120,150),Rect(preview_width + (col*bw) + 2,row * bh,j+1,10))
    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(preview_width + (col*bw) + j ,row * bh,4,10))
    pygame.display.update()

def preview():
    global p, brightness,contrast,modes,mode,red,blue,ISO,sspeed,ev,preview_width,preview_height,zoom,igw,igh,zx,zy,awbs,awb,effects,effect,meters,meter,flickers,flicker,drcs,drc
    speed2 = sspeed
    if speed2 > 6000000:
        speed2 = 6000000
    rpistr = "raspistill  -w " + str(preview_width) + " -h " + str(preview_height) + " -o /run/shm/test.jpg -co " + str(contrast) + " -br " + str(brightness)
    if modes[mode] == 'fixedfps':
        rpistr += " -t 0 -tl 0 -ex " + modes[mode]
    elif modes[mode] == 'off' :
        rpistr += " -t 0 -tl 0 -ex off -ss " + str(speed2)
    else:
        rpistr += " -t 0 -tl 0 -ex " + modes[mode]
    if ISO > 0:
        rpistr += " -ISO " + str(ISO)
    if ev != 0:
        rpistr += " -ev " + str(ev)
    rpistr += " -n"
    if awb == 0:
        rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
    else:
        rpistr += " -awb " + awbs[awb]
    if effect > 0:
        rpistr += " -ifx " + effects[effect]
    if meter > 0:
        rpistr += " -mm " + meters[meter]
    if flicker > 0:
        rpistr += " -fli " + flickers[flicker]
    if drc > 0:
        rpistr += " -drc " + drcs[drc]
    if speed2 > 1000000 and modes[mode] == 'off':
        rpistr += " -bm"
    if zoom > 0 and zoom < 10:
        zwidth = preview_width * (5-zoom)
        if zwidth > igw:
            zwidth = igw - int(igw/20) 
        zheight = preview_height * (5-zoom)
        if zheight > igh:
            zheight = igh - int(igh/20)
        zxo = ((igw-zwidth)/2)/igw
        zyo = ((igh-zheight)/2)/igh
        rpistr += " -roi " + str(zxo) + "," + str(zyo) + "," + str(zwidth/igw) + "," + str(zheight/igh)
    if zoom == 10:
        zxo = ((zx -((preview_width/2) / (igw/preview_width)))/preview_width)
        zyo = ((zy -((preview_height/2) / (igh/preview_height)))/preview_height)
        rpistr += " -roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
    #print (rpistr)
    p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)

# draw buttons
for d in range(1,13):
        button(0,d,6,4)
for d in range(1,5):
        button(1,d,7,3)
for d in range(7,10):
        button(1,d,8,2)
button(0,0,0,4)
button(1,0,0,3)
button(1,5,0,6)
button(1,6,0,6)
button(1,6,0,2)
button(1,10,6,4)
button(1,11,6,4)
button(1,12,0,5)


# write button texts
text(0,0,1,0,1,"CAPTURE",ft,7)
text(0,0,1,1,1,"Still",ft,7)
text(1,0,1,0,1,"CAPTURE",ft,7)
text(1,0,1,1,1,"Video",ft,7)
text(0,1,5,0,1,"Mode",ft,10)
text(0,1,3,1,1,modes[mode],fv,10)
text(0,2,5,0,1,"Shutter S",ft,10)
if mode == 0:
    if shutters[speed] < 0:
        text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
    else:
        text(0,2,3,1,1,str(shutters[speed]),fv,10)
else:
    if shutters[speed] < 0:
        text(0,2,0,1,1,"1/" + str(abs(shutters[speed])),fv,10)
    else:
        text(0,2,0,1,1,str(shutters[speed]),fv,10)
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
if awb == 0:
    text(0,8,3,1,1,str(red)[0:3],fv,10)
    text(0,7,3,1,1,str(blue)[0:3],fv,10)
else:
    text(0,8,0,1,1,str(red)[0:3],fv,10)
    text(0,7,0,1,1,str(blue)[0:3],fv,10)
text(0,7,5,0,1,"Blue",ft,10)
text(0,9,5,0,1,"File Format",ft,10)
text(0,9,3,1,1,extns[extn],fv,10)
if zoom == 0:
    button(1,5,0,4)
    text(1,5,5,0,1,"Focus  /  Zoom",ft,7)
    text(1,5,3,1,1,"",fv,7)
    text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
elif zoom < 10:
    button(1,5,1,4)
    text(1,5,2,0,1,"ZOOMED",ft,0)
    text(1,5,3,1,1,str(zoom),fv,0)
    text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
else:
    button(1,5,0,4)
    text(1,5,3,0,1,"FOCUS",ft,0)
    text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
  
text(0,6,5,0,1,"eV",ft,10)
if mode != 0:
    text(0,6,3,1,1,str(ev),fv,10)
else:
    text(0,6,0,1,1,str(ev),fv,10)
text(1,1,5,0,1,"V_Length S",ft,11)
text(1,2,5,0,1,"V_FPS",ft,11)
text(1,2,3,1,1,str(fps),fv,11)
text(1,1,3,1,1,str(vlen),fv,11)
text(1,3,5,0,1,"V_Format",ft,11)
text(0,10,5,0,1,"AWB",ft,10)
text(0,10,3,1,1,awbs[awb],fv,10)
text(1,4,5,0,1,"V_Annotate",ft,11)
if a_video == 0:
    text(1,4,3,1,1,"OFF",fv,11)
elif a_video == 1:
    text(1,4,3,1,1,"ON 1",fv,11)
else:
    text(1,4,3,1,1,"ON 2",fv,11)
text(1,6,1,0,1,"CAPTURE",ft,7)
text(1,6,1,1,1,"Timelapse",ft,7)
text(1,7,5,0,1,"Duration S",ft,12)
text(1,7,3,1,1,str(tduration),fv,12)
text(1,8,5,0,1,"Interval S",ft,12)
text(1,8,3,1,1,str(tinterval),fv,12)
text(1,9,5,0,1,"No. of Shots",ft,12)
text(1,9,3,1,1,str(tshots),fv,12)
text(0,11,5,0,1,"Effects",fv,10)
text(0,11,3,1,1,effects[effect],fv,10)
text(0,12,5,0,1,"Metering",fv,10)
text(0,12,3,1,1,meters[meter],fv,10)
text(1,10,5,0,1,"DRC",fv,10)
text(1,10,3,1,1,drcs[drc],fv,10)
text(1,11,5,0,1,"Flicker",fv,10)
text(1,11,3,1,1,flickers[flicker],fv,10)
text(1,12,2,0,1,"Save      EXIT",fv,7)
text(1,12,2,1,1,"Config",fv,7)

# draw sliders
draw_bar(0,3,lgrnColor,'ISO',ISO)
draw_bar(0,4,lgrnColor,'brightness',brightness)
draw_bar(0,5,lgrnColor,'contrast',contrast)
draw_bar(0,6,lgrnColor,'ev',ev)
draw_bar(0,7,lgrnColor,'blue',blue)
draw_bar(0,8,lgrnColor,'red',red)
draw_Vbar(1,1,lpurColor,'vlen',vlen)
draw_Vbar(1,2,lpurColor,'fps',fps)
draw_Vbar(1,7,lyelColor,'tduration',tduration)
draw_Vbar(1,8,lyelColor,'tinterval',tinterval)
draw_Vbar(1,9,lyelColor,'tshots',tshots)

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
      max_shutter = 6
   elif igw == 3280:
      Pi_Cam = 2
      max_shutter = 10
   else:
      Pi_Cam = 3
      max_shutter = 239
else:
   Pi_Cam = 0
   max_shutter = 6

# determine max speed for camera
max_speed = 0
while max_shutter > shutters[max_speed]:
    max_speed +=1
    
if Pi_Cam > 0:
    text(0,0,6,2,1,"Found Pi Camera v" + str(Pi_Cam),int(fv*1.7),1)
else:
    text(0,0,6,2,1,"No Pi Camera found",int(fv*1.7),1)
    
# set maximum speed, based on camera version
if speed > max_speed:
    speed = max_speed
    shutter = shutters[speed]
    if shutter < 0:
        shutter = abs(1/shutter)
    sspeed = int(shutter * 1000000)
    if mode == 0:
        if shutters[speed] < 0:
            text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
        else:
            text(0,2,3,1,1,str(shutters[speed]),fv,10)
    else:
        if shutters[speed] < 0:
            text(0,2,0,1,1,"1/" + str(abs(shutters[speed])),fv,10)
        else:
            text(0,2,0,1,1,str(shutters[speed]),fv,10)

draw_bar(0,2,lgrnColor,'speed',speed)
pygame.display.update()
time.sleep(.25)
text(0,0,6,2,1,"Please Wait for preview...",int(fv*1.7),1)

# start preview
preview()

# main loop
while True:
    time.sleep(0.01)
    # load preview image
    if os.path.exists('/run/shm/test.jpg'):
        image = pygame.image.load('/run/shm/test.jpg')
        os.rename('/run/shm/test.jpg', '/run/shm/oldtest.jpg')
        windowSurfaceObj.blit(image, (0, 0))
        if zoom > 0:
            image2 = pygame.surfarray.pixels3d(image)
            crop2 = image2[zx-50:zx+50,zy-50:zy+50]
            gray = cv2.cvtColor(crop2,cv2.COLOR_RGB2GRAY)
            foc = cv2.Laplacian(gray, cv2.CV_64F).var()
            text(20,0,3,2,0,"Focus: " + str(int(foc)),fv* 2,0)
            xx = int(preview_width/2)
            xy = int(preview_height/2)
            pygame.draw.line(windowSurfaceObj,redColor,(xx-25,xy),(xx+25,xy),1)
            pygame.draw.line(windowSurfaceObj,redColor,(xx,xy-25),(xx,xy+25),1)
        else:
            text(0,0,6,2,0,"Preview",fv* 2,0)
            zxp = (zx -((preview_width/2) / (igw/preview_width)))
            zyp = (zy -((preview_height/2) / (igh/preview_height)))
            zxq = (zx - zxp) * 2
            zyq = (zy - zyp) * 2
            if zxp + zxq > preview_width:
                zx = preview_width - int(zxq/2)
                zxp = (zx -((preview_width/2) / (igw/preview_width)))
                zxq = (zx - zxp) * 2
            if zyp + zyq > preview_height:
                zy = preview_height - int(zyq/2)
                zyp = (zy -((preview_height/2) / (igh/preview_height)))
                zyq = (zy - zyp) * 2
            if zxp < 0:
                zx = int(zxq/2) + 1
                zxp = 0
                zxq = (zx - zxp) * 2
            if zyp < 0:
                zy = int(zyq/2) + 1
                zyp = 0
                zyq = (zy - zyp) * 2
            if zoom == 0:
                pygame.draw.rect(windowSurfaceObj,redColor,Rect(zxp,zyp,zxq,zyq),1)
            pygame.draw.line(windowSurfaceObj,redColor,(zx-25,zy),(zx+25,zy),1)
            pygame.draw.line(windowSurfaceObj,redColor,(zx,zy-25),(zx,zy+25),1)
            if vwidth == 1920 and vheight == 1080:
                pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(preview_width * 0.13,preview_height * 0.22,preview_width * 0.74,preview_height * 0.57),1)
            if vwidth == 1280 and vheight == 720:
                pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(0,0,preview_width,preview_height*.75),1)
        pygame.display.update()
    restart = 0
    # continuously read mouse buttons
    buttonx = pygame.mouse.get_pressed()
    if buttonx[0] != 0 :
        time.sleep(0.1)
        pos = pygame.mouse.get_pos()
        mousex = pos[0]
        mousey = pos[1]
        if mousex > preview_width:
          button_column = int((mousex-preview_width)/bw) + 1
          button_row = int((mousey)/bh) + 1
          if button_column == 1:
            if button_row == 2:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'mode':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousex > preview_width + (bw/2):
                    mode +=1
                    mode = min(mode,pmax)
                else:
                    mode -=1
                    mode = max(mode,pmin)
                if mode != 0:
                    text(0,6,3,1,1,str(ev),fv,10)
                else:
                    text(0,6,0,1,1,str(ev),fv,10)
                if mode == 0:
                    if shutters[speed] < 0:
                        text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
                    else:
                        text(0,2,3,1,1,str(shutters[speed]),fv,10)
                else:
                    if shutters[speed] < 0:
                        text(0,2,0,1,1,"1/" + str(abs(shutters[speed])),fv,10)
                    else:
                        text(0,2,0,1,1,str(shutters[speed]),fv,10)
                text(0,1,3,1,1,modes[mode],fv,10)
                draw_bar(0,2,lgrnColor,'speed',speed)
                if mode == 0 and sspeed < 6000001:
                    tinterval = max(tinterval,int((sspeed/1000000) * 6.33))
                if mode == 0 and sspeed > 6000000:
                    tinterval = max(tinterval,int((sspeed/1000000)))
                text(1,8,3,1,1,str(tinterval),fv,12)
                draw_Vbar(1,9,lyelColor,'tinterval',tinterval)
                tduration = tinterval * tshots
                text(1,7,3,1,1,str(tduration),fv,12)
                draw_Vbar(1,8,lyelColor,'tduration',tduration)
                time.sleep(.25)
                restart = 1

            elif button_row == 3:
                if mode == 0 :
                    for f in range(0,len(still_limits)-1,3):
                        if still_limits[f] == 'speed':
                            pmin = still_limits[f+1]
                            pmax = still_limits[f+2]
                    if mousey < ((button_row-1)*bh) + 10:
                        speed = int(((mousex-preview_width) / bw) * (max_speed-pmin))
                        shutter = shutters[speed]
                        if shutter < 0:
                            shutter = abs(1/shutter)
                        sspeed = int(shutter * 1000000)
                    elif mousey < ((button_row-1)*bh) + (bh/1.2): 
                        if mousex > preview_width + (bw/2):
                            speed +=1
                            speed = min(speed,max_speed)
                        else:
                            speed -=1
                            speed = max(pmin,speed)
                        shutter = shutters[speed]
                        if shutter < 0:
                            shutter = abs(1/shutter)
                        sspeed = int(shutter * 1000000)
                        if (shutter * 1000000) - int(shutter * 1000000) > 0.5:
                            sspeed +=1
   
                    if shutters[speed] < 0:
                        text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
                    else:
                        text(0,2,3,1,1,str(shutters[speed]),fv,10)
                    draw_bar(0,2,lgrnColor,'speed',speed)
                    if mode == 0 and sspeed < 6000001:
                        tinterval = max(tinterval,int((sspeed/1000000) * 6.33))
                    if mode == 0 and sspeed > 6000000:
                        tinterval = max(tinterval,int((sspeed/1000000)))
                    text(1,8,3,1,1,str(tinterval),fv,12)
                    draw_Vbar(1,9,lyelColor,'tinterval',tinterval)
                    tduration = tinterval * tshots
                    text(1,7,3,1,1,str(tduration),fv,12)
                    draw_Vbar(1,8,lyelColor,'tduration',tduration)
                    time.sleep(.25)
                    restart = 1
               
            elif button_row == 4:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'ISO':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    ISO = int(((mousex-preview_width) / bw) * (pmax-pmin))
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
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex < preview_width + (bw/2):
                        if ISO == 100:
                            ISO -=100
                        else:
                            ISO = int(ISO / 2)
                        ISO = max(ISO,pmin)
                    else:
                        if ISO == 0:
                            ISO +=100
                        else:
                            ISO = ISO * 2
                        ISO = min(ISO,pmax)
                if ISO != 0:
                   text(0,3,3,1,1,str(ISO),fv,10)
                else:
                    text(0,3,3,1,1,"Auto",fv,10)
                time.sleep(.25)
                draw_bar(0,3,lgrnColor,'ISO',ISO)
                restart = 1
                
            elif button_row == 5:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'brightness':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    brightness = int(((mousex-preview_width) / bw) * (pmax-pmin)) 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + (bw/2):
                        brightness +=1
                        brightness = min(brightness,pmax)
                    else:
                        brightness -=1
                        brightness = max(brightness,pmin)
                text(0,4,3,1,1,str(brightness),fv,10)
                draw_bar(0,4,lgrnColor,'brightness',brightness)
                restart = 1
                
            elif button_row == 6:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'contrast':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    contrast = int(((mousex-preview_width) / bw) * (pmax-pmin)) - 100
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + (bw/2):
                        contrast +=1
                        contrast = min(contrast,pmax)
                    else:
                        contrast -=1
                        contrast = max(contrast,pmin)
                text(0,5,3,1,1,str(contrast),fv,10)
                draw_bar(0,5,lgrnColor,'contrast',contrast)
                restart = 1
                
            elif button_row == 7 and mode != 0:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'ev':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    ev = int(((mousex-preview_width) / bw) * (pmax-pmin)) - 12
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + (bw/2):
                        ev +=1
                        ev = min(ev,pmax)
                    else:
                        ev -=1
                        ev = max(ev,pmin)
                text(0,6,3,1,1,str(ev),fv,10)
                draw_bar(0,6,lgrnColor,'ev',ev)
                restart = 1
                
            elif button_row == 8 and awb == 0:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'blue':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    blue = (((mousex-preview_width) / bw) * (pmax-pmin)) 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex < preview_width + (bw/2):
                        blue -=0.1
                        blue = max(blue,pmin)
                    else:
                        blue +=0.1
                        blue = min(blue,pmax)
                text(0,7,3,1,1,str(blue)[0:3],fv,10)
                draw_bar(0,7,lgrnColor,'blue',blue)
                time.sleep(.25)
                restart = 1

            elif button_row == 9 and awb == 0 :
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'red':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    red = (((mousex-preview_width) / bw) * (pmax-pmin)) 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex < preview_width + (bw/2):
                        red -=0.1
                        red = max(red,pmin)
                    else:
                        red +=0.1
                        red = min(red,pmax)
                text(0,8,3,1,1,str(red)[0:3],fv,10)
                draw_bar(0,8,lgrnColor,'red',red)
                time.sleep(.25)
                restart = 1

            elif button_row == 10:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'extn':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousex < preview_width + (bw/2):
                   extn -=1
                   extn = max(extn,pmin)
                else:
                   extn +=1
                   extn = min(extn,pmax) 
                text(0,9,3,1,1,extns[extn],fv,10)
                time.sleep(.25)
                
            elif button_row == 11:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'awb':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousex > preview_width + (bw/2):
                    awb +=1
                    awb = min(awb,pmax)
                else:
                    awb -=1
                    awb = max(awb,pmin)
                text(0,10,3,1,1,awbs[awb],fv,10)
                if awb == 0:
                    text(0,8,3,1,1,str(red)[0:3],fv,10)
                    text(0,7,3,1,1,str(blue)[0:3],fv,10)
                else:
                    text(0,8,0,1,1,str(red)[0:3],fv,10)
                    text(0,7,0,1,1,str(blue)[0:3],fv,10)
                time.sleep(.25)
                restart = 1
                
            elif button_row == 12:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'effect':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousex > preview_width + (bw/2):
                    effect +=1
                    effect = min(effect,pmax)
                else:
                    effect -=1
                    effect = max(effect,pmin)
                text(0,11,3,1,1,effects[effect],fv,10)
                time.sleep(.25)
                restart = 1
                
            elif button_row == 13:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'meter':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousex > preview_width + (bw/2):
                    meter +=1
                    meter = min(meter,pmax)
                else:
                    meter -=1
                    meter = max(meter,pmin)
                text(0,12,3,1,1,meters[meter],fv,10)
                time.sleep(.25)
                restart = 1
                
          elif button_column == 2:
            if button_row == 2:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'vlen':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    vlen = int(((mousex-preview_width - bw) / bw) * (pmax-pmin))
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        vlen +=1
                        vlen = min(vlen,pmax)
                    else:
                        vlen -=1
                        vlen = max(vlen,pmin)
                vlen = min(vlen,video_limits[2])
                text(1,1,3,1,1,str(vlen),fv,11)
                draw_Vbar(1,1,lpurColor,'vlen',vlen)
                #restart = 1
                time.sleep(.25)
 
            elif button_row == 3:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'fps':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    fps = int(((mousex-preview_width-bw) / bw) * (pmax-pmin))
                    fps = min(fps,vfps)
                    fps = max(fps,pmin)
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        fps +=1
                        fps = min(fps,vfps)
                    else:
                        fps -=1
                        fps = max(fps,video_limits[4])
                text(1,2,3,1,1,str(fps),fv,11)
                draw_Vbar(1,2,lpurColor,'fps',fps)
                time.sleep(.25)
                   
            elif button_row == 4 and zoom == 0:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'vformat':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousex < preview_width + bw + (bw/2):
                    vformat -=1
                    vformat = max(vformat,pmin)
                else:
                    vformat +=1
                    vformat = min(vformat,pmax)
                vwidth  = vwidths[vformat]
                vheight = vheights[vformat]
                vfps    = v_max_fps[vformat]
                fps = min(fps,vfps)
                video_limits[5] = vfps
                text(1,2,3,1,1,str(fps),fv,11)
                draw_Vbar(1,2,lpurColor,'fps',fps)
                text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                time.sleep(.25)

            elif button_row == 5:
                a_video +=1
                if a_video > 2:
                    a_video = 0
                if a_video == 0:
                    text(1,4,3,1,1,"OFF",fv,11)
                elif a_video == 1:
                    text(1,4,3,1,1,"ON 1",fv,11)
                else:
                    text(1,4,3,1,1,"ON 2",fv,11)
                time.sleep(.5)

            elif button_row == 6:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'zoom':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousex >  preview_width + bw + (bw/2) and zoom == 0:
                    zoom +=1
                    zoom = min(zoom,pmax)
                    button(1,5,1,4)
                    text(1,5,2,0,1,"ZOOMED",ft,0)
                    text(1,5,3,1,1,str(zoom),fv,0)
                    text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
                elif mousex >  preview_width + bw + (bw/2) and zoom > 0 and zoom != 10:
                    zoom +=1
                    zoom = min(zoom,pmax)
                    button(1,5,1,4)
                    text(1,5,2,0,1,"ZOOMED",ft,0)
                    text(1,5,3,1,1,str(zoom),fv,0)
                    text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
                elif mousex <  preview_width + bw + (bw/2) and zoom > 0 and zoom < 10:
                    zoom -=1
                    if zoom == 0:
                       button(1,5,0,4)
                       text(1,5,5,0,1,"Focus  /  Zoom",ft,7)
                       text(1,5,3,1,1,"",fv,7)
                       text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                    else:
                       button(1,5,1,4)
                       text(1,5,2,0,1,"ZOOMED",ft,0)
                       text(1,5,3,1,1,str(zoom),fv,0)
                       text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
                elif mousex <  preview_width + bw + (bw/2) and zoom == 0:
                    zoom = 10
                    button(1,5,1,6)
                    text(1,5,3,0,1,"FOCUS",ft,0)
                    text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
                elif zoom == 10:
                    zoom = 0
                    button(1,5,0,4)
                    text(1,5,5,0,1,"Zoom  /  Focus",ft,7)
                    text(1,5,3,1,1,"",fv,7)
                    text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                    
                    
                       
                time.sleep(.25)
                restart = 1

            elif button_row == 8:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'tduration':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    tduration = int(((mousex-preview_width - bw) / bw) * (pmax-pmin)) 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        tduration +=1
                        tduration = min(tduration,pmax)
                    else:
                        tduration -=1
                        tduration = max(tduration,pmin)
                text(1,7,3,1,1,str(tduration),fv,12)
                draw_Vbar(1,7,lyelColor,'tduration',tduration)
                tshots = int(tduration / tinterval)
                text(1,9,3,1,1,str(tshots),fv,12)
                draw_Vbar(1,9,lyelColor,'tshots',tshots)
                time.sleep(.25)

            elif button_row == 9:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'tinterval':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    tinterval = int(((mousex-preview_width-bw) / bw) * (pmax - pmin))
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        tinterval +=1
                        tinterval = min(tinterval,pmax)
                        if mode == 0 and sspeed < 6000001:
                            tinterval = max(tinterval,int((sspeed/1000000) * 6.33))
                        if mode == 0 and sspeed > 6000000:
                            tinterval = max(tinterval,int((sspeed/1000000)))
                    else:
                        tinterval -=1
                        tinterval = max(tinterval,pmin)
                text(1,8,3,1,1,str(tinterval),fv,12)
                draw_Vbar(1,8,lyelColor,'tinterval',tinterval)
                tduration = tinterval * tshots
                text(1,7,3,1,1,str(tduration),fv,12)
                draw_Vbar(1,7,lyelColor,'tduration',tduration)
                time.sleep(.25)
                
            elif button_row == 10:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'tshots':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    tshots = int(((mousex-preview_width-bw) / bw) * (pmax-pmin))
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        tshots +=1
                        tshots = min(tshots,pmax)
                    else:
                        tshots -=1
                        tshots = max(tshots,pmin)
                text(1,9,3,1,1,str(tshots),fv,12)
                draw_Vbar(1,9,lyelColor,'tshots',tshots)
                tduration = tinterval * tshots
                text(1,7,3,1,1,str(tduration),fv,12)
                draw_Vbar(1,7,lyelColor,'tduration',tduration)
                time.sleep(.25)

            elif button_row == 11:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'drc':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousex > preview_width + bw + (bw/2):
                    drc +=1
                    drc = min(drc,pmax)
                else:
                    drc -=1
                    drc = max(drc,pmin)
                text(1,10,3,1,1,drcs[drc],fv,10)
                time.sleep(.25)
                restart = 1
                
            elif button_row == 12:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'flicker':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousex > preview_width + bw + (bw/2):
                    flicker +=1
                    flicker = min(flicker,pmax)
                else:
                    flicker -=1
                    flicker = max(flicker,pmin)
                text(1,11,3,1,1,flickers[flicker],fv,10)
                time.sleep(.25)
                restart = 1
                
                
            elif button_row == 13:
                if mousex < preview_width + bw + (bw/2):
                   # save config
                   text(1,12,3,1,1,"Config",fv,7)
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
                   config[17] = zx
                   config[18] = zy
                   config[19] = zoom
                   config[20] = effect
                   config[21] = meter
                   config[22] = awb
                   config[23] = flicker
                   config[24] = drc
                   with open(config_file, 'w') as f:
                       for item in config:
                           f.write("%s\n" % item)
                   time.sleep(1)
                   text(1,12,2,1,1,"Config",fv,7)
                else: 
                   os.killpg(p.pid, signal.SIGTERM)
                   pygame.display.quit()
                   sys.exit()
                   
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
            if mousex < preview_width and zoom == 0:
                zx = mousex
                zy = mousey
            if mousex > preview_width:
              button_column = int((mousex-preview_width)/bw) + 1
              button_row = int((mousey)/bh) + 1
              y = button_row-1
              if button_column == 1:    
                if button_row == 1:
                   # still
                   os.killpg(p.pid, signal.SIGTERM)
                   button(0,0,1,4)
                   text(0,0,2,0,1,"CAPTURE",ft,0)
                   text(1,0,0,0,1,"CAPTURE",ft,7)
                   text(1,0,0,1,1,"Video",ft,7)
                   text(1,6,0,0,1,"CAPTURE",ft,7)
                   text(1,6,0,1,1,"Timelapse",ft,7)
                   text(0,0,6,2,1,"Please Wait, taking still ...",int(fv*1.7),1)
                   now = datetime.datetime.now()
                   timestamp = now.strftime("%y%m%d%H%M%S")
                   fname =  pic_dir + str(timestamp) + '.' + extns[extn]
                   if speed < 6000001:
                       rpistr = "raspistill -o " + str(fname) + " -e " + extns[extn] + " -co " + str(contrast) + " -br " + str(brightness)
                       rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                       zwidth  = preview_width * (5-zoom)
                       if zwidth > igw:
                           zwidth = igw - int(igw/20) 
                       zheight = preview_height * (5-zoom)
                       if zheight > igh:
                           zheight = igh - int(igh/20)
                       if zoom == 10:
                           rpistr += " -w " + str(preview_width) + " -h " + str(preview_height)
                       elif zoom > 0 and zoom < 10:
                           rpistr += " -w " + str(zwidth) + " -h " + str(zheight)
                       if modes[mode] != 'off':
                           rpistr += " -t 800 -ex " + modes[mode]
                       else:
                           rpistr += " -t 500 -ex off -ss " + str(sspeed)
                       if ISO > 0 and modes[mode] != 'off':
                          rpistr += " -ISO " + str(ISO)
                       if ev != 0 and modes[mode] != 'off':
                          rpistr += " -ev " + str(ev)
                   else:
                       rpistr = "raspistill -t 10 -md 3 -bm -ex off -ag 1 -ss " + str(sspeed) + " -st -o " + fname + " -e " + extns[extn]
                       zwidth  = preview_width * (5-zoom)
                       zheight = preview_height * (5-zoom)
                       if zoom == 10:
                           rpistr += " -w " + str(preview_width) + " -h " + str(preview_height)
                       elif zoom > 0 and zoom < 10:
                           rpistr += " -w " + str(zwidth) + " -h " + str(zheight)
                       rpistr += " -co " + str(contrast) + " -br " + str(brightness)
                       rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                   rpistr += " -n "
                   if awb == 0:
                       rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                   else:
                       rpistr += " -awb " + awbs[awb]
                   if effect > 0:
                       rpistr += " -ifx " + effects[effect]
                   if meter > 0:
                       rpistr += " -mm " + meters[meter]
                   if flicker > 0:
                       rpistr += " -fli " + flickers[flicker]
                   if drc > 0:
                       rpistr += " -drc " + drcs[drc]
                   if zoom > 0 and zoom < 10:
                       zwidth  = preview_width  * (5-zoom)
                       if zwidth > igw:
                           zwidth = igw - int(igw/20) 
                       zheight = preview_height * (5-zoom)
                       if zheight > igh:
                           zheight = igh - int(igh/20)
                       rpistr += " -w " + str(zwidth) + " -h " + str(zheight)
                       zxo = ((igw-zwidth)/2)/igw
                       zyo = ((igh-zheight)/2)/igh
                       rpistr += " -roi " + str(zxo) + "," + str(zyo) + "," + str(zwidth/igw) + "," + str(zheight/igh)
                   if zoom == 10:
                       rpistr += " -w " + str(preview_width) + " -h " + str(preview_height)
                       zxo = ((zx -((preview_width/2) / (igw/preview_width)))/preview_width)
                       zyo = ((zy -((preview_height/2) / (igh/preview_height)))/preview_height)
                       rpistr += " -roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                   #print (rpistr)
                   os.system(rpistr)
                   while not os.path.exists(fname):
                       pass
                   image = pygame.image.load(fname)
                   catSurfacesmall = pygame.transform.scale(image, (preview_width,preview_height))
                   windowSurfaceObj.blit(catSurfacesmall, (0, 0))
                   text(0,0,6,2,1,fname,int(fv*1.5),1)
                   pygame.display.update()
                   time.sleep(2)
                   button(0,0,0,4)
                   text(0,0,1,0,1,"CAPTURE",ft,7)
                   text(1,0,1,0,1,"CAPTURE",ft,7)
                   text(1,0,1,1,1,"Video",ft,7)
                   text(0,0,1,1,1,"Still",ft,7)
                   text(1,6,1,0,1,"CAPTURE",ft,7)
                   text(1,6,1,1,1,"Timelapse",ft,7)
                   restart = 2
 
              if button_column == 2:                       
                if button_row == 1:
                   # video
                   os.killpg(p.pid, signal.SIGTERM)
                   button(1,0,1,3)
                   text(1,0,2,0,1,"CAPTURE",ft,0)
                   text(0,0,0,0,1,"CAPTURE",ft,7)
                   text(0,0,0,1,1,"Still",ft,7)
                   text(1,6,0,0,1,"CAPTURE",ft,7)
                   text(1,6,0,1,1,"Timelapse",ft,7)
                   text(0,0,6,2,1,"Please Wait, taking video ...",int(fv*1.7),1)
                   now = datetime.datetime.now()
                   timestamp = now.strftime("%y%m%d%H%M%S")
                   vname =  vid_dir + str(timestamp) + '.h264'
                   rpistr = "raspivid -t " + str(vlen * 1000)
                   if zoom == 0:
                       rpistr += " -w " + str(vwidth) + " -h " + str(vheight)
                   elif zoom > 0 :
                       rpistr += " -w " + str(preview_width) + " -h " + str(preview_height)
                   if zoom > 0 and Pi_Cam != 3:
                       rpistr += " --mode 2"
                   if zoom > 0 and Pi_Cam == 3:
                       rpistr += " --mode 3"
                   speed2 = sspeed
                   if mode == 0:
                       rpistr +=" -ex off -ss " + str(speed2) + " -fps " + str(fps)
                   elif modes[mode] == "fixedfps":
                       rpistr +=" -ex fixedfps  -ss " + str(speed2) + " -fps " + str(fps)
                   else:
                       rpistr +=" -ex " + str(modes[mode]) + " -ev " + str(ev) + " -fps " + str(fps)
                   rpistr += " -p 0,0," + str(preview_width) + "," + str(preview_height) + " -o " + vname + " -co " + str(contrast) + " -br " + str(brightness)
                   rpistr += " -awb off -awbg " + str(red) + "," + str(blue) +  " -ISO " + str(ISO)
                   if awb == 0:
                       rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                   else:
                       rpistr += " -awb " + awbs[awb]
                   if effect > 0:
                       rpistr += " -ifx " + effects[effect]
                   if meter > 0:
                       rpistr += " -mm " + meters[meter]
                   if flicker > 0:
                       rpistr += " -fli " + flickers[flicker]
                   if drc > 0:
                       rpistr += " -drc " + drcs[drc]
                   if a_video == 1:
                       rpistr += " -a 12 -a '%d-%m-%Y %X' -ae 32,0x8080ff"
                   if a_video == 2:
                       rpistr += " -a 12 -a 16 -a 64 " 
                   if zoom > 0 and zoom < 10:
                       zwidth = preview_width * (5-zoom)
                       if zwidth > igw:
                           zwidth = igw - int(igw/20) 
                       zheight = preview_height * (5-zoom)
                       if zheight > igh:
                           zheight = igh - int(igh/20)
                       zxo = ((igw-zwidth)/2)/igw
                       zyo = ((igh-zheight)/2)/igh
                       rpistr += " -roi " + str(zxo) + "," + str(zyo) + "," + str(zwidth/igw) + "," + str(zheight/igh)
                   if zoom == 10:
                       zxo = ((zx -((preview_width/2) / (igw/preview_width)))/preview_width)
                       zyo = ((zy -((preview_height/2) / (igh/preview_height)))/preview_height)
                       rpistr += " -roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                   
                   #print (rpistr)
                   os.system(rpistr)
                   text(0,0,6,2,1,vname,int(fv*1.5),1)
                   time.sleep(1)
                   button(1,0,0,3)
                   text(0,0,1,0,1,"CAPTURE",ft,7)
                   text(0,0,1,1,1,"Still",ft,7)
                   text(1,0,1,0,1,"CAPTURE",ft,7)
                   text(1,0,1,1,1,"Video",ft,7)
                   text(1,6,1,0,1,"CAPTURE",ft,7)
                   text(1,6,1,1,1,"Timelapse",ft,7)
                   restart = 2
                   
                elif button_row == 7:
                   # timelapse
                   os.killpg(p.pid, signal.SIGTERM)
                   button(1,6,1,2)
                   text(0,0,0,0,1,"CAPTURE",ft,7)
                   text(1,0,0,0,1,"CAPTURE",ft,7)
                   text(1,0,0,1,1,"Video",ft,7)
                   text(0,0,0,1,1,"Still",ft,7)
                   text(1,6,2,0,1,"CAPTURE",ft,0)
                   text(1,6,2,1,1,"Timelapse",ft,0)
                   tcount = 0
                   if tinterval < 20:
                       text(0,0,6,2,1,"Please Wait, taking Timelapse ...",int(fv*1.7),1)
                       rpistr = "raspistill -n -t " + str(tduration * 1000) + " -tl " + str(tinterval * 1000) + " -o /home/pi/Pictures/%04d.jpg -dt"
                       rpistr += " -bm -co " + str(contrast) + " -br " + str(brightness)
                       rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                       if modes[mode] != 'off':
                           rpistr += " -ex " + modes[mode]
                       else:
                           rpistr += " -ex off -ss " + str(sspeed)
                       if ISO > 0 and modes[mode] != 'off':
                           rpistr += " -ISO " + str(ISO)
                       if ev != 0 and modes[mode] != 'off':
                           rpistr += " -ev " + str(ev)
                       if awb == 0:
                           rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                       else:
                           rpistr += " -awb " + awbs[awb]
                       if effect > 0:
                           rpistr += " -ifx " + effects[effect]
                       if meter > 0:
                           rpistr += " -mm " + meters[meter]
                       if flicker > 0:
                           rpistr += " -fli " + flickers[flicker]
                       if drc > 0:
                           rpistr += " -drc " + drcs[drc]
                       if zoom > 0 and zoom < 10:
                           zwidth  = preview_width  * (5-zoom)
                           if zwidth > igw:
                               zwidth = igw - int(igw/20) 
                           zheight = preview_height * (5-zoom)
                           if zheight > igh:
                               zheight = igh - int(igh/20)
                           rpistr += " -w " + str(zwidth) + " -h " + str(zheight)
                           zxo = ((igw-zwidth)/2)/igw
                           zyo = ((igh-zheight)/2)/igh
                           rpistr += " -roi " + str(zxo) + "," + str(zyo) + "," + str(zwidth/igw) + "," + str(zheight/igh)
                       if zoom == 10:
                           rpistr += " -w " + str(preview_width) + " -h " + str(preview_height)
                           zxo = ((zx -((preview_width/2) / (igw/preview_width)))/preview_width)
                           zyo = ((zy -((preview_height/2) / (igh/preview_height)))/preview_height)
                           rpistr += " -roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                       os.system(rpistr)
                   else:
                     while tcount < tshots:
                       tstart = time.monotonic()
                       text(0,0,6,2,1,"Please Wait, taking Timelapse ...",int(fv*1.7),1)
                       now = datetime.datetime.now()
                       timestamp = now.strftime("%y%m%d%H%M%S")
                       fname =  pic_dir + str(timestamp) + '_' + str(tcount) + '.jpg'
                       if speed < 6000001:
                           rpistr = "raspistill  -p 0,0," + str(preview_width) + "," + str(preview_height) + " -o " + str(fname) + " -co " + str(contrast) + " -br " + str(brightness)
                           rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                           if modes[mode] != 'off':
                               rpistr += " -t 800 -ex " + modes[mode]
                           else:
                               rpistr += " -t 500 -ex off -ss " + str(sspeed)
                           if ISO > 0 and modes[mode] != 'off':
                               rpistr += " -ISO " + str(ISO)
                           if ev != 0 and modes[mode] != 'off':
                               rpistr += " -ev " + str(ev)
                       else:
                           rpistr = "raspistill -t " + str(tcount) + " -tl " + str(tinterval) + " -md 3 -bm -ex off -ag 1 -ss " + str(speed) + " -st -o " + fname
                           rpistr += " -co " + str(contrast) + " -br " + str(brightness)
                           rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                       rpistr += " -n "
                       if awb == 0:
                           rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                       else:
                           rpistr += " -awb " + awbs[awb]
                       if effect > 0:
                           rpistr += " -ifx " + effects[effect]
                       if meter > 0:
                           rpistr += " -mm " + meters[meter]
                       if flicker > 0:
                           rpistr += " -fli " + flickers[flicker]
                       if drc > 0:
                           rpistr += " -drc " + drcs[drc]
                       zwidth = preview_width * (5-zoom)
                       zheight = preview_height * (5-zoom)
                       if zoom == 10:
                           rpistr += " -w " + str(preview_width) + " -h " + str(preview_height)
                       else:
                           rpistr += " -w " + str(zwidth) + " -h " + str(zheight)
                       if zoom > 0 and zoom < 10:
                           zwidth = preview_width * (5-zoom)
                           if zwidth > igw:
                               zwidth = igw - int(igw/20) 
                           zheight = preview_height * (5-zoom)
                           if zheight > igh:
                               zheight = igh - int(igh/20)
                           zxo = ((igw-zwidth)/2)/igw
                           zyo = ((igh-zheight)/2)/igh
                           rpistr += " -roi " + str(zxo) + "," + str(zyo) + "," + str(zwidth/igw) + "," + str(zheight/igh)
                       if zoom == 10:
                           zxo = ((zx -((preview_width/2) / (igw/preview_width)))/preview_width)
                           zyo = ((zy -((preview_height/2) / (igh/preview_height)))/preview_height)
                           rpistr += " -roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                       os.system(rpistr)
                       while not os.path.exists(fname):
                          pass
                       image = pygame.image.load(fname)
                       catSurfacesmall = pygame.transform.scale(image, (preview_width,preview_height))
                       windowSurfaceObj.blit(catSurfacesmall, (0, 0))
                       text(0,0,6,2,1,fname,int(fv*1.5),1)
                       pygame.display.update()
                       tcount +=1
                       while time.monotonic() - tstart < tinterval and tcount < tshots:
                           for event in pygame.event.get():
                               if (event.type == MOUSEBUTTONUP):
                                  mousex, mousey = event.pos
                                  if mousex > preview_width:
                                      e = int((mousex-preview_width)/int(bw/2))
                                      f = int(mousey/bh)
                                      g = (f*4) + e
                                      if g == 30 or g == 31:
                                           tcount = tshots
                   button(1,6,0,2)
                   text(0,0,1,0,1,"CAPTURE",ft,7)
                   text(1,0,1,0,1,"CAPTURE",ft,7)
                   text(1,0,1,1,1,"Video",ft,7)
                   text(0,0,1,1,1,"Still",ft,7)
                   text(1,6,1,0,1,"CAPTURE",ft,7)
                   text(1,6,1,1,1,"Timelapse",ft,7)
                   restart = 2
    if restart > 0:
        if restart == 1:
            os.killpg(p.pid, signal.SIGTERM)
        text(0,0,6,2,1,"Waiting for preview ...",int(fv*1.7),1)
        preview()






                      

