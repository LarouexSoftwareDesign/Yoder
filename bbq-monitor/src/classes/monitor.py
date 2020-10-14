# ==================================================================================
#   File:   monitor.py
#   Author: Larry W Jordan Jr (larouex@gmail.com)
#   Use:    This class will return and instance of the BBQ Monitor and with a 
#           runing monitoring loop
#
#   Online: https://github.com/LarouexSoftwareDesign/Yoder
#
#   (c) 2020 Larouex Software Design LLC
#   This code is licensed under MIT license (see LICENSE.txt for details)
# ==================================================================================
import json, sys, time, string, threading, asyncio, os, copy, datetime
import logging

# Pi Plates
import piplates.DAQCplate as DAQCPlate
import piplates.THERMOplate as ThermoPlate
import RPi.GPIO as GPIO

# from prettytable import PrettyTable
from texttable import Texttable

# our classes
from classes.config import Config
from classes.secrets import Secrets
from classes.maptelemetry import MapTelemetry
from classes.deviceclient import DeviceClient
from classes.devicescache import DevicesCache

class Monitor():

    def __init__(self, Log):
      self.logger = Log

      # Load configuration
      self.config = []
      self.load_config()

      # --------------------------------------------------------
      # Plate Addresses
      # --------------------------------------------------------
      self.ThermoPlate_addr = 0
      self.DAQCPlate_addr = 1

      # --------------------------------------------------------
      # Worker Variables for Current Temp
      # --------------------------------------------------------
      self.TemperatureAmbient = 0.0
      self.TemperatureFireBox = 0.0
      self.TemperatureWarmingBox = 0.0
      self.TemperatureLeftBack = 0.0
      self.TemperatureRightBack = 0.0
      self.TemperatureLeftFront = 0.0
      self.TemperatureRightFront = 0.0

      # --------------------------------------------------------
      # Worker Variables for Current Temp
      # --------------------------------------------------------
      self.TemperatureAmbientMapName = "ambienttemperature"
      self.TemperatureFireBoxMapName = "firebox"
      self.TemperatureWarmingBoxMapName = "warmingbox"
      self.TemperatureLeftBackMapName = "leftbackchamber"
      self.TemperatureRightBackMapName = "rightbackchamber"
      self.TemperatureLeftFrontMapName = "leftfrontchamber"
      self.TemperatureRightFrontMapName = "rightfrontchamber"

      # --------------------------------------------------------
      # Worker Variables for last Read Temp
      # --------------------------------------------------------
      self.LastTemperatureAmbient = 0.0
      self.LastTemperatureFireBox = 0.0
      self.LastTemperatureWarmingBox = 0.0
      self.LastTemperatureLeftBack = 0.0
      self.LastTemperatureRightBack = 0.0
      self.LastTemperatureLeftFront = 0.0
      self.LastTemperatureRightFront = 0.0

      # Setup the Variables for Status
      self.Alert = self.config["Status"]["Pins"]["Alert"]
      self.Wait = self.config["Status"]["Pins"]["Wait"]
      self.Good = self.config["Status"]["Pins"]["Good"]

      # Setup PiPlate Pin Variables
      self.Ambient = self.config["ThermoPlate"]["Pins"]["Ambient"]
      self.FireBox = self.config["ThermoPlate"]["Pins"]["FireBox"]
      self.WarmingBox = self.config["ThermoPlate"]["Pins"]["WarmingBox"]
      self.LeftBack = self.config["ThermoPlate"]["Pins"]["LeftBack"]
      self.RightBack = self.config["ThermoPlate"]["Pins"]["RightBack"]
      self.LeftFront = self.config["ThermoPlate"]["Pins"]["LeftFront"]
      self.RightFront = self.config["ThermoPlate"]["Pins"]["RightFront"]

      # Setup PiPlate Led Pin Variables for Status
      self.AmbientStatus = self.config["ThermoPlate"]["Status"]["Ambient"]
      self.FireBoxStatus = self.config["ThermoPlate"]["Status"]["FireBox"]
      self.WarmingBoxStatus = self.config["ThermoPlate"]["Status"]["WarmingBox"]
      self.LeftBackStatus = self.config["ThermoPlate"]["Status"]["LeftBack"]
      self.RightBackStatus = self.config["ThermoPlate"]["Status"]["RightBack"]
      self.LeftFrontStatus = self.config["ThermoPlate"]["Status"]["LeftFront"]
      self.RightFrontStatus = self.config["ThermoPlate"]["Status"]["RightFront"]

      # Setup Display Name Variables for Information
      self.AmbientDisplayText = self.config["ThermoPlate"]["DisplayText"]["Ambient"]
      self.FireBoxDisplayText = self.config["ThermoPlate"]["DisplayText"]["FireBox"]
      self.WarmingBoxDisplayText = self.config["ThermoPlate"]["DisplayText"]["WarmingBox"]
      self.LeftBackDisplayText = self.config["ThermoPlate"]["DisplayText"]["LeftBack"]
      self.RightBackDisplayText = self.config["ThermoPlate"]["DisplayText"]["RightBack"]
      self.LeftFrontDisplayText = self.config["ThermoPlate"]["DisplayText"]["LeftFront"]
      self.RightFrontDisplayText = self.config["ThermoPlate"]["DisplayText"]["RightFront"]

      # Load Device Mapping
      self.devicescache = []
      self.load_devicescache()

            # Telemetry Mapping
      self.interfaces_instances = {}
      self.capabilities_instances = {}
      self.map_telemetry = []
      self.load_map_telemetry()
      self.map_telemetry_devices = []
      self.map_telemetry_interfaces = []
      self.map_telemetry_interfaces_capabilities = []
      self.telemetry_msg = {}
      self.telemetry_dict = {}

      # meta
      self.application_uri = None
      self.namespace = None
      self.device_capability_model_id = None
      self.device_capability_model = []
      self.device_name_prefix = None
      self.ignore_interface_ids = []

      # Device Information
      self.devices_cache = []
      self.load_devicescache()

      # Azure Device
      self.device_client = None


    # -------------------------------------------------------------------------------
    #   Function:   run
    #   Usage:      The start function starts the OPC Server
    # -------------------------------------------------------------------------------
    async def run(self):

      msgCnt = 0

      # Set device client from Azure IoT SDK and connect
      device_client = None

      try:

        while True:
          
          GPIO.output(self.Wait, GPIO.HIGH)
          await asyncio.sleep(self.config["TelemetryFrequencyInSeconds"])

          msgCnt = msgCnt + 1

          GPIO.output(self.Wait, GPIO.LOW)
          GPIO.output(self.Good, GPIO.HIGH)

          print("[%s]: Reading Thermocoupler Values" % self.config["NameSpace"])

          # READ FIREBOX
          print("[%s]: Reading the FIRE BOX TEMPERATURE" % self.config["NameSpace"])
          DAQCPlate.setDOUTbit(self.DAQCPlate_addr, self.FireBoxStatus)
          self.TemperatureFireBox = ThermoPlate.getTEMP(self.ThermoPlate_addr, self.FireBox)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          DAQCPlate.clrDOUTbit(self.DAQCPlate_addr, self.FireBoxStatus)

          # READ WARMING BOX
          print("[%s]: Reading the WARMING BOX TEMPERATURE" % self.config["NameSpace"])
          DAQCPlate.setDOUTbit(self.DAQCPlate_addr, self.WarmingBoxStatus)
          self.TemperatureWarmingBox = ThermoPlate.getTEMP(self.ThermoPlate_addr, self.WarmingBox)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          DAQCPlate.clrDOUTbit(self.DAQCPlate_addr, self.WarmingBoxStatus)

          # READ LEFT BACK CHAMBER
          print("[%s]: Reading the LEFT BACK CHAMBER TEMPERATURE" % self.config["NameSpace"])
          DAQCPlate.setDOUTbit(self.DAQCPlate_addr, self.LeftBackStatus)
          self.TemperatureLeftBack = ThermoPlate.getTEMP(self.ThermoPlate_addr, self.LeftBack)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          DAQCPlate.clrDOUTbit(self.DAQCPlate_addr, self.LeftBackStatus)

          # READ RIGHT BACK CHAMBER
          print("[%s]: Reading the RIGHT BACK CHAMBER TEMPERATURE" % self.config["NameSpace"])
          DAQCPlate.setDOUTbit(self.DAQCPlate_addr, self.RightBackStatus)
          self.TemperatureRightBack = ThermoPlate.getTEMP(self.ThermoPlate_addr, self.RightBack)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          DAQCPlate.clrDOUTbit(self.DAQCPlate_addr, self.RightBackStatus)

          # READ LEFT FRONT CHAMBER
          print("[%s]: Reading the LEFT FRONT CHAMBER TEMPERATURE" % self.config["NameSpace"])
          DAQCPlate.setDOUTbit(self.DAQCPlate_addr, self.LeftFrontStatus)
          self.TemperatureLeftFront = ThermoPlate.getTEMP(self.ThermoPlate_addr, self.LeftFront)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          DAQCPlate.clrDOUTbit(self.DAQCPlate_addr, self.LeftFrontStatus)

          # READ RIGHT FRONT CHAMBER
          print("[%s]: Reading the RIGHT FRONT CHAMBER TEMPERATURE" % self.config["NameSpace"])
          DAQCPlate.setDOUTbit(self.DAQCPlate_addr, self.RightFrontStatus)
          self.TemperatureRightFront = ThermoPlate.getTEMP(self.ThermoPlate_addr, self.RightFront)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          DAQCPlate.clrDOUTbit(self.DAQCPlate_addr, self.RightFrontStatus)

          self.TemperatureAmbient = ThermoPlate.getTEMP(self.ThermoPlate_addr, self.Ambient, "f")

          table = Texttable()
          table.set_deco(Texttable.HEADER)
          table.set_cols_dtype(["t", "f", "f"])
          table.set_cols_align(["l", "r", "r"])
          table.add_rows([["Sensor Name",  "Temperature", "Last Temperature"],
                          [self.AmbientDisplayText, self.TemperatureAmbient, self.LastTemperatureAmbient],
                          [self.FireBoxDisplayText, self.TemperatureFireBox, self.LastTemperatureFireBox],
                          [self.WarmingBoxDisplayText, self.TemperatureWarmingBox, self.LastTemperatureWarmingBox],
                          [self.LeftBackDisplayText, self.TemperatureLeftBack, self.LastTemperatureLeftBack],
                          [self.RightBackDisplayText, self.TemperatureRightBack, self.LastTemperatureRightBack],
                          [self.LeftFrontDisplayText, self.TemperatureLeftFront, self.LastTemperatureLeftFront],
                          [self.RightFrontDisplayText, self.TemperatureRightFront, self.LastTemperatureRightFront]])


          print(table.draw())
          print("***")

          # Capture Last Values
          self.LastTemperatureAmbient = self.TemperatureAmbient
          self.LastTemperatureFireBox = self.TemperatureFireBox
          self.LastTemperatureWarmingBox = self.TemperatureWarmingBox
          self.LastTemperatureLeftBack = self.TemperatureLeftBack
          self.LastTemperatureRightBack = self.TemperatureRightBack
          self.LastTemperatureLeftFront = self.TemperatureLeftFront
          self.LastTemperatureRightFront = self.TemperatureLeftFront

          # Send Data to IoT Central
          for device in self.map_telemetry["Devices"]:

              if device_client == None:
                self.logger.info("[BBQ MONITOR] CONNECTING IOT CENTRAL: %s" % device_client)
                device_client = DeviceClient(self.logger, device["Name"])
                print(device_client)
                await device_client.connect()

              for interface in device["Interfaces"]:

                self.logger.info("[BBQ MONITOR] InterfacelId: %s" % interface["InterfacelId"])
                self.logger.info("[BBQ MONITOR] InterfaceInstanceName: %s" % interface["InterfaceInstanceName"])

                self.telemetry_dict = {}

                for capability in interface["Capabilities"]:

                  # Assign variable name and value to dictionary
                  if capability["Name"] == self.TemperatureAmbientMapName:
                    self.telemetry_dict[capability["Name"]] = self.TemperatureAmbient
                  elif capability["Name"] == self.TemperatureFireBoxMapName:
                    self.telemetry_dict[capability["Name"]] = self.TemperatureFireBox
                  elif capability["Name"] == self.TemperatureWarmingBoxMapName:
                    self.telemetry_dict[capability["Name"]] = self.TemperatureWarmingBox
                  elif capability["Name"] == self.TemperatureLeftBackMapName:
                    self.telemetry_dict[capability["Name"]] = self.TemperatureLeftBack
                  elif capability["Name"] == self.TemperatureRightBackMapName:
                    self.telemetry_dict[capability["Name"]] = self.TemperatureRightBack
                  elif capability["Name"] == self.TemperatureLeftFrontMapName:
                    self.telemetry_dict[capability["Name"]] = self.TemperatureLeftFront
                  elif capability["Name"] == self.TemperatureRightFrontMapName:
                    self.telemetry_dict[capability["Name"]] = self.TemperatureRightFront
                  else:
                    self.telemetry_dict[capability["Name"]] = 0
                  
                  self.logger.info("[BBQ MONITOR] DICTIONARY: %s" % self.telemetry_dict)

                self.logger.info("[BBQ MONITOR] SENDING PAYLOAD IOT CENTRAL")
                await device_client.send_telemetry(self.telemetry_dict, interface["InterfacelId"], interface["InterfaceInstanceName"])
                self.logger.info("[BBQ MONITOR] SUCCESS")

          GPIO.output(self.Good, GPIO.LOW)

        return

      except Exception as ex:
        self.logger.error("[ERROR] %s" % ex)
        self.logger.error("[TERMINATING] We encountered an error in BBQ Monitor Run::run()" )
      
      finally:
        await device_client.disconnect()

    # -------------------------------------------------------------------------------
    #   Function:   setup
    #   Usage:      The setup function preps the configuration for the BBQ Monitor
    # -------------------------------------------------------------------------------
    async def setup(self):

      try:

        print("[%s]: Setting up the BBQ Monitor" % self.config["NameSpace"])

        # --------------------------------------------------------
        # GPIO
        # --------------------------------------------------------
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # --------------------------------------------------------
        # Set Mode Leds (STATUS)
        # --------------------------------------------------------
        GPIO.setup(self.Alert, GPIO.OUT)
        GPIO.setup(self.Wait, GPIO.OUT)
        GPIO.setup(self.Good, GPIO.OUT)

        # Verbose
        self.logger.info("[{0}]: Alert Pin {1}".format(self.config["NameSpace"], self.config["Status"]["Pins"]["Alert"]))
        self.logger.info("[{0}]: Wait Pin {1}".format(self.config["NameSpace"], self.config["Status"]["Pins"]["Wait"]))
        self.logger.info("[{0}]: Good Pin {1}".format(self.config["NameSpace"], self.config["Status"]["Pins"]["Good"]))

        # --------------------------------------------------------
        # Set Temperature Scale
        # --------------------------------------------------------
        ThermoPlate.setSCALE(self.config["ThermoPlate"]["TemperatureScale"])

        # Verbose
        self.logger.info("[{0}]: ThermoPlate Temperature Scale {1}".format(self.config["NameSpace"], self.config["ThermoPlate"]["TemperatureScale"]))

      except Exception as ex:
        self.logger.error("[ERROR] %s" % ex)
        self.logger.error("[TERMINATING] We encountered an error in BBQ Monitor Setup::setup()" )

      print("[%s]: Completed setting up the BBQ Monitor" % self.config["NameSpace"])

      return

    # -------------------------------------------------------------------------------
    #   Function:   load_nodes_from_devicecache
    #   Usage:      The load_nodes_from_devicecache function enumerates the
    #               devicescache.json and creates a node for each kind of
    #               Iot Central Device. It looks at a Twin and registers all
    #               of the interfaces and for devices, registers the interface
    # -------------------------------------------------------------------------------
    async def load_nodes_from_devicecache(self):

      try:

        # Setup root for map telemetry configuration file
        self.logger.info("[BBQ MONITOR] INITIATED MAP TELEMETRY FILE: %s" % self.map_telemetry)
        self.map_telemetry = self.create_map_telemetry_root(self.config["NameSpace"])

        device_count = 0
        for device in self.devicescache["Devices"]:

          self.logger.info("[BBQ MONITOR] DEVICE TYPE: %s" % device["DeviceType"])
          self.logger.info("[BBQ MONITOR] DEVICE NAME: %s" % device["Name"])

          # Add the device info to the map telemetry file
          self.map_telemetry_devices.append(self.create_map_telemetry_device(device["Name"], device["DeviceType"], device["DeviceCapabilityModelId"]))
          self.logger.info("[BBQ MONITOR] ADDED DEVICE TO MAP TELEMETRY FILE: %s" % self.map_telemetry_devices)

          interface_count = 0
          for interface in device["Interfaces"]:

            # Add the interface info to the map telemetry file
            self.map_telemetry_interfaces.append(self.create_map_telemetry_interface(interface["Name"], interface["InterfacelId"], interface["InterfaceInstanceName"]))
            self.logger.info("[BBQ MONITOR] ADDED INTERFACE TO MAP TELEMETRY FILE: %s" % self.map_telemetry_interfaces)

            config_interface = [obj for obj in self.config["Interfaces"] if obj["InterfaceInstanceName"]==interface["InterfaceInstanceName"]]

            for capability in config_interface[0]["Capabilities"]:
              
              capability_type = capability["Type"]
              display_name = capability["DisplayName"]
              name = capability["Name"]
              
              range_value = None
              if capability["UseRangeValues"] == True:
                range_value = capability["RangeValues"][0]

              # Append the capabilties to the Interfaces collection for the map telemetry file
              self.map_telemetry_interfaces_capabilities.append(self.create_map_telemetry_variable(capability_type, display_name, name, capability["IoTCDataType"], capability["Frequency"], capability["OnlyOnValueChange"], capability["UseRangeValues"], capability["RangeValues"]))
              self.logger.info("[BBQ MONITOR] MAP TELEMETRY VARIABLES APPEND: %s" % self.map_telemetry_interfaces[interface_count])

            # Save the variables to the Map Telemetry [Interface] Collection
            self.map_telemetry_interfaces[interface_count]["Capabilities"] = self.map_telemetry_interfaces_capabilities
            self.logger.info("[BBQ MONITOR] MAP TELEMETRY INTERFACES APPEND: %s" % self.map_telemetry_interfaces[interface_count])
            interface_count = interface_count + 1
            self.map_telemetry_interfaces_capabilities = []

          # Append the Interfaces to the Devices collection for the map telemetry file
          self.map_telemetry_devices[device_count]["Interfaces"] = self.map_telemetry_interfaces
          device_count = device_count + 1
          self.map_telemetry_interfaces = []

        # Append the Devices to the Root collection for the map telemetry file
        self.map_telemetry["Devices"] = self.map_telemetry_devices
        self.logger.info("[BBQ MONITOR] MAP TELEMETRY: %s" % self.map_telemetry)
        self.update_map_telemetry()

      except Exception as ex:
        self.logger.error("[ERROR] %s" % ex)
        self.logger.error("[TERMINATING] We encountered an error in load_nodes_from_devicecache()")

      return

    # -------------------------------------------------------------------------------
    #   Function:   load_config
    #   Usage:      Loads the configuration from file
    # -------------------------------------------------------------------------------
    def load_config(self):

      config = Config(self.logger)
      self.config = config.data
      return

    # -------------------------------------------------------------------------------
    #   Function:   load_devicescache
    #   Usage:      Loads the Devices that have been registered and provisioned.
    #               This file is generated from the as-is state of the system
    #               when the OpcUaServer is started.
    # -------------------------------------------------------------------------------
    def load_devicescache(self):

      devicescache = DevicesCache(self.logger)
      self.devicescache = devicescache.data
      return

    # -------------------------------------------------------------------------------
    #   Function:   create_map_telemetry_root
    #   Usage:      Sets the root for the Map Telemetry configuration file
    # -------------------------------------------------------------------------------
    def create_map_telemetry_root(self, NameSpace):
      mapTelemetry = {
        "NameSpace": NameSpace,
        "Created": str(datetime.datetime.now()),
        "Devices": [
        ]
      }
      return mapTelemetry

    # -------------------------------------------------------------------------------
    #   Function:   create_map_telemetry_device
    #   Usage:      Adds a device to the map telemetry configuration file
    # -------------------------------------------------------------------------------
    def create_map_telemetry_device(self, Name, ModelType, DeviceCapabilityModelId):
      mapTelemetry = {
        "Name": Name,
        "ModelType": ModelType,
        "DeviceCapabilityModelId": DeviceCapabilityModelId,
        "Interfaces": [
        ]
      }
      return mapTelemetry

    # -------------------------------------------------------------------------------
    #   Function:   create_map_telemetry_interface
    #   Usage:      Sets the node for the Map Telemetry configuration file
    # -------------------------------------------------------------------------------
    def create_map_telemetry_interface(self, Name, InterfacelId, InterfaceInstanceName):
      mapTelemetry = {
        "Name": Name,
        "InterfacelId": InterfacelId,
        "InterfaceInstanceName": InterfaceInstanceName,
        "Variables":[
        ]
      }
      return mapTelemetry

    # -------------------------------------------------------------------------------
    #   Function:   create_map_telemetry_variable
    #   Usage:      Sets the variable for the Map Telemetry configuration file
    # -------------------------------------------------------------------------------
    def create_map_telemetry_variable(self, Type, DisplayName, Name, IoTCDataType, Frequency, OnlyOnValueChange, UseRangeValues, RangeValues):
      mapTelemetry = {
        "Type": Type,
        "DisplayName": DisplayName,
        "Name": Name,
        "IoTCDataType": IoTCDataType,
        "Frequency": Frequency,
        "OnlyOnValueChange": OnlyOnValueChange,
        "UseRangeValues": UseRangeValues,
        "RangeValueCount": len(RangeValues),
        "RangeValueCurrent": 1,
        "RangeValues": RangeValues
      }
      return mapTelemetry

    # -------------------------------------------------------------------------------
    #   Function:   update_map_telemetry
    #   Usage:      Saves the generated Map Telemetry File
    # -------------------------------------------------------------------------------
    def update_map_telemetry(self):
      map_telemetry_file = MapTelemetry(self.logger)
      map_telemetry_file.update_file(self.map_telemetry)
      return

    # -------------------------------------------------------------------------------
    #   Function:   load_map_telemetry
    #   Usage:      Loads the Map Telemetry File that Maps Telemtry for Azure
    #               Iot Central
    # -------------------------------------------------------------------------------
    def load_map_telemetry(self):

      # Load all the map
      map_telemetry = MapTelemetry(self.logger)
      map_telemetry.load_file()
      self.map_telemetry = map_telemetry.data
      return

