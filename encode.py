import sys, math, argparse
from PIL import Image

parser=argparse.ArgumentParser(description="encodes a file into an Acorn code.")
parser.add_argument("input",type=str,help="input file, can be text or binary")
parser.add_argument("output",type=str,help="output image")
parser.add_argument("-s","--scale",type=int,help="scale the resulting image by an integer")
parser.add_argument("-r","--ratio",type=int,nargs=2,help="use a specific aspect ratio")
parser.add_argument("-W","--width",type=int,help="use a specific width")
parser.add_argument("-H","--height",type=int,help="use a specific height")
parser.add_argument("-u","--reserve-unused",type=float,help="percentage to reserve for unused data, helpful for inserting images (e.g. 50 will use 1/4 of space, 100 will use 1/2 of space)")
parser.add_argument("-U","--transparent-unused",action='store_true',help="make unused space completely transparent on the final image, helpful for inserting images (make sure the output file format supports transparency!!)")
args=parser.parse_args()

content=None
with open(args.input,"rb") as file:
    content=file.read()

datasize=(len(content)+3)*3 # number of pixels that will be taken. i have no idea why i put +3, but that's here in case it doesn't make the EOF when it's +1

# get output resolution
height = 19
if args.height!=None:
    height = max(args.height,10)
    # naming x the known data size, y the size of the middle part we want to get, and z the height
    # 2(z-9) + 1(z-5) + y(z-4) + 3(z-6) + 1(z-9) = x
    # 2z-18 + z-5 + yz-4y + 3z-36 + z-9 = x
    # yz + -4y + 2z+z+3z+z + -18-5-36-9 = x
    # yz - 4y + 7z - 68 = x
    # yz - 4y + 7z = x+68
    # y(z-4) = x+68-7z
    # y = (x+68-7z)/(z-4)
    # y+7 (data width) = (x+68-7z)/(z-4)+7
    dw=(datasize+68-7*height)/(height-4)+7
    width=max(math.ceil(dw+4),11)
elif args.width!=None:
    width = max(args.width,11)
    # naming x the total data size, y the width of the middle part and z the total data height. we want to solve for z:
    # 2(z-9) + 1(z-5) + y(z-4) + 3(z-6) + 1(z-9) = x
    # 2z-18 + z-5 + yz-4 + 3z-36 + z-9 = x
    # (2z+z+3z+z) + (-18-5-4-36-9) + yz = x
    # 7z + -72 + yz = x
    # z(7+y) = x+72
    # z = (x+72)/(7+y)
    mw = width-7-4
    dh=(datasize+72)/(7+mw)
    height=max(math.ceil(dh+4),10)
else:
    rawheight = math.sqrt(22+datasize)+4 # this was figured out by my friend WahPlus. i don't want to figure out how this works.
    rawwidth = rawheight
    if args.ratio!=None:
        ratio = args.ratio[0]/args.ratio[1]
        # using the square root here, because doing it without the square root would apply the ratio squared instead of the actual ratio
        rawwidth*=math.sqrt(ratio)
        rawheight/=math.sqrt(ratio)
    if args.reserve_unused!=None:
        rpx=args.reserve_unused/100
        mult=1+rpx
        rawwidth*=math.sqrt(mult)
        rawheight*=math.sqrt(mult)
    height = max(math.ceil(rawheight),10)
    width = max(math.ceil(rawwidth),11) # minimum is 11 for the decoder to work

img=Image.new("RGBA",(width,height),(0,0,0,255))
def hline(x,y,s,c):
    c=tuple(list(c)+[255])
    for i in range(x,x+s):
        img.putpixel((i,y),c)
def vline(x,y,s,c):
    c=tuple(list(c)+[255])
    for i in range(y,y+s):
        img.putpixel((x,i),c)
def hlinep(x,y,s,c1,c2):
    c1=tuple(list(c1)+[255])
    c2=tuple(list(c2)+[255])
    for i in range(x,x+s):
        img.putpixel((i,y),[c1,c2][i%2])
def vlinep(x,y,s,c1,c2):
    c1=tuple(list(c1)+[255])
    c2=tuple(list(c2)+[255])
    for i in range(y,y+s):
        img.putpixel((x,i),[c1,c2][i%2])
def square(x,y,c):
    img.putpixel((x,y),c)
    img.putpixel((x+1,y),c)
    img.putpixel((x,y+1),c)
    img.putpixel((x+1,y+1),c)

# sync borders
hlinep(0,0,width,(255,255,0),(255,0,0))
hline(0,1,width,(0,0,0))

hlinep(0,height-1,width,(0,0,255),(0,255,255))
hline(0,height-2,width,(0,0,0))

vlinep(0,0,height,(0,0,0),(255,255,255))
vline(1,0,height,(0,0,0))

vlinep(width-1,0,height,(255,0,255),(0,255,0))
vline(width-2,0,height,(0,0,0))

square(0,0,(0,0,0))
square(2,0,(255,0,0))
vline(4,0,3,(255,255,255))
hline(0,2,4,(255,255,255))
# extra border
hline(1,3,5,(0,0,0))
vline(5,1,3,(0,0,0))

square(width-4,0,(255,255,0))
square(width-2,0,(0,255,0))
vline(width-5,0,3,(0,0,0))
hline(width-4,2,4,(0,0,0))

square(0,height-4,(255,255,255))
square(0,height-2,(0,255,255))
hline(0,height-5,3,(0,0,0))
vline(2,height-4,4,(0,0,0))

square(width-2,height-4,(255,0,255))
square(width-2,height-2,(0,0,255))
hline(width-3,height-5,3,(255,255,255))
vline(width-3,height-4,4,(255,255,255))

# encoding data
octal=""
idx=0
eof=False
def processPixel(x,y):
    global octal,idx,eof
    if len(octal)==0:
        if idx==len(content):
            octal="777"
        elif idx>len(content):
            octal="770"
        else:
            octal=format(content[idx],"03o")
            if len(content)>10000 and idx%2048==0: # if file is more than 10KB
                print(f"\r\x1b[2K{round(idx/len(content)*100)}% ({idx}/{len(content)})",end="")
        idx+=1
    if idx>len(content)+1 and args.transparent_unused:
        img.putpixel((x,y),(0,0,0,0))
        return
    n=int(octal[0])
    octal=octal[1:]
    c=(int(n&1==1)*255,int(n&2==2)*255,int(n&4==4)*255)
    img.putpixel((x,y),c)
    if len(octal)==0 and idx==len(content):
        eof=True

w=width
h=height
for x in range(w-3,w-5,-1):
    for y in range(3,h-6):
        processPixel(x,y)
for y in range(3,h-2):
    processPixel(w-5,y)
for x in range(w-6,5,-1):
    for y in range(2,h-2):
        processPixel(x,y)
for x in range(5,2,-1):
    for y in range(4,h-2):
        processPixel(x,y)
for y in range(4,h-5):
    processPixel(2,y)
print("\r\x1b[2K",end="")

if not eof:
    print("WARNING: The EOF marker could not be written, or has been cut off. The generated Acorn code may be invalid.")

if args.scale!=None:
    img=img.resize((w*args.scale,h*args.scale),Image.NEAREST)

try:
    img.save(args.output)
except OSError:
    # most likely "OSError: cannot write mode RGBA as JPEG"
    img=img.convert("RGB")
    img.save(args.output)
