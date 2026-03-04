import sys, argparse
from PIL import Image

def decode(img,scale=None):
    res = img.size
    if scale!=None:
        img=img.resize((res[0]//scale,res[1]//scale))
    img=img.convert("RGB")
    octal=""
    output=b""
    reachedEnd=False
    def processPixel(x,y):
        nonlocal octal,output,reachedEnd
        if reachedEnd: return
        c=img.getpixel((x,y))
        n=(c[0]>127)+(c[1]>127)*2+(c[2]>127)*4
        octal=octal+str(n)
        octnum=None
        if len(octal)==3:
            octnum=int(octal,8)
            octal=""
            if octnum==0o777:
                reachedEnd=True
                return
            if octnum>255:
                print(f"WARNING: got byte outside of 0-255 range ({oct(octnum)}), skipping")
                return
            output=output+bytes([octnum])

    w=img.width
    h=img.height
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

    return output

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description="decodes contents from an Acorn code.",epilog="WARNING: this program does not verify alignment patterns for rotation or transformation. please use this with a clean image if possible.")
    parser.add_argument("input",type=str,help="input image")
    parser.add_argument("output",type=str,help="output file, can be text or binary")
    parser.add_argument("-s","--scale",type=int,help="scaling factor if the input image has integer scaling (e.g. if a pixel is 3x3, use '-s 3')")
    args=parser.parse_args()

    img = Image.open(args.input)

    output = decode(img,args.scale)

    with open(args.output,"wb") as file:
        file.write(output)
