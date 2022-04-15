import dbus
from gi.repository import GLib 
import GATT
import constants
import bletools
from advertisement import Advertisement
from distanceMonitor import DistanceMonitor

class DistanceCharacteristic(GATT.Characteristic):
    ''' Notify only Characteristic
        sends a PropertiesChanged Signal whenever a
        car has been detected to come within 6.5 feet
        of the smart-light '''

    def __init__(self, bus, index, service):
        GATT.Characteristic.__init__(
            self, bus, index,
            constants.DISTANCE_CHRC_UUID,
            ['notify'], service)
        self.notifying = False
        self.monitor = DistanceMonitor()


    def notify_distance_violation(self, distance, time):
        if not self.notifying:
            return

        self.PropertiesChanged(
            constants.GATT_CHARACTERISTIC_INTERFACE,
            {'Value': [dbus.Byte(distance)]}, [])

    def monitor_distance(self):
        while self.notifying:
            distance, time = self.monitor.scan_for_violations()
            self.notify_distance_violation(distance, time)

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return
        print("notifications activated!")
        self.notifying = True
        self.monitor_distance()

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False

class DistanceService(GATT.Service):
    def __init__(self, bus, index):
        print("Initialising DistanceService object at",constants.DISTANCE_SVC_UUID)
        GATT.Service.__init__(
            self, bus, index,
            constants.DISTANCE_SVC_UUID, primary = True)
        print("Adding Distance Characteristic")
        self.add_characteristic(DistanceCharacteristic)
        # add more characteristics here
        # TODO: add BatteryCharacteristic to monitor smartLight battery
        #       will need to look at PiSugar documentation for this
        # 
        #       add TemperatureCharacteristic to monitor device temp
        #       operating temp 0C-60C or so


class SmartLightApplication(GATT.Application):
    def __init__(self, bus):
        print("Initialising SmartLightApplication object")
        GATT.Application.__init__(self, bus)
        print("Adding Distance Service")
        self.add_service(DistanceService)
        # Add more services here

    def register(self):
        super().register()
