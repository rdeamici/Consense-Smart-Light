# Standard modules
import logging

# local modules
import smartlightGATT

# sensor modules
from distanceMonitor import DistanceMonitor


# logger = logging.getLogger('localGATT')
# logger.setLevel(logging.DEBUG)

# Example of the output from read_sensor()
test_dm = DistanceMonitor()
test_dm.sensor.read_sensor()
print(f"distance: {test_dm.sensor.distance}")


app = smartlightGATT.SmartLightApplication()
app.register()
try:
    app.run()
except KeyboardInterrupt:
    app.quit()