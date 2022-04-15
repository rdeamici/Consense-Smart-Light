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

# logger = logging.getLogger('localGATT')
# logger.setLevel(logging.DEBUG)

# Example of the output from read_sensor()
test_dm = DistanceMonitor()
test_dm.sensor.read_sensor()
print(f"distance: {test_dm.sensor.distance}")

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

advertisement = Advertisement(bus, 0,'peripheral','test...')
advertisement.register()

mainloop = GLib.MainLoop()
mainloop.run()
# app.register()
# try:
#    app.run()
# except KeyboardInterrupt:
#    app.quit()