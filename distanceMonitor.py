from time import sleep
from tfminiplus import TFMini

class DistanceMonitor:
    '''represents the car detection monitor part of the smart-light'''

    def __init__(self, serial_port=None):
        self.sensor = TFMini() if serial_port is None else TFMini(serial_port)
        self.violation_time = -1
        self.close_readings = []
        self.num_far_readings = 0
        self.state = 0


    def reset_violation_detector(self):
        ''' used to reset everything back to baseline'''
        self.violation_time = -1
        self.close_readings = []
        self.num_far_readings = 0
        self.state = 0

    def consecutive_readings(self, readings):
        ''' check to see if enough readings of the same value have been
            recorded. If so, move to next state.
            readings will be either num_far_readings, or len(close_readings)
        '''
        return readings == 5

    def scan_for_violations(self):
        ''' function that monitors for vehicles that
            come within 6.5 feet (78 inches) of smart-light.
            
            There are 2 states the monitor can be in:
                state 0: no object detected within 78 inches of sensor,
                         for 5 consecutive sensor readings

                state 1: an object has been detected within 78 inchese
                         for at least 5 consecutive readings. 
                         If consecutive readings reaches 24, then a 
                         violation distance value is returned. 
                         If 5 consecutive readings > 6.5 feet then 
                         state 0 is triggered, and no violation
                         distance value is returned

                must have 5 consecutive readings in order to transition
                from one state to another
        '''
        self.reset_violation_detector()
        sleep_time = .010 # 10 milliseconds
        while True:
            self.sensor.read_sensor()
            # -1 is error code from distance_sensor
            # 78 inches is 6.5 feet
            violation = 0 < self.sensor.distance < 78
            
            ######################## state 0 ########################
            if self.state == 0 and violation:
                # detected a distance < 6.5 feet,
                self.close_readings.append(self.sensor.distance)
                if self.consecutive_readings(len(self.close_readings)):
                    self.state = 1
                    self.num_far_readings = 0

            # consecutive readings verification
            elif self.state == 0 and not violation:
                if len(self.close_readings) > 0:
                    self.num_far_readings += 1
                    if self.consecutive_readings(self.num_far_readings):
                        self.num_far_readings = 0
                        self.close_readings = []
            #########################################################

            ######################## state 1 ########################
            elif self.state == 1 and violation:
                if len(self.close_readings) < 24:
                    self.close_readings.append(self.sensor.distance)
                elif len(self.close_readings) == 24:
                    print("3-feet violation detected!")
                    print(f"distance (integer): {self.sensor.distance}")
                    self.violation_time = self.sensor.time_of_reading
                    self.state = 2
                    self.num_far_readings = 0
            elif self.state == 1 and not violation:
                self.num_far_readings += 1
                if self.consecutive_readings(self.num_far_readings):
                    print("object cleared. Probably not a vehicle")
                    self.reset_violation_detector()
            #########################################################

            ######################## state 2 ########################
            elif self.state == 2 and violation:
                pass # stay in state 2 until object clears sensor
            elif self.state == 2 and not violation:
                self.num_far_readings += 1
                if self.consecutive_readings(self.num_far_readings):
                    # vehicle has cleared the violation zone
                    # incident report will be created
                    avg_distance = sum(self.close_readings)//len(self.close_readings)
                    print("3-feet violation reported!")
                    print("distance =",avg_distance)
                    self.reset_violation_detector()
                    return avg_distance, self.violation_time
            #########################################################
            sleep(sleep_time)

    @classmethod
    def notify_callback(self,notifying, characteristic):
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
            async_tools.add_timer_ms(11, self.update_value, characteristic)
        else:
            print("notifying is false...")
            # characteristic.mainloop.quit()

    @classmethod
    def on_disconnect(self, adapter_address, device_address):
        print("disconnected from "+device_address)