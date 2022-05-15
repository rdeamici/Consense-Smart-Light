import dbus
import dbus.service
from time import sleep
from tfminiplus import TFMini

class DistanceMonitor():
    '''represents the car detection monitor part of the smart-light'''

    def __init__(self):
        self.sensor = TFMini()
        self.violation_begin_time = -1
        self.violation_end_time = -1
        self.violation_distance = -1
        self.close_readings = 0
        self.num_close_readings = 0
        self.num_far_readings = 0
        self.state = 0
        self.state_close_readings = 0


    def reset_violation_detector(self):
        ''' used to reset everything back to baseline'''
        self.violation_begin_time = -1
        self.violation_end_time = -1
        self.violation_distance = -1
        self.close_readings = 0
        self.num_close_readings = 0
        self.num_far_readings = 0
        self.state = 0

    def consecutive_readings(self, readings):
        ''' check to see if enough readings of the same value have been
            recorded. If so, move to next state.
            readings will be either num_far_readings, or num_close_readings

           This will only return true on the exact 5th reading, so 
           calling this function for consecutive readings > 5 in a row will return false
        '''
        return readings == 5

    def scan_for_violations(self, test=False):
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
        violation_distance = -1
        res = self.sensor.read_sensor()
        if test and res[0]>1000:
            print("distance:",res[0],'\n','strength',res[1],'\n')
        # -1 is sensor err code
        if self.sensor.distance < 0:
            return violation_distance
        # 84 inches is 6 feet + 1 foot for distance from the sensor
        # to the outermost part of the cyclist closest to the vehicle
        violation = self.sensor.distance < 84

        ######################## state 0 ########################
        if self.state == 0 and violation:
            # detected a distance < 6.5 feet,
            self.close_readings += self.sensor.distance
            self.num_close_readings += 1
            if self.num_close_readings == 1:
                self.violation_begin_time = self.sensor.time_of_reading
            elif self.consecutive_readings(self.num_close_readings):
                print("Object detected!")
                self.state = 1
                self.num_far_readings = 0
            # always reset far_readings counter when a close reading is recorded
            # The sensor occasionally returns false large-distance readings on the rpi3
            # but rarely seems to return false short-distance readings
            self.num_far_readings = 0
        # consecutive readings verification
        elif self.state == 0 and not violation:
            if self.num_close_readings > 0:
                self.num_far_readings += 1
                if self.consecutive_readings(self.num_far_readings):
                    self.reset_violation_detector()
        #########################################################


        ######################## state 1 ########################
        elif self.state == 1 and violation:
            self.close_readings += self.sensor.distance
            self.num_close_readings += 1
            if self.num_close_readings == 24:
                print("3-feet violation detected!")
                print(f"distance (integer): {self.sensor.distance}")

                if test: sleep(5)

                self.state = 2
                self.state_close_readings = 0

            # always reset far readings counter when a close reading is seen
            # The sensor occasionally returns false large-distance readings on the rpi3
            # but rarely seems to return false short-distance readings
            self.num_far_readings = 0

        elif self.state == 1 and not violation:
            self.num_far_readings += 1
            if self.consecutive_readings(self.num_far_readings):
                print("object cleared. Probably not a vehicle")
                self.reset_violation_detector()
        #########################################################


        ######################## state 2 ########################
        elif self.state == 2 and violation:
            self.close_readings += self.sensor.distance
            self.num_close_readings += 1
            self.num_far_readings = 0

        elif self.state == 2 and not violation:
            self.num_far_readings += 1
            if self.consecutive_readings(self.num_far_readings):
                # vehicle has cleared the violation zone
                # incident report will be created
                avg_distance = self.close_readings//self.num_close_readings
                self.violation_end_time = self.sensor.time_of_reading
                print("3-feet violation reported!")
                print("total time:",self.violation_end_time - self.violation_begin_time)
                self.reset_violation_detector()
                violation_distance = avg_distance
        #########################################################
        return violation_distance

    def shutdown(self):
        print("\nshutting down distance monitor")
        self.sensor.close_port()

def main():
    # import dbus.mainloop.glib
    # from gi.repository import GLib
    # dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    # bus = dbus.SystemBus()
    import sys
    monitor = DistanceMonitor()
    # print("running main loop...")
    # mainloop = GLib.MainLoop()
    try:
        # mainloop.run()
        while True:
            violation_distance = monitor.scan_for_violations()
            print("violation distance ='",violation_distance,"'")
            sleep(.01)
    except KeyboardInterrupt:
        monitor.shutdown()
        print("\nsuccessful exit. Goodbye...")
        sys.exit(0)

if __name__ == "__main__":
    print("calling main")


    main()
