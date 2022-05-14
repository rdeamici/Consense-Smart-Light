#!/usr/bin/python3
#
# Defines Services, Characteristic and Descriptor classes which should be extended to make concrete
# GATT attributes of specific types by Applications
#
# This code largely originates from test/example-gatt-server in the BlueZ source
import dbus
import dbus.exceptions
import dbus.service
from gi.repository import GLib

import constants
import exceptions
import bletools

class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """
    def __init__(self, bus):
        self.eventLoop = bletools.eventLoop()
        self.bus = bus
        self.path = '/'
        self.services = []
        self.srvc_index = 0
        self.adapter_path = bletools.find_adapter_path(self.bus)
        self.service_manager = dbus.Interface(
            self.bus.get_object(constants.BLUEZ_SERVICE_NAME, self.adapter_path),
            constants.GATT_MANAGER_INTERFACE)
        dbus.service.Object.__init__(self, self.bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        srvc = service(self.bus, self.srvc_index)
        self.services.append(srvc)
        self.srvc_index += 1
    
    def register_app_cb(self):
        print('GATT application registered')

    def register_app_error_cb(self, error):
        print('Failed to register application: ' + str(error))
        self.mainloop.quit()

    def register(self):
        print('Registering GATT application...')
        self.service_manager.RegisterApplication(
            self.get_path(), {},
            reply_handler=self.register_app_cb,
            error_handler=self.register_app_error_cb)

    def run(self):
        print("running application!")
        self.eventLoop.run()
    
    def quit(self):
        print("\nGATT application terminated")
        self.eventLoop.quit()


    @dbus.service.method(constants.DBUS_OM_IFACE,
                         out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        print('GetManagedObjects')

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response


class Service(dbus.service.Object):
    """
    org.bluez.GattService1 interface implementation
    since it extend dbus.service.Object it can be exported to DBus
    but generally only an Application is exported.
    """
    SRVC_PATH_BASE = PATH_BASE = '/org/bluez/ldsg/service'

    def __init__(self, bus, index, uuid, primary):
        ''' bus = DBus system bus object
            path_base = path to a Service object
            index = intended to be different for each service in an Application
            uuid = unique identifier for this service
            primary = indicates whether this service is primary or secondary
        '''
        self.path = self.SRVC_PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary # boolean
        self.chrc_index = 0 # increment for every characteristic add
        self.characteristics = [] # will hold chrcs of a concrete Service
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            constants.GATT_SERVICE_INTERFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    self.get_characteristic_paths(),
                    signature='o')
                }
            }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        chrc = characteristic(self.bus, self.chrc_index, self)
        self.characteristics.append(chrc)
        self.chrc_index += 1

    def get_characteristic_paths(self):
        result = []
        for chrc in self.characteristics:
            result.append(chrc.get_path())
        return result

    def get_characteristics(self):
        return self.characteristics

    @dbus.service.method(constants.DBUS_PROPERTIES,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        ''' method of org.freedesktop.DBus.Properties interface
            allows discovery of properties of the Service object
        '''
        if interface != constants.GATT_SERVICE_INTERFACE:
            raise exceptions.InvalidArgsException()

        return self.get_properties()[constants.GATT_SERVICE_INTERFACE]


class Characteristic(dbus.service.Object):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        print("creating Characteristic with path="+self.path)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            constants.GATT_CHARACTERISTIC_INTERFACE: {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
                'Descriptors': dbus.Array(
                    self.get_descriptor_paths(),
                    signature='o')
                }
            }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        result = []
        for desc in self.descriptors:
            result.append(desc.get_path())
        return result

    def get_descriptors(self):
        return self.descriptors

    @dbus.service.method(constants.DBUS_PROPERTIES,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != constants.GATT_CHARACTERISTIC_INTERFACE:
            raise exceptions.InvalidArgsException()

        return self.get_properties()[constants.GATT_CHARACTERISTIC_INTERFACE]

    @dbus.service.method(constants.GATT_CHARACTERISTIC_INTERFACE,
                        in_signature='a{sv}',
                        out_signature='ay')
    def ReadValue(self, options):
        '''override in concrete class'''
        print('Default ReadValue called, returning error')
        raise exceptions.NotSupportedException()

    @dbus.service.method(constants.GATT_CHARACTERISTIC_INTERFACE,
                         in_signature='aya{sv}')
    def WriteValue(self, value, options):
        '''override in concrete class'''
        print('Default WriteValue called, returning error')
        raise exceptions.NotSupportedException()

    @dbus.service.method(constants.GATT_CHARACTERISTIC_INTERFACE)
    def StartNotify(self):
        '''override in concrete class'''
        print('Default StartNotify called, returning error')
        raise exceptions.NotSupportedException()

    @dbus.service.method(constants.GATT_CHARACTERISTIC_INTERFACE)
    def StopNotify(self):
        '''override in concrete class'''
        print('Default StopNotify called, returning error')
        raise exceptions.NotSupportedException()

    @dbus.service.signal(constants.DBUS_PROPERTIES,
                         signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


class Descriptor(dbus.service.Object):
    """
    org.bluez.GattDescriptor1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, characteristic):
        self.path = characteristic.path + '/desc' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.chrc = characteristic
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            constants.GATT_DESCRIPTOR_INTERFACE: {
                'Characteristic': self.chrc.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
                }
            }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(constants.DBUS_PROPERTIES,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != constants.GATT_DESCRIPTOR_INTERFACE:
            raise exceptions.InvalidArgsException()

        return self.get_properties()[constants.GATT_DESCRIPTOR_INTERFACE]

    @dbus.service.method(constants.GATT_DESCRIPTOR_INTERFACE,
                        in_signature='a{sv}',
                        out_signature='ay')
    def ReadValue(self, options):
        print ('Default ReadValue called, returning error')
        raise exceptions.NotSupportedException()

    @dbus.service.method(constants.GATT_DESCRIPTOR_INTERFACE,
                         in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called, returning error')
        raise exceptions.NotSupportedException()
