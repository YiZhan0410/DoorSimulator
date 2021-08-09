# File: DoorSystem.py
# Description: Professional Practice Week (CET235 - Internet of Things)
# Author: Yi Zhan Wong, University of Sunderland
# Date: May 2020

# Imports
from libs.iot_app import IoTApp
from time import sleep


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
    MQTT_ADDR = "broker.hivemq.com"  # DNS of the public MQTT server
    MQTT_PORT = 1883  # MQTT broker port number

    MQTT_USER = "uos/cet235-41/user/value"  # User's name will publish to this path and subscribe by IoTSystem.py

    def init(self):
        """
        Method to initialise system
        """
        #  Nobody access
        self.indicator = "Available"
        self.user_str = "_______"

        self.wifi_msg = "No Wi-Fi"
        connect_count = 0
        # Try to connect ot Wi-Fi 5 times
        while connect_count < 5 and not self.is_wifi_connected():
            self.oled_clear()
            self.wifi_msg = "Connect Wi-Fi: {0}".format(connect_count + 1)
            self.oled_text(self.wifi_msg, 0, 0)
            self.oled_display()
            self.connect_to_wifi(wifi_settings=(self.AP_SSID, self.AP_PSWD, self.AP_TOUT))
            connect_count += 1

        if self.is_wifi_connected():
            self.wifi_msg = "Wi-Fi"
            # Register to the MQTT broker
            self.register_to_mqtt(server=self.MQTT_ADDR, port=self.MQTT_PORT)
        else:
            self.oled_clear()
            self.wifi_msg = "No Wi-Fi"
            self.oled_text(self.wifi_msg, 0, 0)
            self.oled_display()
            sleep(2)

        self.oled_clear()
        self.oled_text("Press A for user MJ235AA \nPress B for user CK523BB", 0, 0)  # Display option for the user ID

    def loop(self):
        """
        Method after init() and execute until the finish property set to true
        """
        if self.is_wifi_connected():
            # Publish a "uos/cet235-41/user/value" topic message
            # IoTSystem received once for the id and it won't update the user id if user id is switched
            self.mqtt_client.publish(self.MQTT_USER, self.user_str)

    def deinit(self):
        """
        Method that after loop() has finished
        """
        pass

    def btnA_handler(self, pin):
        """
        Method btnA represent user MJ235AA
        """
        self.oled_clear()
        self.indicator = "Occupied"  # Indicate the room is occupied
        self.user_str = "MJ235AA"  # User is MJ235AA
        output = "{0} by user {1}".format(self.indicator, self.user_str)  # Output's value (Occupied by user MJ235AA)
        self.oled_text(output, 0, 0)  # Display on the OLED FeatherWing

    def btnB_handler(self, pin):
        """
        Method btnB represent user CK523BB
        """
        self.oled_clear()
        self.indicator = "Occupied"  # Indicate the room is occupied
        self.user_str = "CK523BB"  # User is CK523BB
        output = "{0} by user {1}".format(self.indicator, self.user_str)  # Output's value (Occupied by user CK523BB)
        self.oled_text(output, 0, 0)  # Display on the OLED FeatherWing

# Main program to run devices
def main():
    """
    Main function for DoorSystem
    """
    #   name: "Door System"
    #   has_oled_board: set to True while using the OLED FeatherWing
    #   finish_button: set to "C" to set finish property to true
    #   start_verbose: Show message that program starts
    #
    app = MainApp(name="Door System", has_oled_board=True, finish_button="C", start_verbose=True)

    # Run the app
    app.run()


# Invoke main() program entrance
if __name__ == "__main__":
    # execute only if run as a script
    main()
