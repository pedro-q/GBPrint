# GB Print

Simple command line interface for sending images to a Game Boy Printer

## Description

This command line written in python can be used to convert 4 color images to the Game Boy Printer format and send them through a serial line to the Game Boy Printer

## Getting Started

### Dependencies

* Requires PIL / Pillow to convert images
* Requires pyserial to send images through the serial connection
* A four color image (RGB, 2-bit, 1-bit or Indexed)
* For sending and printing images you will need an Arduino, a Game Boy Printer surely and [follow some instructions below](#send-to-game-boy-printer)

### Installing

1. Create a new virtual environment
```
python3 -m venv venv
```
2. Activate your virtual environment
3. Install the requirements
```
pip install -r requirements.txt
```

### Executing program

* After activating your virtual env and installing requirements, you can run the executable with:
```
python gbprint.py --image <yourimagefile.png>
```
There is a dump option that will output a binary file to test or to use anywhere else if that is more convenient.

## Send to Game Boy Printer
This script assumes your Arduino is connected on COM5 and serial is configured to 9600 baud rate.

You will need a stripped game link cable connected to a Arduino flashed with the correct code to send images to the printer, I have used this code with success: https://github.com/Raphael-Boichot/The-Arduino-SD-Game-Boy-Printer/tree/master/Research/Serial_Pocket_Printer_interface

You can also follow the instructions of that repository in the pinout section (https://github.com/Raphael-Boichot/The-Arduino-SD-Game-Boy-Printer/blob/master/README.md#the-pinout) to connect your game boy printer to an Arduino, I do recommend that you have a multimeter handy to test your cable pairs and verify that everything is connected correctly to the Arduino.

## Help

You can use
```
python gbprint.py --help
```
to get the help screen of the command.

## Version History

* 0.1
    * Initial Release

## TODO
* **Print larger images** Just now only 160 x 144px images are supported because it's what the buffer can handle but there are ways to print larger images.
* **Interpret error codes** I just blast the commands to the printer without worring for errors, doesn't seem that bad for the printer but the user is completely clueless of what happened if something failed.

## Acknowledgments

* [A simple PC to Game Boy Printer interface with an Arduino](https://github.com/Raphael-Boichot/PC-to-Game-Boy-Printer-interface) Great resource, got all the protocol information and the printer codes from this repository
* [GBPrinter](https://github.com/octavifs/GBPrinter) I got the idea for this script from this repo as I at first tried to use this tool to print some images but sadly the code was outdated.
* [Printing on the Game Boy Printer using an STM32F4](https://dhole.github.io/post/gameboy_serial_3/) This was really helpful to learn how to parse the image into the really specific Game Boy tiles as I found out that the Arduino SD code was a little hard to understand.
