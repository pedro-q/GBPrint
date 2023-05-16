import sys
import argparse
import serial
import time
from PIL import Image
from math import ceil, sqrt

''' This is just my reminder of which cable color is which
Brown - 4 - SOUT
Blue - 3 - SCK (clock)
Green - 2 -SIN
Red - 6 - GROUND
'''

# Commands structures
INITCMD    = [b'\x88', b'3', b'\x01', b'\x00', b'\x00', b'\x00', b'\x01', b'\x00', b'\x00', b'\x00']
EMPTYCMD   = [b'\x88', b'3', b'\x04', b'\x00', b'\x00', b'\x00', b'\x04', b'\x00', b'\x00', b'\x00']
PRINTCMD   = [b'\x88', b'\x33', b'\x02', b'\x00', b'\x04', b'\x00', b'\x01', b'\x00', b'\xe4', b'\x7f', b'\x6a', b'\x01', b'\x00', b'\x00']
REPORTCMD  = [b'\x88', b'3', b'\x0f', b'\x00', b'\x00', b'\x00', b'\x0f', b'\x00', b'\x00', b'\x00']
DATAPREFIX = [b'\x88', b'3', b'\x04', b'\x00', b'\x80', b'\x02']

def lum (r,g,b):
    # Maybe sorting by luminosity is overkill
    return sqrt( .241 * r + .691 * g + .068 * b ) 

def convert_image(file):
    """
    Convert an image in the GB Printer 8x8 tile format
    
        Params:
            file (str): Route to an image file
            
        Returns:
            tile_rows (list[x][640]): The bytes representation of the image
    """
    im = Image.open(file)
    width, height = im.size
    mode = im.mode

    if width > 160:
        raise ValueError("Image needs to be 160px wide")
        
    if height % 16 != 0:
        raise ValueError("Image height needs to be a multiple of 16")

    if mode not in ["P", "RGB", "RGBA", "L", "1"]:
        raise ValueError("Image needs to be RGB, grayscale or indexed")
    
    if mode != "RGB":
        im = im.convert('RGB')

    num_colors = im.getcolors()

    if len(num_colors) > 4:
        raise ValueError("Image can't have more than 4 colors")

    num_colors.sort(key=lambda rgb: lum(*rgb[1])) 
    
    hor_tile = width // 8
    vert_tile = height // 8
    total_tiles = hor_tile * vert_tile
    tile_rows = [[0 for i in range(0, 640)] for x in range(0, (height // 16))]
    for row in range(0, vert_tile):
        for col in range(0, hor_tile):
            for y in range(0, 8):
                lsb = 0
                msb = 0
                for x in range(0, 8): 
                    py = (row * 8) + y
                    px = (col * 8) + x
                    pixel = im.getpixel((px, py))
                    lowhigh = (0, 0) #white
                    if pixel == num_colors[0][1]: #black
                        lowhigh = (1,1)
                    elif pixel == num_colors[1][1]: # dark gray
                        lowhigh = (0,1)
                    elif pixel == num_colors[2][1]: # light gray
                        lowhigh = (1,0)
                    lsb = lsb | (lowhigh[0] << (7-x))
                    msb = msb | (lowhigh[1] << (7-x)) 
                i = (row % 2) * 320 + col*16 + y*2
                i1 = i + 1
                j = row // 2
                tile_rows[j][i] = bytes.fromhex(hex(lsb)[2:].zfill(2))
                tile_rows[j][i1] = bytes.fromhex(hex(msb)[2:].zfill(2))
    k = ceil(len(tile_rows)/9)
    if k > 1:
        raise NotImplementedError("Sorry multiple images aren't supported right now :(")
    return tile_rows

def make_data(img):
    """
    Converts the image data to GB Printer DATA packet format.
    
        Params:
            img (list[x][640]): An image chunked into the GB Printer tiles format
        
        Returns:
            data_packets (list): A list with multiple DATA packets
    """

    ''' Checksum head is packet command + lenght of data
     In DATA case: length of data is always 640 (or 80 02 in hex)
    '''
    data_packets = []
    checksum_head = DATAPREFIX[2][0] + DATAPREFIX[4][0] + DATAPREFIX[5][0]
    checksum = checksum_head 
    for i in img: # Get packets to print one by one
        data_packet = []
        data_packet.extend(DATAPREFIX)
        checksum = checksum_head 
        for x in i: # Get bytes in packet one by one
            data_packet.append(x)
            checksum = checksum + x[0] # We add the int value to the checksum 
        data_packet.append((checksum & 255).to_bytes(1, byteorder='little')) # Extract checksum bytes
        data_packet.append(((checksum & 65280) >> 8).to_bytes(1, byteorder='little')) # Extract checksum bytes
        data_packet.append(b"\x00") # Response byte
        data_packet.append(b"\x00") # Response byte
        data_packets.append(data_packet)
    return data_packets

def write_data(data, ser):
    """
    Writes a command to the GB Printer
    
       Params:
           data (list): formatted packet to send
           ser (??): the serial connection
           
       Returns:
           res (list): printer response, only the last two bytes are the response code
    """
    res = []
    for cmd in data:
        ser.write(cmd)
        ser.flush()
        res.append(ser.read())
    return res

def print_data(data_packets):
    """
    Sends data to be printed to the Game Boy Printer
    
        Params:
            data_packets (list): A list with multiple data packets
    """
    ser = serial.Serial('COM5',9600, timeout=120, dsrdtr=False)
    time.sleep(2)
    print(ser.readline())
    time.sleep(2)
    
    # SEND INIT
    print("Sending init")
    res = write_data(INITCMD, ser)
    print(res[-2:], "init response")

    # SEND DATA
    print("Send data")
    for dpk in data_packets: # we can only send 9 DATA packets until buffer's full
        res = write_data(dpk, ser)
        print(res[-2:], "data response")

    # SEND EMPTY DATA
    print("Send empty data")
    res = write_data(EMPTYCMD, ser)
    print(res[-2:], "empty data response")
    
    # SEND PRINT
    print("Send print")
    res = write_data(PRINTCMD, ser)
    print(res[-2:], "print response")

    # SEND REPORT
    print("Send report")
    for i in range(10):
        res = write_data(REPORTCMD, ser)
        print(res[-2:], "report " + str(i)+ " response")
        time.sleep(1.1)
    ser.close()

def dump_to_bin(imagebin, fileout):
    """
    Dumps the converted image to a file
    
        Parameters:
            imagebin (list[x][640]): The image in 8x8 GB Printer format
            fileout (str): The name of the output file  
    """
    newFile = open(fileout, "wb")
    for y in imagebin:
        for x in y:
            newFile.write(x)

def main(argv):

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("-i",'--image', help='image file name', required=True)
    parser.add_argument("-d",'--dump', help='dumps image to bin file', action=argparse.BooleanOptionalAction)
    parser.add_argument("-o",'--out', help='out file for dump (default dump.bin)', default="dump.bin")

    args = parser.parse_args()

    banner = convert_image(args.image)

    if(args.dump):
        dump_to_bin(banner, args.out)
    else:
        data_packets = make_data(banner)
        print_data(data_packets)

if __name__ == "__main__":
    main(sys.argv)