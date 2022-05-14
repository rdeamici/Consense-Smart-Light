import dbus
import dbus.service
from time import sleep
from tfminiplus import TFMini

class DistanceMonitor():
    '''represents the car detection monitor part of the smart-light'''

    def __init__(self, serial_port=None):
        self.sensor = TFMini() if serial_port is None else TFMini(serial_port)
        self.violation_begin_time = -1
        self.violation_end_time = -1
        self.violation_distance = -1
        self.close_readings = []
        self.num_far_readings = 0
        self.state = 0
        self.scanning = False

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
                         If consecutive readings reaches 24, then
                         state 2 is triggered.
                         If 5 consecutive readings > 6.5 feet then 
                         state 0 is triggered, and no violation
                         distance value is returned

                state 2: an object is currently in violation zone
                         and has been for 240 ms, which is minimum
                         amount needed to detect a car.
                         stays in this state until vehicle clears, in
                         which case a violation is created and
                         reverts back to state 0

                must have 5 consecutive readings in order to transition
                from one state to another
        '''
        self.sensor.read_sensor()
        # -1 is sensor err code    78 inches is 6.5 feet
        violation = 0 < self.sensor.distance < 78
            
        ######################## state 0 ########################
        if self.state == 0 and violation:
            # detected a distance < 6.5 feet,
            self.close_readings.append(self.sensor.distance)
            if len(self.close_readings) == 1:
                self.violation_begin_time = self.sensor.time_of_reading 
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
                self.violation_end_time = self.sensor.time_of_reading
                print("3-feet violation reported!")
                print("total time:",self.violation_end_time - self.violation_begin_time)
                self.reset_violation_detector()
                self.violation_distance = avg_distance
        #########################################################



def main():
    import dbus.mainloop.glib
    from gi.repository import GLib
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    monitor = DistanceMonitor(bus)
    print("running main loop...")
    mainloop = GLib.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("\nstopping main loop...")
        mainloop.quit()

if __name__ == "__main__":
    print("calling main")


    main()