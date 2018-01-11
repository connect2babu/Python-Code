import serial
import time
import subprocess
from robot.api import logger # print to terminal with logger.console(message)

class CountDownTimer:
    'Common base class for all countdown timers'

    def __init__(self, seconds):
        self.initTime = seconds
        self.startTime = time.time()
        self.remainingTime = 0
        self.expired = False

    def timerRemaining(self):
        self.remainingTime = self.initTime - (time.time() - self.startTime)
        print("timerExpired = %d" %self.remainingTime )
        return self.remainingTime

    def timerExpired(self):
        if self.initTime < (time.time() - self.startTime):
            self.expired = True
        return self.expired

    def timerReset(self):
        self.expired = False
        self.remainingTime = 0

#def open_serial(dev, ser):
def open_serial(dev):    
    # Variables
    #portname = "/dev/tty.usbserial-DN01ZHLE"

    # Constants
    SERIAL_TIMEOUT_SECONDS = 5

    # Setup com port
    ser = serial.Serial()
    ser.port = dev
    ser.baudrate = 115200
    ser.bytesize = serial.EIGHTBITS    #number of bits per bytes
    ser.parity = serial.PARITY_NONE    #set parity check: no parity
    ser.stopbits = serial.STOPBITS_ONE #number of stop bits
    ser.timeout = 0                    # seconds for timeout, 0 = non blocking read
    ser.xonxoff = False                #disable software flow control
    ser.rtscts = False                 #disable hardware (RTS/CTS) flow control
    ser.dsrdtr = False                 #disable hardware (DSR/DTR) flow control
    ser.writeTimeout = 2
    #inter_byte_timeout = 1             #in tenths of a second (0.1 = 10ms)

    # Open com port
    ser.open()
    ser.flushInput() #flush input buffer, discarding all its contents
    ser.flushOutput()#flush output buffer, aborting current output

    return ser

def close_serial(ser):
    ser.close()

