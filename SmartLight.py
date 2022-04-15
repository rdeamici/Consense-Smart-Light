# Standard modules
import logging
import dbus
import dbus.mainloop.glib
from gi.repository import GLib
# local modules
import smartlightGATT
from advertisement import Advertisement
import constants
import bletools
# sensor modules
from distanceMonitor import DistanceMonitor

adv_mgr_interface = None

def properties_changed(interface, changed, invalidated, path):
    if interface == constants.DEVICE_INTERFACE and "Connected" in changed:
        set_connected_status(changed['Connected'])

def interfaces_added(path, interfaces):
    properties = interfaces.get(constants.DEVICE_INTERFACE,{})
    if "Connected" in properties:
        set_connected_status(properties['Connected'])

def set_connected_status(status):
    if status == 1:
        print("Connected!")
        connected = 1
        stop_advertising()
    else:
        print("disconnected")
        connected = 0
        register()

def register_ad_cb():
    print('Advertisement registered OK')

def register_ad_error_cb(error):
    print('Error: Failed to register advertisement: ' + str(error))



def stop_advertising():
    global adv_mgr_interface
    global advertisement
    print("Unregistering advertisement", advertisement.get_path())
    adv_mgr_interface.UnregisterAdvertisement(advertisement.get_path())

def register():
    global bus
    global advertisement
    global adv_mgr_interface
    adapter_path = bletools.find_adapter_path(bus)
    print("found adapter at",adapter_path)
    # get access to adapter object from DBus
    adv_mgr_interface = dbus.Interface(
        bus.get_object(constants.BLUEZ_SERVICE_NAME, adapter_path),
        constants.ADVERTISING_MANAGER_INTERFACE)
        
    print("Registering advertisement",advertisement.get_path(),
          "as",advertisement.local_name)
        
    adv_mgr_interface.RegisterAdvertisement(
        advertisement.get_path(), {},
        reply_handler=register_ad_cb,
        error_handler=register_ad_error_cb)


# logger = logging.getLogger('localGATT')
# logger.setLevel(logging.DEBUG)

# Example of the output from read_sensor()
test_dm = DistanceMonitor()
test_dm.sensor.read_sensor()
print(f"distance: {test_dm.sensor.distance}")

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
bus.add_signal_receiver(
            properties_changed,
            dbus_interface=constants.DBUS_PROPERTIES,
            signal_name = "PropertiesChanged",
            path_keyword = "path")

bus.add_signal_receiver(
            interfaces_added,
            dbus_interface = constants.DBUS_OM_IFACE,
            signal_name = "InterfacesAdded")

#app = smartlightGATT.SmartLightApplication(bus)

advertisement = Advertisement(bus, 0,'peripheral','test...')
register()

mainloop = GLib.MainLoop()
mainloop.run()
# app.register()
# try:
#    app.run()
# except KeyboardInterrupt:
#    app.quit()