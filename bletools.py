import dbus
import dbus.mainloop.glib
from gi.repository import GLib

#local modules
import constants

def find_adapter_path(bus):
    '''returns the dbus objectManager adapter'''
    remote_om = dbus.Interface(
        bus.get_object(constants.BLUEZ_SERVICE_NAME, "/"),
        constants.DBUS_OM_IFACE)

    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if constants.ADVERTISING_MANAGER_INTERFACE in props:
            return o

    return None

class eventLoop:
    """Facade class to help with using GLib event loop"""
    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.mainloop = GLib.MainLoop()

    def run(self):
        """Run event loop"""
        self.mainloop.run()

    def quit(self):
        """Stop event loop"""
        self.mainloop.quit()

    def is_running(self):
        """Check if event loop is running"""
        self.mainloop.is_running() 
