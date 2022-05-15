import serial
import time
import sys


class TFMini:
    def __init__(self):
        self.port = '/dev/ttyAMA'
        # rpi4 has 4 UART, so we use UART1
        # rpi3 only has 1 UART plus the mini-uart, so UART0 must be used
        with open("/proc/cpuinfo") as f:
            cpuinfo = f.read().lower()
            model_pos = cpuinfo.find("model")
            model = cpuinfo[model_pos:].split(':')[1].strip()
            # note: will not work for raspberry pi 2. Something to keep in mind...
            self.port += '0' if 'raspberry pi 3' in model else '1'

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

        # while distance < self.distance_min or distance > self.distance_max:
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

        # round down to nearest inch
        # keeps distance at -1 in the event of an erroneous reading from the sensor
        if self.distance_min < cm_distance*0.39 < self.distance_max:
            # 1 cm = 0.39 inches
            distance = int(cm_distance*0.39)

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
            print(f"\n\tserial port {self.port} has been closed")



if __name__ == "__main__":
    tfmini = TFMini()
    try:
        start = time.time()
        prev = 0
        while True:
            tfmini.read_sensor()
            total_time = (time.time()-start)*1000
            # if tfmini.distance != prev:
            prev = tfmini.distance
            print("distance read:", end="\t")
            print(tfmini.distance)
            print("ms taken to read sensor:", end="\t")
            print(f"{total_time:.2f}","\n")
            start = time.time()
            time.sleep(.015)
    except KeyboardInterrupt:
        tfmini.close_port()

    print("DONE!")
