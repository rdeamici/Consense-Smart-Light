#!/usr/bin/python3
# Broadcasts connectable advertising packets
import dbus
import dbus.exceptions
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

import constants
import exceptions
import bletools

# much of this code was copied or inspired by test\example-advertisement in the BlueZ source
class Advertisement(dbus.service.Object):
    ''' represents a DBus advertisement object
        base class for creating Advertisements.
        class extends dbus.service.Object so it can be
        registered with DBus '''

    PATH_BASE = '/org/bluez/ldsg/advertisement'

    def __init__(self, index, advertising_type, name):
        ''' index should increment for every successive advertisement created
            advertising_type options are 'peripheral','broadcast'
        '''
        self.path = self.PATH_BASE + str(index)
        self.bus = dbus.SystemBus()

        if advertising_type not in ('peripheral', 'broadcast'):
            raise exceptions.InvalidArgsException()

        self.ad_type = advertising_type
        self.local_name = name
        self.service_uuids = None
        self.manufacturer_data = None
        self.solicit_uuids = None
        self.service_data = None
        self.include_tx_power = False
        self.data = None
        # causes flags field to be included in advert packet with bits set
        # to indicate General Discoverable Mode see core specification 9.2.4
        self.discoverable = True
        dbus.service.Object.__init__(self, self.bus, self.path)
        self.adv_mgr_interface = None
        self.connected = 0
        self.add_signal_receiver(
            self.properties_changed,
            dbus_interface=constants.DBUS_PROPERTIES,
            signal_name = "PropertiesChanged",
            path_keyword = "path")

        self.bus.add_signal_reciever(
            self.interfaces_added,
            dbus_interface = constants.DBUS_OM_IFACE,
            signal_name = "InterfacesAdded")


    def get_properties(self):
        properties = dict()
        properties['Type'] = self.ad_type

        if self.service_uuids is not None:
            properties['ServiceUUIDs'] = dbus.Array(self.service_uuids,
                signature='s')        
        if self.solicit_uuids is not None:
            properties['SolicitUUIDs'] = dbus.Array(self.solicit_uuids,
                signature='s')
        if self.manufacturer_data is not None:
            properties['ManufacturerData'] = dbus.Dictionary(
                self.manufacturer_data, signature='qv')
        if self.service_data is not None:
            properties['ServiceData'] = dbus.Dictionary(self.service_data,
                signature='sv')
        if self.local_name is not None:
            properties['LocalName'] = dbus.String(self.local_name)
        if self.discoverable is not None and self.discoverable:
            properties['Discoverable'] = dbus.Boolean(self.discoverable)
        if self.include_tx_power:
            properties['Includes'] = dbus.Array(["tx-power"], signature='s')
        if self.data is not None:
            properties['Data'] = dbus.Dictionary(
                self.data, signature='yv')
        print(self.path, "properties:",properties)
        return {constants.ADVERTISING_MANAGER_INTERFACE: properties}

    def get_path(self):
        ''' returns path to the DBus object that represents the advertisement
            useful for logging, and registering/unregistering advertisement '''
        return dbus.ObjectPath(self.path)

    @dbus.service.method(constants.DBUS_PROPERTIES,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        ''' returns dictionary of named property values to be converted
            to advertising packet TLV fields once advertising commences '''

        if interface != constants.ADVERTISEMENT_INTERFACE:
            raise exceptions.InvalidArgsException()
        return self.get_properties()[constants.ADVERTISING_MANAGER_INTERFACE]

    @dbus.service.method(constants.ADVERTISING_MANAGER_INTERFACE,
                         in_signature='',
                         out_signature='')
    def Release(self):
        print('%s: Released' % self.path)

    def set_connected_status(self, status):
        if status == 1:
            print("Connected!")
            self.connected = 1
            self.stop_advertising()
        else:
            print("disconnected")
            self.connected = 0
            self.register()

    def properties_changed(self, interface, changed, invalidated, path):
        if interface == constants.DEVICE_INTERFACE and "Connected" in changed:
            self.set_connected_status(changed['Connected'])

    def interfaces_added(self, path, interfaces):
        properties = interfaces.get(constants.DEVICE_INTERFACE,{})
        if "Connected" in properties:
            self.set_connected_status(properties['Connected'])


    def register_ad_cb(self):
        print('Advertisement registered OK')

    def register_ad_error_cb(self, error):
        print('Error: Failed to register advertisement: ' + str(error))

    def stop_advertising(self):
        print("Unregistering advertisement",self.get_path())
        self.adv_mgr_interface.UnregisterAdvertisement(self.get_path())

    def register(self):
        adapter_path = bletools.find_adapter_path(self.bus)
        # get access to adapter object from DBus
        self.adv_mgr_interface = dbus.Interface(
            self.bus.get_object(constants.BLUEZ_SERVICE_NAME, adapter_path),
            constants.ADVERTISING_MANAGER_INTERFACE)
        
        print("Registering advertisement",self.get_path(),
              "as",self.local_name)
        
        self.adv_mgr_interface.RegisterAdvertisement(
            self.get_path(), {},
            reply_handler=self.register_ad_cb,
            error_handler=self.register_ad_error_cb)



if __name__=="__main__":
    adv = Advertisement(0, 'peripheral','test')
    adv.register()
    print("Advertising as "+adv.local_name)
    