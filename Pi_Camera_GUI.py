#!/usr/bin/env python3
import time
import pygame
from pygame.locals import *
import os, sys
import datetime
import subprocess
import signal

#set displayed image size (must be less than screen size to allow for menu!!)
cwidth  = 640 
cheight = 480 

# set default parameters
mode       = 1       # set camera mode ['off','auto','night'] 
speed      = 100000  # mS x 1000 
ISO        = 0       # 0 = auto or 100,200,400,800 
brightness = 50      # set camera brightness
contrast   = 0       # set camera contrast 
red        = 1.5     # red balance
blue       = 1.2     # blue balance
ev         = 0       # eV correction
vlen       = 10      # in seconds
fps        = 25      # video fps
frame      = 1       # set to 1 for no frame
pic_dir = "/home/pi/Pictures/"
vid_dir = "/home/pi/Videos/"

# NOTE if you change any of the above parameters you need to delete /home/pi/PiCconfig5.txt and restart.

# set button sizes
bw = int(cwidth/8)
bh = int(cheight/12)
ft = int(cwidth/48)
fv = int(cwidth/44)

modes =  ['off','auto','night']

# check PiCconfig.txt exists, if not then write default values
if not os.path.exists('PiCconfig5.txt'):
    points = [mode,speed,ISO,brightness,contrast,frame,int(red*10),int(blue*10),ev,vlen,fps]
    with open('PiCconfig5.txt', 'w') as f:
        for item in points:
            f.write("%s\n" % item)

# read PiCconfig.txt
config = []
with open("PiCconfig5.txt", "r") as file:
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

pygame.init()
if frame == 0:
   windowSurfaceObj = pygame.display.set_mode((cwidth + bw,cheight ), 0, 24)
else:
   windowSurfaceObj = pygame.display.set_mode((cwidth + bw,cheight), pygame.NOFRAME, 24)
pygame.display.set_caption('Pi Camera')

global greyColor, redColor, greenColor, blueColor, dgryColor, lgryColor, blackColor, whiteColor, purpleColor, yellowColor
bredColor =   pygame.Color(255,   0,   0)
lgryColor =   pygame.Color(192, 192, 192)
blackColor =  pygame.Color(  0,   0,   0)
whiteColor =  pygame.Color(200, 200, 200)
greyColor =   pygame.Color(128, 128, 128)
dgryColor =   pygame.Color( 64,  64,  64)
greenColor =  pygame.Color(  0, 255,   0)
purpleColor = pygame.Color(255,   0, 255)
yellowColor = pygame.Color(255, 255,   0)
blueColor =   pygame.Color(  0,   0, 255)
redColor =    pygame.Color(200,   0,   0)

def button(col,row, bColor):
   global cwidth,bw,bh
   colors = [greyColor, dgryColor]
   Color = colors[bColor]
   bx = cwidth + (col * bw)
   by = row * bh
   pygame.draw.rect(windowSurfaceObj,Color,Rect(bx,by,bw-1,bh))
   pygame.draw.line(windowSurfaceObj,whiteColor,(bx,by),(bx+bw,by))
   pygame.draw.line(windowSurfaceObj,greyColor,(bx+bw-1,by),(bx+bw-1,by+bh))
   pygame.draw.line(windowSurfaceObj,whiteColor,(bx,by),(bx,by+bh-1))
   pygame.draw.line(windowSurfaceObj,dgryColor,(bx,by+bh-1),(bx+bw-1,by+bh-1))
   pygame.display.update(bx, by, bw, bh)
   return

def text(row,fColor,top,upd,msg,fsize,bcolor):
   global bh,cwidth,fv
   colors =  [dgryColor, greenColor, yellowColor, redColor, purpleColor, blueColor, whiteColor, greyColor, blackColor, purpleColor]
   Color  =  colors[fColor]
   bColor =  colors[bcolor]
   bx = cwidth
   by = row * bh
   if os.path.exists ('/usr/share/fonts/truetype/freefont/FreeSerif.ttf'): 
       fontObj =       pygame.font.Font('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', int(fsize))
   else:
       fontObj =       pygame.font.Font(None, int(fsize))
   msgSurfaceObj = fontObj.render(msg, False, Color)
   msgRectobj =    msgSurfaceObj.get_rect()
   if top == 0:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+1,by+1,bw-4,int(bh/2)))
       msgRectobj.topleft = (bx + 5, by + 3)
   elif msg == "Still    -  Video":
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+2,by+int(bh/2),int(bw/2),int(bh/2)-1))
       msgRectobj.topleft = (bx+3,  by + int(bh/2))
   elif top == 1:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+29,by+int(bh/2),int(bw/2),int(bh/2)-1))
       msgRectobj.topleft = (bx + 29, by + int(bh/2)-int(bh/20))
   elif top == 2:
       if bcolor == 1:
           pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,0,int(cwidth/2) + 20,fv*2))
       msgRectobj.topleft = (0,row * fsize)
                    
   windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
   if upd == 1 and top == 2:
      pygame.display.update(0,0,int(cwidth/2),fv*2)
   if upd == 1:
      pygame.display.update(bx, by, bw, bh)

