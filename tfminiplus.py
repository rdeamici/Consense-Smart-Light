import serial
import time
import sys

class TFMini:
    def __init__(self, serial_port="/dev/ttyS0"):
        self.port = serial_port
        self._ser = serial.Serial(self.port,115200)
        if not self._ser.is_open:
            self._ser.open()
        
        time.sleep(0.1)

        self._distance = 0
        self._strength = 0
        self.distance_min = 10 # appr 4 inches
        self.distance_max = 1200 # appr 40 feet
        if self._ser.in_waiting > 0:
            print(f"sensor at {self.port} up and sensing...")
        else:
            print(f"sensor at {self.port} not working...")

    def get_data(self):
        '''everytime through the loop try to get distance data from sensor
           if hardware error, distance will be -1 (used for error checking)
           if distance reported is less than min or greater than max
           distance will be truncated to the min or max, respectively'''

        distance = -1
        strength = -1

        count = self._ser.in_waiting
        while count < 9:
            count = self._ser.in_waiting

        recv = self._ser.read(9)
        self._ser.reset_input_buffer()
        if recv[0] == 0x59 and recv[1] == 0x59:
            distance = recv[2] + recv[3]*256
            strength = recv[4] + recv[5]*256

            if distance < self.distance_min:
                distance = self.distance_min
            elif distance > self.distance_max:
                distance = self.distance_max

        self._distance = distance
        self._strength = strength


    @property
    def distance(self):
        return self._distance

    @property
    def strength(self):
        return self._strength


    def close(self):
        if self._ser != None and self._ser.is_open:
            self._ser.close()
            print(f"serial port {self.port} has been closed")


class ThreeFeet:
    '''distance between sensors is in cm'''

    def __init__(self, serial_port1="/dev/ttyS0",serial_port2="/dev/ttyAMA1", distance_between_sensors=12):
        self.tfmini_back = TFMini(serial_port=serial_port1)
        self.tfmini_front = TFMini(serial_port=serial_port2)


    def close_serial_ports(self):
        self.tfmini_back.close()
        self.tfmini_front.close()

    def start_sensing(self):
        self.tfmini_back.get_data()
        self.tfmini_front.get_data()

    def print_both_sensors(self):
        self.tfmini_back.get_data()
        self.tfmini_front.get_data()
        print("back sensor: {:}".format(self.tfmini_back.distance))
        print("front sensor: {:}\n".format(self.tfmini_front.distance))        

    def calculate_speed(self):
        d = 12 # distance between sensors in sm
        t = self.end_violation_time - self.begin_violation_time
        cm_per_ms = d/t
        mph = cm_per_ms / 44.704
        return mph

    def confirm_reading_from_sensor(self, sensor):
        i = 0
        self.begin_violation_time = time.time()
        avg_dist = sensor.distance()
        for _ in range(2):
            sensor.get_data()
            avg_distance += sensor.distance

        avg_dist /= 3
        return avg_dist
        


    def check_for_violations(self):
        '''3.5 feet is about 106 cm. TFMini Plus returns cm values'''
        while True:
            self.print_both_sensors()
            if self.tfmini_back.distance > 106 or self.tfmini_back.distance < 0:
                continue

            # back sensor took a reading less than 3.5 feet
            dist = confirm_reading_from_sensor(self.tfmini_back)
            if dist > 106:
            print(f"back sensor distance = {self.tfmini_back.distance}")
            self.begin_violation_time = time.time()
            while 0 < self.tfmini_front.distance >= 106:
                self.tfmini_front.get_data()
            i = 0
            while i < 10:
                self.tfmini_front.get_data()
                if 0 < self.tfmini_front.distance < 106:
                    i += 1
            print(f"front sensor distance = {self.tfmini_front.distance}")
            self.end_violation_time = time.time()
            print("3 feet violation detected!")
            mph = self.calculate_speed()
            print(f"object moving @ {mph} mph\n")
            print("pausing for 5 seconds")
            time.sleep(5)
            print("DONE!\n")

    def print_distance_in_feet_and_inches(self):
        # 20.48 cm in a foot
        # 0.39 inches in a cm
        d = self.tfmini_back.distance
        ft = d//30.48
        inches = (d%30.48)*0.3937007874

        print(f"{d}' {inches:.2}''")

if __name__ == "__main__":
    # tfmini1 = TFMini(serial_port="/dev/ttyS0")
    
    threeft = ThreeFeet()
    # avg_time = 0
    try:
    #     for _ in range(50):
    #         start_time = time.time()
    #         threeft.tfmini_back.get_data()
    #         total_time = time.time()-start_time
    #         avg_time += total_time

    #     avg_time = avg_time/50
    #     print(f"avg amount of time needed to read sensor = {avg_time*1000:.4} ms")
        threeft.check_for_violations()
    except KeyboardInterrupt:
        threeft.close_serial_ports()
    print("DONE!")