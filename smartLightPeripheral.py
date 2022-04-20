import dbus

from advertisement import Advertisement
import smartlightGATT
import bletools

class SmartLightPeripheral:
      def __init__(self):
            self.eventLoop = bletools.eventLoop() # do this before accessing the system bus
            self.bus = dbus.SystemBus()
            self.advertisement = Advertisement(self.bus, 0,'peripheral','Consense Smart-Light')
            self.advertisement.register()
            self.app = smartlightGATT.SmartLightApplication(self.bus)
            self.app.register()

      def publish(self):
            try:
                self.app.run()
            except KeyboardInterrupt:
                self.app.quit()
