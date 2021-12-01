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

    def read_sensor(self):
        '''everytime through the loop try to get distance data from sensor
           if hardware error, distance will be -1 (used for error checking)
           if distance reported is less than min or greater than max
           distance will be truncated to the min or max, respectively'''

        distance = -1
        strength = -1
        avg_distance = 0
        avg_strength = 0
        num_readings = 3
        read_counter = 3

        while read_counter:
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
            
                avg_distance += distance
                avg_strength += strength
                read_counter -= 1

        avg_distance /= num_readings
        avg_strength /= num_readings
        self._distance = avg_distance
        self._strength = avg_strength
        self.time_of_reading = time.time()

        return avg_distance, avg_strength, self.port


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



if __name__ == "__main__":
    tfmini = TFMini(serial_port="/dev/ttyS0")
    
    avg_time = 0
    try:
        distances = []
        for _ in range(50):
            start_time = time.time()
            tfmini.read_sensor()
            total_time = time.time()-start_time
            avg_time += total_time
            distances.append(tfmini.distance)

        avg_time = avg_time/50
        print("distances read:")
        print(distances)
        print(f"avg amount of time needed to read sensor = {avg_time*1000:.4} ms")
    except KeyboardInterrupt:
        tfmini.close()

    print("DONE!")