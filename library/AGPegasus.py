import requests
import time
import os

class Uranus:

    def __init__(self,reboot=0):
        self.error = ''

        dev_url = "http://localhost:32000/Server/DeviceManager/Connected"
        try:
            list_resp = requests.get(dev_url)
        except:
            os.startfile("C:/ProgramData/Microsoft/Windows/Start Menu/Programs/Unity Platform/PegasusAstro - Unity Platform.lnk")
            time.sleep(60)
            try:
                list_resp = requests.get(dev_url)
            except:
                self.error = "Communication Error"
                return

        devlist = list_resp.json()
        
        for item in devlist["data"]:
            if item['name'] == "Uranus":
                self.uranus_id = item['uniqueKey']

        if not hasattr(self,'uranus_id'):
            self.error = "Uranus ID not detected"
            print("Uranus ID not detected")
            return

        if reboot == 1:
        # Reboot the device
            rb_url = f"http://localhost:32000/Driver/Uranus/Reboot?DriverUniqueKey={self.uranus_id}"
            requests.put(rb_url)
            time.sleep(3)

        self.refresh()

    def refresh(self):

        if not hasattr(self,'uranus_id'):
            self.error = "Uranus ID not detected"
            print("Uranus ID not detected")
            return

        api_url = f"http://localhost:32000/Driver/Uranus/Report?DriverUniqueKey={self.uranus_id}"
        try:
            response = requests.get(api_url)
        except:
            self.error = "Communication Error"
            return
        data = response.json()
        if response.status_code != 202:
            print("Error receiving request")
            return

        self.dewpoint = data["data"]["message"]["dewPoint"]["temperature"]
        self.humidity = data["data"]["message"]["relativeHumidity"]["percentage"]
        self.mpsas = data["data"]["message"]["skyQuality"]["mpsas"]
        self.latitude = data["data"]["message"]["latitude"]["dd"]["decimalDegree"]
        self.longitude = data["data"]["message"]["longitude"]["dd"]["decimalDegree"]
        self.altitude = data["data"]["message"]["altitude"]["meters"]
        self.barometricAltitude = data["data"]["message"]["barometricAltitude"]["meters"]
        self.cloudpct = data["data"]["message"]["cloudCoverage"]["percentage"]
        self.lux = data["data"]["message"]["illuminance"]["lux"]
        self.nelm = data["data"]["message"]["nelm"]["vMag"]
        self.temp = data["data"]["message"]["temperature"]["temperature"]
        self.skytemp = data["data"]["message"]["skyTemperature"]["temperature"]
        self.skytempdiff = data["data"]["message"]["temperatureDifference"]["temperature"]
        self.gpsfix = data["data"]["message"]["isGpsFixed"]
        self.relativePressure = data["data"]["message"]["relativePressure"]["hPa"]
        self.dewPoint = data["data"]["message"]["dewPoint"]["temperature"]

        print(f"Clouds {self.cloudpct}%, light {self.lux}, nelm {self.nelm}")
        return


class upbv2:

    def __init__(self):
        self.error = ''

        dev_url = "http://localhost:32000/Server/DeviceManager/Connected"
        try:
            list_resp = requests.get(dev_url)
        except:
            os.startfile("C:/ProgramData/Microsoft/Windows/Start Menu/Programs/Unity Platform/PegasusAstro - Unity Platform.lnk")
            time.sleep(20)
            try:
                list_resp = requests.get(dev_url)
            except:
                self.error = "Communication Error"
                return

        devlist = list_resp.json()
        
        for item in devlist["data"]:
            if item['name'] == "UPBv2":
                self.upbv2_id = item['uniqueKey']

        if not hasattr(self,'upbv2_id'):
            self.error = "UPBv2 ID not detected"
            print("UPBv2 ID not detected")
            return

        self.refresh()

    def refresh(self):

        if not hasattr(self,'upbv2_id'):
            self.error = "UPBv2 ID not detected"
            print("UPBv2 ID not detected")
            return

        api_url = f"http://localhost:32000/Driver/UPBv2/Report?DriverUniqueKey={self.upbv2_id}"
        try:
            response = requests.get(api_url)
        except:
            self.error = "Communication Error"
            return
        data = response.json()
        if response.status_code != 200:
            print("Error receiving request")
            return

        self.voltage = data["data"]["message"]["voltage"]
        self.current = data["data"]["message"]["current"]
        self.power = data["data"]["message"]["power"]
        self.temperature = data["data"]["message"]["temperature"]
        self.humidity = data["data"]["message"]["humidity"]
        self.dewPoint = data["data"]["message"]["dewPoint"]
        self.wattPerHour = data["data"]["message"]["wattPerHour"]
        self.ampsPerHour = data["data"]["message"]["ampsPerHour"]
        self.upTime = data["data"]["message"]["upTime"]
        


