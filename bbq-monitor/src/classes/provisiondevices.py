
# ==================================================================================
#   File:   provisiondevices.py
#   Author: Larry W Jordan Jr (larouex@gmail.com)
#   Use:    Provisions Devices and updates cache file and do device provisioning
#           via DPS for IoT Central
#
#   Online: https://github.com/LarouexSoftwareDesign/Yoder
#
#   (c) 2020 Larouex Software Design LLC
#   This code is licensed under MIT license (see LICENSE.txt for details)
# ==================================================================================
import time, logging, string, json, os, binascii, struct, threading, asyncio, datetime

# Sur classes
from classes.devicescache import DevicesCache
from classes.secrets import Secrets
from classes.symmetrickey import SymmetricKey
from classes.config import Config

# uses the Azure IoT Device SDK for Python (Native Python libraries)
from azure.iot.device.aio import ProvisioningDeviceClient

# -------------------------------------------------------------------------------
#   ProvisionDevices Class
# -------------------------------------------------------------------------------
class ProvisionDevices():

    timer = None
    timer_ran = False
    dcm_value = None

    def __init__(self, Log, Id, InFileName, ModelType, NumberOfDevices):

      self.logger = Log
      self.id_device = Id
      self.in_file_name = InFileName
      self.model_type = ModelType
      self.number_of_devices = NumberOfDevices

      # Load the configuration file
      self.config = {}
      self.load_config()

      # Symmetric Key
      self.symmetrickey = SymmetricKey(self.logger)

      # Secrets
      self.secrets = Secrets(self.logger)
      self.secrets_cache_data = self.secrets.data

      # meta
      self.application_uri = None
      self.namespace = None
      self.device_capability_model_id = None
      self.device_capability_model = []
      self.device_name_prefix = None
      self.ignore_interface_ids = []

      # Devices Cache
      self.devices_cache = DevicesCache(self.logger)
      self.devices_cache_data = self.devices_cache.data
      self.devices_to_provision = []


    # -------------------------------------------------------------------------------
    #   Function:   provision_devices
    #   Usage:      Iterates through all of the nodes in config.json and will create
    #               a provisioning call to associated a device template to the node
    #               interface based on the twin, device or gateway pattern
    # -------------------------------------------------------------------------------
    async def provision_devices(self):

      # First up we gather all of the needed provisioning meta-data and secrets
      try:

        for pattern in self.config["IoTCentralPatterns"]:
          if pattern["ModelType"] == self.model_type:
            self.namespace = pattern["NameSpace"]
            self.device_capability_model_id = pattern["DeviceCapabilityModelId"]
            self.device_name_prefix = pattern["DeviceNamePrefix"]
            self.ignore_interface_ids = pattern["IgnoreInterfaceIds"]
            break

        # this is our working cache for things we provision in this session
        self.devices_to_provision = self.create_devices_to_provision()

        # Specific string formatting based on the device-model-type
        if self.model_type == "Twins":
          self.twins_create()
        elif self.model_type == "Gateways":
          self.gateways_create()
        elif self.model_type == "Devices":
          self.devices_create()

        print("********************************")
        print("DEVICES TO PROVISION: %s" % self.devices_to_provision)
        print("********************************")

        # Update or Append new Records to the Devices Cache
        found_device = False
        for device_to_provision in self.devices_to_provision["Devices"]["Devices"]:
          index = 0
          for devices_cache in self.devices_cache_data["Devices"]:
            found_device = False
            if devices_cache["Name"] == device_to_provision["Name"]:
              self.devices_cache_data["Devices"][index] = device_to_provision
              found_device = True
              break
            else:
              index = index + 1
          if found_device == False:
            self.devices_cache_data["Devices"].append(device_to_provision)


        # Update or Append new Records to the Secrets
        found_secret = False
        for device_to_provision in self.devices_to_provision["Secrets"]:

          # Azure IoT Central SDK Call to create the provisioning_device_client
          provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
            provisioning_host = self.secrets.get_provisioning_host(),
            registration_id = device_to_provision["Name"],
            id_scope = self.secrets.get_scope_id(),
            symmetric_key = device_to_provision["DeviceSymmetricKey"],
            websockets=True
          )

          # Azure IoT Central SDK call to set the DCM payload and provision the device
          provisioning_device_client.provisioning_payload = '{"iotcModelId":"%s"}' % (device_to_provision["DeviceCapabilityModelId"])
          registration_result = await provisioning_device_client.register()
          self.logger.info("[REGISTRATION RESULT] %s" % registration_result)
          self.logger.info("[device_symmetrickey] %s" % device_to_provision["DeviceSymmetricKey"])
          device_to_provision["AssignedHub"] = registration_result.registration_state.assigned_hub

          index = 0
          for secrets_cache in self.secrets_cache_data["Devices"]:
            found_secret = False
            if secrets_cache["Name"] == device_to_provision["Name"]:
              self.secrets_cache_data["Devices"][index] = device_to_provision
              found_secret = True
              break
            else:
              index = index + 1
          if found_secret == False:
            self.secrets_cache_data["Devices"].append(device_to_provision)

        print("********************************")
        print("DEVICES TO PROVISION: %s" % self.devices_to_provision)
        print("********************************")

        self.devices_cache.update_file(self.devices_cache_data)
        self.secrets.update_file_device_secrets(self.secrets_cache_data["Devices"])
        return

      except Exception as ex:
        self.logger.error("[ERROR] %s" % ex)
        self.logger.error("[TERMINATING] We encountered an error in CLASS::ProvisionDevices::provision_devices()" )

    # -------------------------------------------------------------------------------
    #   Function:   load_config
    #   Usage:      Loads the configuration
    # -------------------------------------------------------------------------------
    def load_config(self):

      config = Config(self.logger)
      self.config = config.data
      return

    # -------------------------------------------------------------------------------
    #   Function:   twins_create
    #   Usage:      Returns a a Twin pattern for Devices and Secrets
    # -------------------------------------------------------------------------------
    def twins_create(self):

      try:

        # We will iterate the number of devices we are going to create
        for x in range(self.number_of_devices):

          # Define the Device iteration suffix, it is
          # the base passed number with leading zeros for
          # a legnth of 3 (1-999) devices
          id_number_str = str(int(self.id_device) + x)
          id_number_str = id_number_str.zfill(3)

          device_name = self.device_name_prefix.format(id=id_number_str)

          # The Device Asset scenario appends one interfaces per device id
          device_capability_model = self.create_device_capability_model(device_name, self.device_capability_model_id)

          # Let's Look at the config file and generate
          # our device from the interfaces configuration
          for node in self.config["Interfaces"]:

            # check if we are excluding the interface?
            if self.ignore_interface_ids.count(node["InterfacelId"]) == 0:
              device_capability_model["Interfaces"].append(self.create_device_interface(node["Name"], node["InterfacelId"], node["InterfaceInstanceName"]))

          self.devices_to_provision["Devices"]["Devices"].append(device_capability_model)
          self.devices_to_provision["Secrets"].append(self.create_device_connection(device_name, self.device_capability_model_id))

      except Exception as ex:
        self.logger.error("[ERROR] %s" % ex)
        self.logger.error("[TERMINATING] We encountered an error in CLASS::ProvisionDevices::devices_create()" )

      return

    # -------------------------------------------------------------------------------
    #   Function:   gateways_create
    #   Usage:      Returns a a Gateway pattern for Devices and Secrets
    # -------------------------------------------------------------------------------
    def gateways_create(self):

      try:

        # Let's Look at the config file and generate
        # our device from the interfaces configuration
        for node in self.config["Nodes"]:

          device_capability_model_id = self.device_capability_model_id.format(interfaceName=node["Name"])

          # check if we are excluding the interface?
          if self.ignore_interface_ids.count(node["InterfacelId"]) == 0:

            # We will iterate the number of devices we are going to create
            for x in range(self.number_of_devices):

              # Define the Device iteration suffix, it is
              # the base passed number with leading zeros for
              # a legnth of 3 (1-999) devices
              id_number_str = str(int(self.id_device) + x)
              id_number_str = id_number_str.zfill(3)

              device_name = self.device_name_prefix.format(nodeName=node["Name"], id=id_number_str)

              # The Device Asset scenario appends one interfaces per device id
              device_capability_model = self.create_device_capability_model(device_name, device_capability_model_id)
              device_capability_model["Interfaces"].append(self.create_device_interface(node["Name"], node["InterfacelId"], node["InterfaceInstanceName"]))

              self.devices_to_provision["Devices"]["Devices"].append(device_capability_model)
              self.devices_to_provision["Secrets"].append(self.create_device_connection(device_name, device_capability_model_id))

      except Exception as ex:
        self.logger.error("[ERROR] %s" % ex)
        self.logger.error("[TERMINATING] We encountered an error in CLASS::ProvisionDevices::devices_create()" )

      return

    # -------------------------------------------------------------------------------
    #   Function:   devices_create
    #   Usage:      Returns a Device Interface for Interfaces Array
    # -------------------------------------------------------------------------------
    def devices_create(self):

      try:

        # Let's Look at the config file and generate
        # our device from the interfaces configuration
        for node in self.config["Nodes"]:

          device_capability_model_id = self.device_capability_model_id.format(interfaceName=node["Name"])

          # check if we are excluding the interface?
          if self.ignore_interface_ids.count(node["InterfacelId"]) == 0:

            # We will iterate the number of devices we are going to create
            for x in range(self.number_of_devices):

              # Define the Device iteration suffix, it is
              # the base passed number with leading zeros for
              # a legnth of 3 (1-999) devices
              id_number_str = str(int(self.id_device) + x)
              id_number_str = id_number_str.zfill(3)

              device_name = self.device_name_prefix.format(nodeName=node["Name"], id=id_number_str)

              # The Device Asset scenario appends one interfaces per device id
              device_capability_model = self.create_device_capability_model(device_name, device_capability_model_id)
              device_capability_model["Interfaces"].append(self.create_device_interface(node["Name"], node["InterfacelId"], node["InterfaceInstanceName"]))

              self.devices_to_provision["Devices"]["Devices"].append(device_capability_model)
              self.devices_to_provision["Secrets"].append(self.create_device_connection(device_name, device_capability_model_id))

      except Exception as ex:
        self.logger.error("[ERROR] %s" % ex)
        self.logger.error("[TERMINATING] We encountered an error in CLASS::ProvisionDevices::devices_create()" )

      return

    # -------------------------------------------------------------------------------
    #   Function:   create_devices_to_provision
    #   Usage:      Returns a Devices Array
    # -------------------------------------------------------------------------------
    def create_devices_to_provision(self):
      newDeviceToProvisionArray = {
        "Devices": {
          "Devices": [
          ]
        }
        ,
        "Secrets": [
        ]
      }
      return newDeviceToProvisionArray

    # -------------------------------------------------------------------------------
    #   Function:   create_device_capability_model
    #   Usage:      Returns a Device Interface with the  Interfaces Array
    # -------------------------------------------------------------------------------
    def create_device_capability_model(self, DeviceName, DeviceCapabilityModelId):
      newDeviceCapabilityModel = {
        "Name": DeviceName,
        "DeviceType": self.model_type,
        "DeviceCapabilityModelId": DeviceCapabilityModelId,
        "Interfaces": [
        ],
        "LastProvisioned": str(datetime.datetime.now())
      }
      return newDeviceCapabilityModel

    # -------------------------------------------------------------------------------
    #   Function:   create_device_interface
    #   Usage:      Returns a Device Interface for Interfaces Array
    # -------------------------------------------------------------------------------
    def create_device_interface(self, name, Id, instantName):
      newInterface = {
        "Name": name,
        "InterfacelId": Id,
        "InterfaceInstanceName": instantName
      }
      return newInterface

    # -------------------------------------------------------------------------------
    #   Function:   create_device_connection
    #   Usage:      Returns a Device Interface for Interfaces Array
    # -------------------------------------------------------------------------------
    def create_device_connection(self, Name, DeviceCapabilityModelId):

      # Get device symmetric key
      device_symmetric_key = self.symmetrickey.compute_derived_symmetric_key(Name, self.secrets.get_device_secondary_key())

      newDeviceSecret = {
        "Name": Name,
        "DeviceCapabilityModelId": DeviceCapabilityModelId,
        "DeviceType": self.model_type,
        "AssignedHub": "",
        "DeviceSymmetricKey": device_symmetric_key,
        "LastProvisioned": str(datetime.datetime.now())
      }
      return newDeviceSecret

