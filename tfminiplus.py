import serial
import time
import sys

class TFMini:
    def __init__(self, serial_port="/dev/ttyAMA1"):
        self.port = serial_port
        self.time_of_reading = None
        self._ser = serial.Serial(self.port,115200)
        if not self._ser.is_open:
            self._ser.open()
        
        time.sleep(0.1)

        self._distance = 0
        self._strength = 0
        self.distance_min = 4 # inches
        self.distance_max = 480 # 40 feet
        if self._ser.in_waiting > 0:
            print(f"sensor at {self.port} up and sensing...")
        else:
            print(f"sensor at {self.port} not working...")
        

    def read_sensor(self):
        ''' everytime through the loop try to get distance data from sensor
            if hardware error, distance will be -1 (used for error checking)
            if distance reported is less than min or greater than max
            distance will be truncated to the min or max, respectively
        '''
        distance = -1
        strength = -1

        recv = [0,0]
        attempts = 10
        while recv[0] != 0x59 and recv[1] != 0x59 and attempts:
            count = self._ser.in_waiting
            while count < 9:
                count = self._ser.in_waiting
            recv = self._ser.read(9)
            self._ser.reset_input_buffer()
            attempts -= 1

        if attempts:
            cm_distance = recv[2] + recv[3]*256 
            strength = recv[4] + recv[5]*256
            # 1 cm = 0.39 inches
            distance = cm_distance*0.39

        # round down to nearest inch
        distance = int(distance)
        self._distance = distance
        self._strength = strength
        self.time_of_reading = time.time()
        # print(f"tfmini distance: {self._distance}")
        return distance, strength, self.port


    @property
    def distance(self):
        return self._distance

    @property
    def strength(self):
        return self._strength


    def close_port(self):
        if self._ser != None and self._ser.is_open:
            self._ser.close()
            print(f"\nserial port {self.port} has been closed")



if __name__ == "__main__":
    tfmini = TFMini()
    try:
        start = time.time()
        while True:
            tfmini.read_sensor()
            total_time = (time.time()-start)*1000
            print("distance read:")
            print(tfmini.distance)
            print("ms taken to read sensor:")
            print(total_time)
            start = time.time()
            time.sleep(.009)
    except KeyboardInterrupt:
        tfmini.close_port()

    print("DONE!")