def test_fw_version(ser, expected, identifier):
    """
    Tests the firmware version string of the device on the given open comport
    """
    ser.flushInput()
    ser.flushOutput()
    #ser.write("version\n".encode('utf-8'))
    command = "version\n"
    send_command(ser, command)
    text_file = open("debugoutput.txt", 'w')

    # read in until we find the identifier, then stop reading
    message = ""
    stop_identifier = identifier
    while stop_identifier not in message:
        message += ser.read(1).decode('utf-8')
    stop_identifier = "\r\n"
    text_file.write(message)

    actual = ""
    while stop_identifier not in actual:
        actual += ser.read(1).decode('utf-8')
    actual = actual.strip()
    text_file.write(actual)
    time.sleep(.25)

    text_file.close()

    if expected != actual:
        raise AssertionError("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))
    else:
        logger.info("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))

    return

def test_reset(ser, expected):
    """
    Tests the reset command
    """
    ser.flushInput()
    ser.flushOutput()
    ser.write("reset\n".encode('utf-8'))
    time.sleep(.25)

    # read in until we find the identifier, then stop reading
    message = ""
    stop_identifier = "\r\n"
    while stop_identifier not in message:
        message += ser.read(1).decode('utf-8')

    stop_identifier = expected
    actual = ""
    while stop_identifier not in actual:
        actual += ser.read(1).decode('utf-8')
    actual = actual.strip()
    time.sleep(.25)

    if expected != actual:
        raise AssertionError("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))
    else:
        logger.info("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))

    return

def test_shutdown(ser, relayser, relay):
    """
    Tests the shutdown command
    """
    ser.flushInput()
    ser.flushOutput()
    #ser.write("shutdown\r\n".encode('utf-8'))
    command = "shutdown\r\n"
    send_command(ser, command)

    # read in until we find the identifier, then stop reading
    message = ""
    stop_identifier = "shutdown\r\n"
    while stop_identifier not in message:
        message += ser.read(1).decode('utf-8')

    expected = "System will power off after USB is disconnected"
    stop_identifier = expected
    actual = ""
    while stop_identifier not in actual:
        actual += ser.read(1).decode('utf-8')
    actual = actual.strip()
    time.sleep(.5)

    # reset device
    set_relay(relayser, relay, "on")
    time.sleep(3)
    set_relay(relayser, relay, "off")

    if expected != actual:
        raise AssertionError("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))
    else:
        logger.info("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))

    return

def test_usb_reset(ser, expected, relayser, relay, power):
    """
    Tests reset on USB insertion
    """
    ser.flushInput()
    ser.flushOutput()
    set_relay(relayser, relay, power)

    # read in until we find the identifier, then stop reading
    message = ""
    stop_identifier = "Power off touchpad\r\n"
    while stop_identifier not in message:
        message += ser.read(1).decode('utf-8')

    stop_identifier = expected
    actual = ""
    while stop_identifier not in actual:
        actual += ser.read(1).decode('utf-8')
    actual = actual.strip()

    set_relay(relayser, relay, "off")
    time.sleep(3)

    if expected != actual:
        raise AssertionError("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))
    else:
        logger.info("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))

    return

def test_gesture(ser, gesture, expected):
    """
    Tests when gesture sent to mobile app is acknowledged with a notification
    """
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    text_file = open("debugoutput.txt", 'a')
    #ser.write(("send gesture " + str(gesture) + "\n").encode('utf-8'))

    command = ("send gesture " + gesture)
    send_command(ser, command)
    time.sleep(.25)

    # read in until we find the identifier, then stop reading
    message = ""
    #stop_identifier = "Pattern "
    stop_identifier = "[NOTIFICATION]: "
    timer = CountDownTimer(5)
    while ( (stop_identifier not in message) and (timer.timerExpired() == False) ):
        message += ser.read(1).decode('utf-8')
    del timer

    # if stop_identifier not in message:
    #     raise AssertionError("Expected stop identifier: '%s' Actual vaule: '%s'."
    #                              % (stop_identifier, message))

    # read in until we find the identifier, then stop reading
    timer = CountDownTimer(5)
    #actual = stop_identifier
    actual = ""
    stop_identifier = expected
    while ( (stop_identifier not in actual) and (timer.timerExpired() == False) ):
        actual += ser.read(1).decode('utf-8')
    text_file.write(actual)
    actual = actual.strip()
    time.sleep(.25)

    text_file.close()

    if expected != actual:
        raise AssertionError("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))
    else:
        logger.info("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))

    del timer
    return

def set_battery_sim(ser):
    #set_battery_sim(addr, ch, volt, curr, limit, out):
    """
    Setup the Keithley 2306/2281S Battery Simulator on Channel 1
    """
    ser.flushInput()
    ser.flushOutput()

    # Set GPIB to write to
    ser.write("++addr 16\n".encode('utf-8'))
    time.sleep(.10)

    # Set active channel
    ser.write("DISP:CHAN 1\n".encode('utf-8'))
    time.sleep(.10)

    # Set voltage
    ser.write("SOUR1:VOLT 4.00\n".encode('utf-8'))
    time.sleep(.10)

    # Enable auto range for current
    ser.write("SENS1:CURR:RANG:AUTO ON\n".encode('utf-8'))
    time.sleep(.10)

    # Set current limit
    ser.write("SOUR1:CURR 250e-3\n".encode('utf-8'))
    time.sleep(.10)

    # Select trip mode for current limit
    ser.write("SOUR1:CURR:TYPE TRIP\n".encode('utf-8'))
    time.sleep(.10)

    # Select the voltage measurement function
    ser.write("SENS1:FUNC 'VOLT'\n".encode('utf-8'))
    time.sleep(.10)

    # Set integration rate to 2 PLC
    ser.write("SENS1:NPLC 2\n".encode('utf-8'))
    time.sleep(.10)

    # Set average reading count
    ser.write("SENS1:AVER 5\n".encode('utf-8'))
    time.sleep(.10)

    # Turn on the power supply output
    ser.write("OUTP1 ON\n".encode('utf-8'))
    time.sleep(.10)

    return

def test_bat_state(ser, expected):
    """
    Tests the battery level in the command console

    """
    expected = expected + ")"
    #send "set battery 5 secs" command
    command = ("set battery 5")
    send_command(ser, command)


    time.sleep(120)
    #timer = CountDownTimer(60)
    text_file = open("debugoutput.txt", 'a')

    # while ( (actual != expected) and (timer.timerExpired() == False) ):
    # #while ( (actual != expected) ):
    #     # read in until we find the identifier, then stop reading
    #     ser.flushInput()
    #     message = ""
    #     stop_identifier = "Battery measurement "
    #     while stop_identifier not in message:
    #         message += ser.read(1).decode('utf-8')
    #     text_file.write(message)

    #     stop_identifier = expected
    #     actual = ""
    #     while stop_identifier not in actual:
    #         actual += ser.read(1).decode('utf-8')
    #     actual = actual.strip()
    #     time.sleep(.25)
    #     text_file.write(actual)

    #send "battery" command
    command = ("battery")
    send_command(ser, command)

    # read in until we find the identifier, then stop reading
    ser.flushInput()
    message = ""
    stop_identifier = "Battery percent: "
    while stop_identifier not in message:
        message += ser.read(1).decode('utf-8')
    text_file.write(message)
    
    stop_identifier = " ("
    while stop_identifier not in message:
        message += ser.read(1).decode('utf-8')
    text_file.write(message)

    stop_identifier = expected
    actual = ""
    while stop_identifier not in actual:
        actual += ser.read(1).decode('utf-8')
    actual = actual.strip()
    text_file.write(actual)
    text_file.close()


    if expected != actual:
        raise AssertionError("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))
    else:
        logger.info("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))

    return


def set_battery_sim_volt(ser, volt):
    #set_battery_sim(addr, ch, volt, curr, limit, out):
    """
    Set the Keithley 2306/2281S Battery Simulator Voltage on Channel 1
    """
    ser.flushInput()
    ser.flushOutput()

    # Set GPIB to write to
    ser.write("++addr 16\n".encode('utf-8'))
    time.sleep(.10)

    # Set active channel
    ser.write("DISP:CHAN 1\n".encode('utf-8'))
    time.sleep(.10)

    # Set voltage
    ser.write(("SOUR1:VOLT " + volt + "\n").encode('utf-8'))
    time.sleep(.10)

    return

def update_application():
    """
    Update the Tag firmware application
    """
    command = 'nrfutil dfu serial --port /dev/tty.usbserial-FTZ70J97 --baudrate 115200 --package /Users/jeffw/houston/TagFW/jacquard_v00.32/jacquard/release/jacquard.zip '.split()
    actual = ""

    for line in run_command(command):
        response = str(line)
        expected = "Device programmed"
        failure = "Failed to upgrade target"
        if expected in response:
            actual = expected
        if failure in response:
            actual = failure
    time.sleep(2)
    if expected != actual:
        raise AssertionError("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))
    else:
        logger.info("Expected value: '%s' Actual vaule: '%s'."
                                 % (expected, actual))

    return

def set_wom_connect_timeout(ser):
    """
    Sets the WOM connect timeout
    """
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    actual = "imu_wom on 11 560 Previous 5 12"
    for char in actual:
        ser.write((char).encode('utf-8'))
        time.sleep(0.01)
    ser.write(("\r\n").encode('utf-8'))

    return

def run_command(command):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return iter(p.stdout.readline, b'')

def send_command(ser, command):
    """
    Send commands to serial port with 10ms delay between each byte
    """
    for char in command:
        ser.write((char).encode('utf-8'))
        time.sleep(0.01)
    ser.write(("\n").encode('utf-8'))
    return

def set_relay(ser, relay, setting):
    """
    Set the relay on/off on Arduino Sheild
    """
    ser.flushInput()
    ser.flushOutput()

    ser.write(("relay " + relay + " " + setting + "\r\n").encode('utf-8'))

    return