def preview():
    global p, brightness,contrast,modes,mode,red,blue,ISO,speed,ev,cwidth,cheight
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
    p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)

for d in range(0,12):
    button(0,d,0)

text(0,1,0,1,"CAPTURE",ft,7)
text(0,1,1,1,"Still    -  Video",ft,7)
text(1,5,0,1,"Mode",ft,7)
text(1,3,1,1,modes[mode],fv,7)
if mode == 0:
    if speed < 1000000:
        text(2,5,0,1,"Shutter mS",ft,7)
        text(2,3,1,1,str(int(speed/1000)),fv,7)
    else:
        text(2,5,0,1,"Shutter S",ft,7)
        text(2,3,1,1,str(int(speed/100000)/10),fv,7)
else:
    if speed < 1000000:
        text(2,5,0,1,"Shutter mS",ft,7)
        text(2,0,1,1,str(int(speed/1000)),fv,7)
    else:
        text(2,5,0,1,"Shutter S",ft,7)
        text(2,0,1,1,str(int(speed/100000)/10),fv,7)
text(3,5,0,1,"ISO",ft,7)
if ISO != 0:
    text(3,3,1,1,str(ISO),fv,7)
else:
    text(3,3,1,1,"Auto",fv,7)
text(4,5,0,1,"Brightness",ft,7)
text(4,3,1,1,str(brightness),fv,7)
text(5,5,0,1,"Contrast",ft,7)
text(5,3,1,1,str(contrast),fv,7)
text(8,5,0,1,"Red",ft,7)
text(8,3,1,1,str(red)[0:3],fv,7)
text(7,5,0,1,"Blue",ft,7)
text(7,3,1,1,str(blue)[0:3],fv,7)
text(6,5,0,1,"eV",ft,7)
if mode != 0:
    text(6,3,1,1,str(ev),fv,7)
else:
    text(6,0,1,1,str(ev),fv,7)
text(9,5,0,1,"V_Length",ft,7)
text(10,5,0,1,"FPS",ft,7)
text(10,3,1,1,str(fps),fv,7)
text(9,3,1,1,str(vlen),fv,7)
text(11,2,0,1,"EXIT",fv,7)

text(0,6,2,1,"Please Wait, checking camera",fv* 1.7,1)
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
   if image.get_width() == 2592:
      Pi_Cam = 1
      max_speed = 6000000
   elif image.get_width() == 3280:
      Pi_Cam = 2
      max_speed = 10000000
   else:
      Pi_Cam = 3
      max_speed = 239000000
else:
   Pi_Cam = 0
   max_speed = 6000000
if Pi_Cam > 0:
    text(0,6,2,1,"Found Pi Camera v" + str(Pi_Cam),fv* 2,1)
else:
    text(0,6,2,1,"No Pi Camera found",fv* 2,1)

pygame.display.update()
time.sleep(1)
text(0,6,2,1,"Please Wait for preview...",fv* 2,1)

# start preview
preview()

