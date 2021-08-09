# File: IoTSystem.py
# Description: Professional Practice Week (CET235 - Internet of Things)
# Author: Yi Zhan Wong, University of Sunderland
# Date: May 2020

# Imports
import os
from time import sleep
from libs.iot_app import IoTApp
from libs.bme680 import BME680, OS_2X, OS_8X, FILTER_SIZE_3, ENABLE_GAS_MEAS
from neopixel import NeoPixel
from machine import Pin


# Classes
class MainApp(IoTApp):
    """
    IoTApp provides an execution loop that can be started by calling the
    run() method of the IoTApp class (which is of course inherited into the
    app class). All providing implementations of the init(), loop() and deinit() methods.
    Looping of the program can be controlled using the finished flag property of
    the class.
    """
    # Configuration to connect Wi-Fi and MQTT server
    AP_SSID = "DCETLocalVOIP"  # Name for the Wi-Fi
    AP_PSWD = ""  # Password for the Wi-Fi
    AP_TOUT = 5000  # Wi-Fi router
    NTP_ADDR = "13.86.101.172"  # IP address for the NTP server
    NTP_PORT = 123  # NTP server port number
    MQTT_ADDR = "broker.hivemq.com"  # DNS of the public MQTT broker
    MQTT_PORT = 1883  # MQTT broker port number

    MQTT_USER = "uos/cet235-41/user/value"  # User's name received from MQTT server

    def init(self):
        """
        Method to initialise system
        """
        # Initialise the BME680 driver instance with the I2C bus from the ProtoRig instance and
        # with the I2C address where the BME680 device is found on the shared I2C bus (0x76 hex,
        # 118 decimal), note: the I2C object is encapsulated in an I2CAdapter object
        self.sensor_bme680 = BME680(i2c=self.rig.i2c_adapter, i2c_addr=0x76)  # obtain readings from bme680

        # Configuration for bme680 up to 10 heater profiles with their own temperature and duration
        self.sensor_bme680.set_gas_heater_temperature(320)
        self.sensor_bme680.set_gas_heater_duration(150)
        self.sensor_bme680.select_gas_heater_profile(0)

        # Calibration for the readings
        self.sensor_bme680.set_humidity_oversample(OS_2X)
        self.sensor_bme680.set_temperature_oversample(OS_8X)
        self.sensor_bme680.set_filter(FILTER_SIZE_3)
        self.sensor_bme680.set_gas_status(ENABLE_GAS_MEAS)

        self.file_name = "log.csv"  # all readings read into log.csv file in root file system of Huzzah ESP32

        # If log.csv file exists, remove log.csv file
        if self.file_exists(self.file_name):
            os.remove(self.file_name)

        # Open log.csv file, w+ prevents the file overwritten
        self.file = open(self.file_name, "w+")

        # Count lines in log.csv to calculate the time taken during access period
        self.count = 0

        # Configure NeoPixel (Simulate that pin 21 is connected via a jumper wire)
        self.neopixel_pin = self.rig.PIN_21

        # Set pin 21 to a digital output pin that is initially pulled down (off)
        self.neopixel_pin.init(mode=Pin.OUT, pull=Pin.PULL_DOWN)

        # Instantiate a NeoPixel object with the required NeoPixel FeatherWing pin,
        # number of NeoPixels (4 x 8 = 32), bytes used for colour of each NeoPixel
        # and a timing value (keep as 1)
        self.npm = NeoPixel(self.neopixel_pin, 32, bpp=3, timing=1, app=self)

        # Colours are set by using RGB channel tuple value from 0 to 255
        # ((0, 0, 0)) means no coloured
        # ((255, 255, 255)) means black
        # RGB colour code can be find on htmlcolorcodes.com
        # Each NeoPixel can be changed using the [] indexing from 0..31, this splits
        # the matrix into 4 rows of 8 NeoPixels with the following indices:-
        #
        #      0  1  2  3  4  5  6  7
        #      8  9 10 11 12 13 14 15
        #     16 17 18 19 20 21 22 23
        #     24 25 26 27 28 29 30 31
        #
        # Note: index 0 is the NeoPixel furthest to the top left under the FeatherWing
        # text on the NeoPixel FeatherWing board

        # Program start with no coloured lights
        self.npm.fill((0, 0, 0))
        # NeoPixel.write() method is required to display the matrix
        self.npm.write()

        # Nothing is measured before program starts
        self.target_indicator = "N"
        self.temperature_target = None
        self.humidity_target = None
        self.gas_resistance_target = None

        self.ntp_msg = "No Wi-Fi"
        connect_count = 0
        # Try to connect ot Wi-Fi 5 times
        while connect_count < 5 and not self.is_wifi_connected():
            self.oled_clear()
            self.oled_text("Connect Wi-Fi:{0}".format(connect_count + 1), 0, 0)
            self.oled_display()
            self.connect_to_wifi(wifi_settings=(self.AP_SSID, self.AP_PSWD, True, self.AP_TOUT))
            connect_count += 1

        if self.is_wifi_connected():
            self.ntp_msg = "Wi-Fi"
            # Contact with NTP server and update the RTC with the correct date and time
            self.set_rtc_by_ntp(ntp_ip=self.NTP_ADDR, ntp_port=self.NTP_PORT)
            # Register to MQTT broker
            self.register_to_mqtt(server=self.MQTT_ADDR, port=self.MQTT_PORT,
                                  sub_callback=self.mqtt_callback)
            # Subscribe the value that publish from DoorSystem.py
            self.mqtt_client.subscribe(self.MQTT_USER)
            self.oled_clear()
            self.oled_display()
        else:
            self.oled_clear()
            self.oled_text("No WiFi", 0, 0)
            self.oled_display()

        self.user_str = "_______"  # Remaining empty as nobody access

    def loop(self):
        """
        Method after init() and execute until the finish property set to true
        """
        self.oled_clear()

        # Get currently accurate date and time and display it
        yr, mn, dy, dn, hr, mi, se, ms = self.rtc.datetime()
        # Format for date output
        date = "{0} {1:02d}-{2:02d}-{3}".format(self._DAY_NAMES[dn][0:3], dy, mn, yr)
        # Format for time output
        time = "{0:02d}:{1:02d}:{2:02d}".format(hr, mi, se)

        self.oled_display()

        self.oled_clear()
        # Get sensor from bme680 if sensor readings are available and read them per second
        if self.sensor_bme680.get_sensor_data(temperature_target=self.temperature_target,
                                              humidity_target=self.humidity_target,
                                              gas_resistance_target=self.gas_resistance_target):

            tm_reading = self.sensor_bme680.data.temperature  # variable for temperature reading
            rh_reading = self.sensor_bme680.data.humidity  # variable for humidity reading

            if self.is_wifi_connected():
                # Check any message received from the MQTT broker
                self.mqtt_client.check_msg()

            output = "User: {0}".format(self.user_str)  # Output user ID
            self.oled_text(output, 0, 0)  # Output at first line

            output = "{0}".format(date)  # output date on OLED screen
            self.oled_text(output, 0, 10)  # second line of OLED screen

            output = "{0}".format(time)  # output time on OLED screen
            self.oled_text(output, 0, 15)  # third line of OLED screen

            output = "{0:.2f}C,{1:.2f}%rh".format(tm_reading,
                                                  rh_reading)  # output temperature and humidity readings on OLED screen
            self.oled_text(output, 0, 20)  # forth line of OLED screen

            data_line = "{0},{1},{2},{3:.2f},{4:.2f}\n".format(self.user_str, date, time, tm_reading,
                                                               rh_reading)  # format for input data into log.csv file

            self.file.write(data_line)  # all data recorded into log.csv file

            self.count += 1  # Increment for each reading per second
            self.oled_text(self.count, 100, 20)  # Display time taken during access period

            # Constant variables to display colour during access period
            min_second = 0
            medium_second = 5
            max_second = 10
            if self.count >= min_second:
                self.npm.fill((0, 255, 0))  # Display green from 0 - 5 seconds
                self.npm.write()

            if self.count >= medium_second:
                self.npm.fill((255, 195, 0))  # Display amber from 5 - 10 seconds
                self.npm.write()

            if self.count >= max_second:
                self.npm.fill((255, 0, 0))  # Display red after 10 seconds
                self.npm.write()

        #  Display readings on the OLED screen
        self.oled_display()

        #  Take readings every second
        sleep(1)

    def deinit(self):
        """
        Method that after loop() has finished
        """
        # Close file when nobody access
        self.file.close()

        # Turn off the lights
        self.npm.fill((0, 0, 0))
        self.npm.write()

        print("Time taken: {0}".format(self.count))  # Display the time taken after the program closes

    def file_exists(self, file_name):
        """
        function for check file exist, operating system list the file path if it exists
        """
        file_names = os.listdir()

        return file_name in file_names

    def mqtt_callback(self, topic, msg):
        """
        MQTT callback method to received message from DoorSystem.py
        """
        # Received user's id if topic is equal to MQTT_USER and decode by ("utf-8") method
        if topic == self.MQTT_USER:
            self.user_str = "{0}".format(str(msg.decode("utf-8")))

    def btnA_handler(self, pin):
        """
        Simulation for increasing the values of each readings
        """
        self.target_indicator = "H"  # Indicate increasing
        self.temperature_target = 35.0  # Temperature will reach until 35.0
        self.humidity_target = 90  # Humidity will reach until 90
        self.gas_resistance_target = 16000  # Gas resistance will reach until 16000

    def btnB_handler(self, pin):
        """
        Simulation for decreasing the values of each readings
        """
        self.target_indicator = "L"  # Indicate decreasing
        self.temperature_target = 20.0  # Temperature will reach until 20.0
        self.humidity_target = 5  # Humidity will reach until 5
        self.gas_resistance_target = 1000  # Gas resistance will reach until 100s


# Main program to run devices
def main():
    """
    Main function for IoTSystem
    """
    #   name: "Record Log"
    #   has_oled_board: set to True while using the OLED FeatherWing
    #   finish_button: set to "C" to set finish property to true
    #   start_verbose: Show message that program starts
    #
    app = MainApp(name="Record Log", has_oled_board=True, finish_button="C", start_verbose=True)

    # Run the app
    app.run()


# Invoke main() program entrance
if __name__ == "__main__":
    # execute only run as a script
    main()
