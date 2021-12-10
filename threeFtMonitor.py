"""Example of how to create a Peripheral device/GATT Server"""
# Standard modules
import logging
import random
import time

# Bluezero modules
from bluezero import async_tools
from bluezero import adapter
from bluezero import peripheral

# sensor modules
from tfminiplus import TFMini

# constants
# Custom service uuid
THREE_FT_SRVC = '12341000-1234-1234-1234-123456789abc'
# custom characteristic uuid
THREE_FT_CHRC = '12341000-1234-1234-1234-123456789abd'

# https://www.bluetooth.com/specifications/assigned-numbers/
# Bluetooth SIG adopted UUID for Characteristic Presentation Format
DIST_FMT_DSCP = '2904'


distance_sensor = TFMini()

class DistanceMonitor:
    vehicle_previously_detected = False
    violation_start_time = -1
    close_distances = []
    far_distances = []
    num_readings_in_3ft_zone = 0

    @classmethod
    def reset_violation_detector(cls):
        cls.vehicle_previously_detected = False
        cls.violation_start_time = -1
        cls.close_distances = []
        cls.far_distances = []
        cls.num_readings_in_3ft_zone = 0

    @classmethod
    def read_value(cls):
        """
        Example read callback. Value returned needs to a list of bytes/integers
        in little endian format.

        This one does a mock reading CPU temperature callback.
        Return list of integer values.
        Bluetooth expects the values to be in little endian format and the
        temperature characteristic to be an sint16 (signed & 2 octets) and that
        is what dictates the values to be used in the int.to_bytes method call.

        :return: list of uint8 values
        """
        distance_sensor.read_sensor()
        cls.distance = distance_sensor.distance

    @classmethod
    def update_value(cls,characteristic):
        """
        callback to send notifications

        :param characteristic:
        :return: boolean to indicate if timer should continue
        """
        # read/calculate new value.
        cls.read_value()
        # -1 is error code from distance_sensor
        if 0 < cls.distance < 42:
            if not cls.vehicle_previously_detected:
                cls.close_distances.append(cls.distance)
                if len(cls.close_distances) == 10:
                    print("3-feet violation detected!")
                    print(f"distance (integer): {cls.distance}")
                    cls.violation_start_time = distance_sensor.time_of_reading
                    cls.vehicle_previously_detected = True
                    cls.num_readings_in_3ft_zone = len(cls.close_distances)
            else:
                cls.num_readings_in_3ft_zone += 1
                # when in 3ft violation state
                # only add a distance measurement every 100 ms
                if cls.num_readings_in_3ft_zone % 10 == 0:
                    cls.close_distances.append(cls.distance)

        elif cls.vehicle_previously_detected:
            cls.far_distances.append(cls.distance)
            if len(cls.far_distances) == 10:
                # vehicle has cleared the 3ft zone
                # incident report will be created
                violation_end_time = distance_sensor.time_of_reading
                time_in_zone = violation_end_time- cls.violation_start_time
                avg_distance = sum(cls.close_distances)//len(cls.close_distances)
                avg_distance = avg_distance.to_bytes(2, byteorder='little')
                characteristic.set_value(avg_distance)
                print("3-feet violation reported!")
                cls.reset_violation_detector()

        # no object currently detected within 3 feet and
        # no object previously detected within 3 feet
        else:
            cls.reset_violation_detector()

        # Return True to continue notifying. Return a False will stop notifications
        # Getting the value from the characteristic of if it is notifying
        return characteristic.is_notifying

    @classmethod
    def notify_callback(cls,notifying, characteristic):
        """
        Noitificaton callback example. In this case used to start a timer event
        which calls the update callback ever 10 milliseconds

        :param notifying: boolean for start or stop of notifications
        :param characteristic: The python object for this characteristic
        """
        print("notify_callback triggered")
        if notifying:
            # if not characteristic.mainloop.is_running():
            #     characteristic.mainloop.run()
            print("notifying started")
            async_tools.add_timer_ms(11, cls.update_value, characteristic)
        else:
            print("notifying is false...")
            # characteristic.mainloop.quit()

    @classmethod
    def on_disconnect(cls, adapter_address, device_address):
        print("disconnected from "+device_address)




def main(adapter_address):
    """Creation of peripheral"""
    logger = logging.getLogger('localGATT')
    logger.setLevel(logging.DEBUG)
    # Example of the output from read_value
    DistanceMonitor.read_value()
    print(f"distance: {DistanceMonitor.distance}")
    # Create peripheral
    Three_ft_sensor = peripheral.Peripheral(adapter_address,
                                        local_name='3Feet Monitor',
                                        appearance=1344)
    # Add service
    Three_ft_sensor.add_service(srv_id=1, uuid=THREE_FT_SRVC, primary=True)
    # Add characteristic
    Three_ft_sensor.add_characteristic(srv_id=1, chr_id=1, uuid=THREE_FT_CHRC,
                                   value=[], notifying=False,
                                   flags=['read','notify'],
                                   read_callback=DistanceMonitor.read_value,
                                   write_callback=None,
                                   notify_callback=DistanceMonitor.notify_callback
                                   )
    # Add descriptor
    Three_ft_sensor.add_descriptor(srv_id=1, chr_id=1, dsc_id=1, uuid=DIST_FMT_DSCP,
                               # value is in little endian format
                               #  [ unsigned 8-bit, exponent of 1, 27A2 = length(inches)
                               value=[0x06, 0x00, 0xA2, 0x27, 0x00, 0x00,
                                      0x00],
                               flags=['read'])
    # Publish peripheral and start event loop
    Three_ft_sensor.publish()


if __name__ == '__main__':
    # Get the default adapter address and pass it to main
    main(list(adapter.Adapter.available())[0].address)