while True:
    if os.path.exists('/run/shm/test.jpg'):
        image = pygame.image.load('/run/shm/test.jpg')
        os.rename('/run/shm/test.jpg', '/run/shm/oldtest.jpg')
        windowSurfaceObj.blit(image, (0, 0))
        text(0,6,2,0,"Preview",fv* 2,0)
        pygame.display.update()
    buttonx = pygame.mouse.get_pressed()
    if buttonx[0] != 0 :
        os.killpg(p.pid, signal.SIGTERM)
        time.sleep(0.1)
        pos = pygame.mouse.get_pos()
        mousex = pos[0]
        mousey = pos[1]
        if mousex > cwidth:
            x = int((mousex-cwidth)/int(bw/2))
            y = int((mousey)/bh)
            g = (y*2) + x
            if g == 5 :
                if mode == 0:
                    show = 0
                    if speed > 5000000:
                        speed +=1000000
                    elif speed > 1000000:
                        speed +=100000
                    elif speed > 100000:
                        speed +=10000
                    else:
                        speed +=1000
                    speed = min(speed,max_speed)
                    if speed < 1000000:
                        text(2,5,0,1,"Shutter mS",ft,7)
                        text(2,3,1,1,str(int(speed/1000)),fv,7)
                    else:
                        text(2,5,0,1,"Shutter S",ft,7)
                        text(2,3,1,1,str(int(speed/100000)/10),fv,7)

            elif g == 4 :
                if mode == 0:
                    if speed > 5000000:
                        speed -=1000000
                    elif speed > 1000000:
                        speed -=100000
                    elif speed > 100000:
                        speed -=10000
                    else:
                        speed -=1000
                    speed = max(speed,1000)
                    if speed < 1000000:
                        text(2,5,0,1,"Shutter mS",ft,7)
                        text(2,3,1,1,str(int(speed/1000)),fv,7)
                    else:
                        text(2,5,0,1,"Shutter S",ft,7)
                        text(2,3,1,1,str(int(speed/100000)/10),fv,7)

            elif g == 9 :
                brightness +=1
                brightness = min(brightness,100)
                text(4,3,1,1,str(brightness),fv,7)
            elif g == 8 :
                brightness -=1
                brightness = max(brightness,0)
                text(4,3,1,1,str(brightness),fv,7)
            elif g == 11:
                contrast +=1
                contrast = min(contrast,100)
                text(5,3,1,1,str(contrast),fv,7)
            elif g == 10 :
                contrast -=1
                contrast = max(contrast,-100)
                text(5,3,1,1,str(contrast),fv,7)
            elif g == 13 and mode != 0:
                ev +=1
                ev = min(ev,12)
                text(6,3,1,1,str(ev),fv,7)
            elif g == 12 and mode != 0:
                ev -=1
                ev = max(ev,-12)
                text(6,3,1,1,str(ev),fv,7)
            elif g == 19 :
                vlen +=1
                vlen = min(vlen,300)
                text(9,3,1,1,str(vlen),fv,7)
            elif g == 18 :
                vlen -=1
                vlen = max(vlen,0)
                text(9,3,1,1,str(vlen),fv,7)
        preview()

    #check for any mouse button presses
    for event in pygame.event.get():
       if event.type == QUIT:
           pygame.quit()

       elif (event.type == MOUSEBUTTONUP):
           os.killpg(p.pid, signal.SIGTERM)
           mousex, mousey = event.pos
           if mousex > cwidth:
               e = int((mousex-cwidth)/int(bw/2))
               f = int(mousey/bh)
               g = (f*2) + e

               if g == 22 or g ==23:
                   pygame.display.quit()
                   sys.exit()

               elif g == 7 :
                   if ISO == 0:
                       ISO +=100
                   else:
                       ISO = ISO * 2
                   ISO = min(ISO,800)
                   if ISO != 0:
                       text(3,3,1,1,str(ISO),fv,7)
                   else:
                       text(3,3,1,1,"Auto",fv,7)
               elif g ==6 :
                   if ISO == 100:
                       ISO -=100
                   else:
                       ISO = int(ISO / 2)
                   ISO = max(ISO,0)
                   if ISO != 0:
                       text(3,3,1,1,str(ISO),fv,7)
                   else:
                       text(3,3,1,1,"Auto",fv,7)        
               elif g == 3 :
                   mode +=1
                   mode = min(mode,2)
                   if mode != 0:
                       text(6,3,1,1,str(ev),fv,7)
                   else:
                       text(6,0,1,1,str(ev),fv,7)
                   if mode == 0:
                       if speed < 1000000:
                           text(2,5,0,1,"Shutter mS",ft,7)
                           text(2,3,1,1,str(int(speed/1000)),fv,7)
                       else:
                           text(2,5,0,1,"Shutter S",ft,7)
                           text(2,3,1,1,str(int(speed/100000)/10),fv,7)
                   else:
                       if speed < 1000000:
                           text(2,5,0,1,"Shutter mS",ft,7)
                           text(2,0,1,1,str(int(speed/1000)),fv,7)
                       else:
                           text(2,5,0,1,"Shutter S",ft,7)
                           text(2,0,1,1,str(int(speed/100000)/10),fv,7)
                   text(1,3,1,1,modes[mode],fv,7)
                   
               elif g == 2 :
                   mode -=1
                   mode = max(mode,0)
                   if mode != 0:
                       text(6,3,1,1,str(ev),fv,7)
                   else:
                       text(6,0,1,1,str(ev),fv,7)
                   if mode == 0:
                       if speed < 1000000:
                           text(2,5,0,1,"Shutter mS",ft,7)
                           text(2,3,1,1,str(int(speed/1000)),fv,7)
                       else:
                           text(2,5,0,1,"Shutter S",ft,7)
                           text(2,3,1,1,str(int(speed/100000)/10),fv,7)
                   else:
                       if speed < 1000000:
                           text(2,5,0,1,"Shutter mS",ft,7)
                           text(2,0,1,1,str(int(speed/1000)),fv,7)
                       else:
                           text(2,5,0,1,"Shutter S",ft,7)
                           text(2,0,1,1,str(int(speed/100000)/10),fv,7)
                   text(1,3,1,1,modes[mode],fv,7)

               elif g == 0:
                   button(0,0,1)
                   text(0,2,0,1,"CAPTURE",ft,0)
                   text(0,6,2,1,"Please Wait, taking still ...",fv* 2,1)
                   now = datetime.datetime.now()
                   timestamp = now.strftime("%y%m%d%H%M%S")
                   fname =  pic_dir + str(timestamp) + '.jpg'
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
                       rpistr = "raspistill -t 10 -md 3 -bm -ex off -ag 1 -ss " + str(speed) + " -st -o " + fname
                       rpistr += " -co " + str(contrast) + " -br " + str(brightness)
                       rpistr += " -awb off -awbg " + str(red) + "," + str(blue)
                   rpistr += " -n "
                   os.system(rpistr)
                   while not os.path.exists(fname):
                       pass
                   image = pygame.image.load(fname)
                   catSurfacesmall = pygame.transform.scale(image, (cwidth,cheight))
                   windowSurfaceObj.blit(catSurfacesmall, (0, 0))
                   text(0,6,2,1,fname,int(fv*1.5),1)
                   pygame.display.update()
                   time.sleep(2)
                   button(0,0,0)
                   text(0,1,0,1,"CAPTURE",ft,7)
                   text(0,1,1,1,"Still    -  Video",ft,7)
                   text(0,6,2,1,"Waiting for preview ...",fv* 2,1)
                                     
               elif g == 1:
                   button(0,0,1)
                   text(0,2,0,1,"CAPTURE",ft,0)
                   text(0,6,2,1,"Please Wait, taking video ...",fv* 2,1)
                   now = datetime.datetime.now()
                   timestamp = now.strftime("%y%m%d%H%M%S")
                   vname =  vid_dir + str(timestamp) + '.h264'
                   rpistr = "raspivid -t " + str(vlen * 1000) + " -w 1440 -h 1080"
                   rpistr += " -p 0,0," + str(cwidth) + "," + str(cheight) + " -fps " + str(fps) + " -o " + vname + " -co " + str(contrast) + " -br " + str(brightness)
                   rpistr += " -awb off -awbg " + str(red) + "," + str(blue) +  " -ISO " + str(ISO) + " -a 12 -a '%Y-%m-%d %Z%z %p:%X' -ae 32,0x8080ff" 
                   speed2 = speed
                   if speed2 > 1/fps:
                       speed2 = 1/(fps *2)
                   if mode == 0:
                       rpistr +=" -ex off -ss " + str(speed2)
                   else:
                       rpistr +=" -ex " + str(modes[mode]) + " -ev " + str(ev)
                   os.system(rpistr)
                   text(0,6,2,1,vname,int(fv*1.5),1)
                   time.sleep(1)
                   button(0,0,0)
                   text(0,1,0,1,"CAPTURE",ft,7)
                   text(0,1,1,1,"Still    -  Video",ft,7)
                   text(0,6,2,1,"Waiting for preview ...",fv* 2,1)

               elif g == 21 :
                   fps +=1
                   fps = min(fps,40)
                   text(10,3,1,1,str(fps),fv,7)
               elif g == 20 :
                   fps -=1
                   fps = max(fps,1)
                   text(10,3,1,1,str(fps),fv,7)
               elif g == 16 :
                   red -=0.1
                   red = max(red,0.1)
                   text(8,3,1,1,str(red)[0:3],fv,7)
               elif g == 17 :
                   show = 0
                   red +=0.1
                   red = min(red,8)
                   text(8,3,1,1,str(red)[0:3],fv,7)
               elif g == 14 :
                   blue -=0.1
                   blue = max(blue,0.1)
                   text(7,3,1,1,str(blue)[0:3],fv,7)
               elif g == 15 :
                   blue +=0.1
                   blue = min(blue,8)
                   text(7,3,1,1,str(blue)[0:3],fv,7) 

        
           # save config
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
           with open('PiCconfig5.txt', 'w') as f:
               for item in config:
                   f.write("%s\n" % item)
           preview()





                      

