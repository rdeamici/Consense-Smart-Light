import dbus
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