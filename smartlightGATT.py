import dbus
from gi.repository import GLib
import GATT
import constants
import bletools
from advertisement import Advertisement
from distanceMonitor import DistanceMonitor

class DistanceDescriptor(GATT.Descriptor):
    ''' Descriptor to tell clients The distance
        characteristic is to be understood as integer
        value representing inches '''

    def __init__(self, bus, index, characteristic):
        GATT.Descriptor.__init__(
            self, bus, index,
            constants.CHR_PRES_FMT_UUID,
            constants.DISTANCE_CHR_VALUE,
            ['read'],
            characteristic
        )

    def ReadValue(self):
        return self.value

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
        self.add_descriptor(DistanceDescriptor)


    def distance_violation_cb(self):
        violation_distance = self.monitor.scan_for_violations()
        # monitor returns -1 except the exact moment it records a violation.
        if violation_distance > 0:
            print("Sending notification!")
            print("distance =",violation_distance)
            self.PropertiesChanged(
                constants.GATT_CHARACTERISTIC_INTERFACE,
                {'Value': [dbus.Byte(violation_distance)]}, [])
            print("    DONE!")
            # have to reset the value here or else we can't
            # both access it here and reset it in DistanceMonitor
            self.monitor.violation_distance = -1
        return self.notifying

    def monitor_distance(self):
        if not self.notifying:
            return
        # turn on DistanceMonitor scanning
        GLib.timeout_add(10,self.distance_violation_cb) #10 ms

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

        print("notifications de-activated!")
        self.notifying = False


class DistanceService(GATT.Service):
    def __init__(self, bus, index):
        print("Initialising DistanceService object at",constants.DISTANCE_SVC_UUID)
        self.local_name = "DistanceService"
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

    def quit(self):
        for serv in self.services:
            if hasattr(serv,'local_name') and serv.local_name=='DistanceService':
                for chr in serv.characteristics:
                    if hasattr(chr,'monitor'):
                        chr.monitor.shutdown()
        super().quit()
