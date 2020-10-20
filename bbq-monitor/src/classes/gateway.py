# ==================================================================================
#   File:   gateway.py
#   Author: Larry W Jordan Jr (larouex@gmail.com)
#   Use:    Gateway acts a Client to the OPC Server and Handles Protocol
#           translation to Azure IoT Central
#
#   Online: https://github.com/LarouexSoftwareDesign/Yoder
#
#   (c) 2020 Larouex Software Design LLC
#   This code is licensed under MIT license (see LICENSE.txt for details)    
# ==================================================================================
import json, sys, time, string, threading, asyncio, os, copy
import logging

# opcua
from asyncua import Client, Node, ua

# uses the Azure IoT Device SDK for Python (Native Python libraries)
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
from azure.iot.device import MethodResponse

# our classes
from Classes.config import Config
from Classes.secrets import Secrets
from Classes.maptelemetry import MapTelemetry
from Classes.varianttype import VariantType
from Classes.deviceclient import DeviceClient
from Classes.devicescache import DevicesCache

class Gateway():
    
    def __init__(self, Log, WhatIf):
      self.logger = Log
      self.whatif = WhatIf

      # load up configuration and mapping files
      self.config = []
      self.nodes = []
      self.load_config()

      # Device Information
      self.devices_cache = []
      self.load_devicescache()

      # Map Telemetry
      self.map_telemetry = []
      self.load_map_telemetry()
      self.telemetry_msg = {}
      self.telemetry_dict = {}

      # Azure Device
      self.device_client = None

    # -------------------------------------------------------------------------------
    #   Function:   run
    #   Usage:      The start function loads configuration and starts the OPC Server
    # -------------------------------------------------------------------------------
    async def run(self):

      # Gateway Loop
      try:

        # configure the endpoint
        url = self.config["ClientUrlPattern"].format(port = self.config["Port"])
        self.logger.info("[GATEWAY] SEEKING ENDPOINT %s" % url)

        async with Client(url=url) as client:

          while True:

            await asyncio.sleep(self.config["ClientFrequencyInSeconds"])

            for device in self.map_telemetry["Devices"]:

              # Set device client from Azure IoT SDK and connect
              device_client = DeviceClient(self.logger, device["Name"])
              print(device_client)
              await device_client.connect()
              self.logger.info("[GATEWAY] CONNECTING IOT CENTRAL: %s" % device_client)

              for interface in device["Interfaces"]:

                self.logger.info("[GATEWAY] InterfacelId: %s" % interface["InterfacelId"])
                self.logger.info("[GATEWAY] InterfaceInstanceName: %s" % interface["InterfaceInstanceName"])

                self.telemetry_dict = {}

                for variable in interface["Variables"]:

                  read_node = client.get_node(variable["NodeId"])
                  val = await read_node.get_value()
                  log_msg = "[GATEWAY] TELEMETRY: *NAME: {tn} *VALUE: {val} *NODE ID: {ni} *DISPLAY NAME: {dn}"
                  self.logger.info(log_msg.format(tn = variable["TelemetryName"], val = val, ni = variable["NodeId"], dn = variable["DisplayName"]))

                  # Assign variable name and value to dictionary
                  self.telemetry_dict[variable["TelemetryName"]] = val
                  self.logger.info("[GATEWAY] DICTIONARY: %s" % self.telemetry_dict)

                self.logger.info("[GATEWAY] SENDING PAYLOAD IOT CENTRAL")
                await device_client.send_telemetry(self.telemetry_dict, interface["InterfacelId"], interface["InterfaceInstanceName"])
                self.logger.info("[GATEWAY] SUCCESS")
                await device_client.disconnect()
                await asyncio.sleep(3)

      except Exception as ex:
        self.logger.error("[ERROR] %s" % ex)
        self.logger.error("[TERMINATING] We encountered an error in Gateway" )
        return 999

      finally:
          await client.disconnect()
          self.device_client = None
          #self.device_client.disconnect()
          return 0

      return 0

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
    #   Function:   load_map_telemetry
    #   Usage:      Loads the Map Telemetry File that Maps Telemtry for Azure
    #               Iot Central to the Node Id's for the Opc Server.
    # -------------------------------------------------------------------------------
    def load_map_telemetry(self):

      # Load all the map
      map_telemetry = MapTelemetry(self.logger)
      map_telemetry.load_file()
      self.map_telemetry = map_telemetry.data
      return
