from tfminiplus import TFMini
import time

class ThreeFeet:
    '''distance between sensors is in cm'''

    def __init__(self, serial_port1="/dev/ttyS0",serial_port2="/dev/ttyAMA1", distance_between_sensors=12):
        self.tfmini_back = TFMini(serial_port=serial_port1)
        self.tfmini_front = TFMini(serial_port=serial_port2)


    def close_serial_ports(self):
        self.tfmini_back.close()
        self.tfmini_front.close()

    def read_sensors(self):
        self.tfmini_back.read_sensor()
        self.tfmini_front.read_sensor()

    def print_both_sensor_readings(self):
        self.read_sensors()
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
            sensor.read_sensor()
            avg_distance += sensor.distance

        avg_dist /= 3
        return avg_dist
        


    def check_for_violations(self):
        '''3.5 feet is about 106 cm. TFMini Plus returns cm values'''
        violation_detected = False
        while True:
            self.read_sensors()
            # case 1: back sensor detects vehicle within 3 feet, front sensor does not
            # case 2: back sensor doesn't detect vehicle within 3 feet, front sensor does
            # case 3: both sensors detect vehicle within 3 feet
            # back sensor took a reading less than 3.5 feet
            if not violation_detected and self.tfmini_back.distance < 106 and self.tfmini_front.distance >= 106:
                print(f"back sensor detects 3feet violation!\n    Distance = {self.tfmini_back.distance}")
                self.begin_violation_time = self.tfmini_back.time_of_reading

                while self.tfmini_front.distance >= 106:
                    self.tfmini_front.read_sensor()
                
                print(f"front sensor detects 3feet violation!\n    Distance = {self.tfmini_front.distance}")
                self.end_violation_time = self.tfmini_front.time_of_reading

                time.sleep(0.001)
                print("3 feet violation detected!")
                mph = self.calculate_speed()
                print(f"object moving @ {mph} mph\n")
                time.sleep(1)

            while violation_detected: # wait until vehicle is gone from sensors view
                self.read_sensors()
                violation_detected = self.tfmini_back.distance < 106 and self.tfmini_front.distance < 106
            
            

    def print_distance_in_feet_and_inches(self):
        # 20.48 cm in a foot
        # 0.39 inches in a cm
        d = self.tfmini_back.distance
        ft = d//30.48
        inches = (d%30.48)*0.3937007874

        print(f"{d}' {inches:.2}''")



if __name__ == "__main__":
    device = ThreeFeet()
    try:
        device.check_for_violations()
    except KeyboardInterrupt:
        device.close_serial_ports()


    # import sys
    # num_readings = int(sys.argv[1])
    # far_sensor = TFMini(serial_port="/dev/ttyS0")
    # near_sensor = TFMini(serial_port="/dev/ttyAMA1")
    # start = time.time()
    # distances_far = []
    # distances_near = []
    
    # time.sleep(0.01)
    # distances_far = []
    # distances_near = []
    # queued_results = []
    # far_q = Queue()
    # near_q = Queue()
    # far_p = Process(target=read_sensor_into_q, args=(far_sensor,far_q))
    # near_p = Process(target=read_sensor_into_q, args=(near_sensor,near_q))
        
    # start = time.time()
    # for _ in range(num_readings):
    #     far_p.run()
    #     near_p.run()
    #     # start = time.time()
    
    # end = time.time()
    # while not far_q.empty():
    #     print(far_q.get_nowait())
    # while not near_q.empty():
    #     print(near_q.get_nowait())
    # far_q.close()
    # near_q.close()
    # time.sleep(0.01)
    # total_sec = end-start
    # total_ms = total_sec*1000
    # print(f"QUEUES: took {total_ms:,} ms to read both sensors {num_readings} times")
    # for r in queued_results:
    #     print(r)    



    # time.sleep(0.01)
    # start = time.time()
    # synchronous_results = []
    # for _ in range(num_readings):
    #     far_sensor.read_sensor()
    #     far_res = far_sensor.distance
    #     near_sensor.read_sensor()
    #     near_res = near_sensor.distance
    #     synchronous_results.append((far_res,near_res))

    # end = time.time()
    # total_sec = end-start
    # total_ms = total_sec*1000
    # print(f"SYNCHRONOUS: took {total_ms:,} ms to read both sensors {num_readings} times")
    # for r in synchronous_results:
    #     print(r)

    # time.sleep(0.01)
    # start = time.time()
    # for _ in range(num_readings):
    #     far_sensor.read_sensor()
    #     far_res = far_sensor.distance
    # end = time.time()

    # total_sec = end-start
    # total_ms = total_sec*1000
    # print(f"took {total_ms:,} ms to read far sensor {num_readings} times")
    
    # start = time.time()
    # for _ in range(num_readings):
    #     near_sensor.read_sensor()
    #     near_res = near_sensor.distance
    # end = time.time()
    # total_sec = end-start
    # total_ms = total_sec*1000
    # print(f"took {total_ms:,} ms to read near sensor {num_readings} times")

    # start = time.time()
    # near_sensor.read_sensor()
    # end = time.time()
    # total_sec = end-start
    # total_ms = total_sec*1000
    # print(f"took {total_ms:,} ms to read near sensor just one time")


    # far_sensor.close()
    # near_sensor.close()