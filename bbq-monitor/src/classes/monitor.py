# ==================================================================================
#   File:   monitor.py
#   Author: Larry W Jordan Jr (larouex@gmail.com)
#   Use:    This class will create and instance of the BBQ Monitor and start the
#           monitoring loop
#
#   Online: https://github.com/LarouexSoftwareDesign/Yoder
#
#   (c) 2020 Larouex Software Design LLC
#   This code is licensed under MIT license (see LICENSE.txt for details)
# ==================================================================================
import json, sys, time, string, threading, asyncio, os, copy, datetime
import logging

# Pi Plates
import piplates.DAQCplate as daqc_plate
import piplates.THERMOplate as thermo_plate
import RPi.GPIO as GPIO

# from prettytable import PrettyTable
from texttable import Texttable

# our classes
from Classes.config import Config

class Monitor():

    def __init__(self, Log):
      self.logger = Log

      # Load configuration
      self.config = []
      self.load_config()

      # --------------------------------------------------------
      # Plate Addresses
      # --------------------------------------------------------
      self.thermo_plate_addr = 0
      self.daqc_plate_addr = 1

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

      self.node_instances = {}
      self.variable_instances = {}

      # Telemetry Mapping
      self.map_telemetry = []
      self.map_telemetry_devices = []
      self.map_telemetry_interfaces = []
      self.map_telemetry_interfaces_variables = []

      # meta
      self.application_uri = None
      self.namespace = None
      self.device_capability_model_id = None
      self.device_capability_model = []
      self.device_name_prefix = None
      self.ignore_interface_ids = []

    # -------------------------------------------------------------------------------
    #   Function:   run
    #   Usage:      The start function starts the OPC Server
    # -------------------------------------------------------------------------------
    async def run(self):

      msgCnt = 0

      try:

        while True:
          await asyncio.sleep(self.config["ServerFrequencyInSeconds"])

          GPIO.output(self.Wait, GPIO.HIGH)
          msgCnt = msgCnt + 1

          print("[%s]: Reading Thermocoupler Values" % self.config["NameSpace"])

          # READ FIREBOX
          print("[%s]: Reading the FIRE BOX TEMPERATURE" % self.config["NameSpace"])
          daqc_plate.setDOUTbit(self.daqc_plate_addr, self.FireBoxStatus)
          self.TemperatureFireBox = thermo_plate.getTEMP(self.thermo_plate_addr, self.FireBox)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          daqc_plate.clrDOUTbit(self.daqc_plate_addr, self.FireBoxStatus)

          # READ WARMING BOX
          print("[%s]: Reading the WARMING BOX TEMPERATURE" % self.config["NameSpace"])
          daqc_plate.setDOUTbit(self.daqc_plate_addr, self.WarmingBoxStatus)
          self.TemperatureWarmingBox = thermo_plate.getTEMP(self.thermo_plate_addr, self.WarmingBox)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          daqc_plate.clrDOUTbit(self.daqc_plate_addr, self.WarmingBoxStatus)

          # READ LEFT BACK CHAMBER
          print ("Reading the LEFT BACK CHAMBER TEMPERATURE...")
          daqc_plate.setDOUTbit(self.daqc_plate_addr, self.LeftBackStatus)
          self.TemperatureLeftBack = thermo_plate.getTEMP(self.thermo_plate_addr, self.LeftBack)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          daqc_plate.clrDOUTbit(self.daqc_plate_addr, self.LeftBackStatus)

          # READ RIGHT BACK CHAMBER
          print ("Reading the RIGHT BACK CHAMBER TEMPERATURE...")
          daqc_plate.setDOUTbit(self.daqc_plate_addr, self.RightBackStatus)
          self.TemperatureRightBack = thermo_plate.getTEMP(self.thermo_plate_addr, self.RightBack)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          daqc_plate.clrDOUTbit(self.daqc_plate_addr, self.RightBackStatus)

          # READ LEFT FRONT CHAMBER
          print ("Reading the LEFT FRONT CHAMBER TEMPERATURE...")
          daqc_plate.setDOUTbit(self.daqc_plate_addr, self.LeftFrontStatus)
          self.TemperatureLeftFront = thermo_plate.getTEMP(self.thermo_plate_addr, self.LeftFront)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          daqc_plate.clrDOUTbit(self.daqc_plate_addr, self.LeftFrontStatus)

          # READ RIGHT FRONT CHAMBER
          print ("Reading the RIGHT FRONT CHAMBER TEMPERATURE...")
          daqc_plate.setDOUTbit(self.daqc_plate_addr, self.RightFrontStatus)
          self.TemperatureRightFront = thermo_plate.getTEMP(self.thermo_plate_addr, self.RightFront)
          await asyncio.sleep(self.config["ReadTimeBetweenTemperatureInSeconds"])
          daqc_plate.clrDOUTbit(self.daqc_plate_addr, self.RightFrontStatus)

          self.TemperatureAmbient = thermo_plate.getTEMP(self.thermo_plate_addr, self.Ambient, "f")

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
          self.TemperatureAmbient = self.LastTemperatureAmbient
          self.TemperatureFireBox = self.LastTemperatureFireBox
          self.TemperatureWarmingBox = self.LastTemperatureWarmingBox
          self.TemperatureLeftBack = self.LastTemperatureLeftBack
          self.TemperatureRightBack = self.LastTemperatureRightBack
          self.TemperatureLeftFront = self.LastTemperatureLeftFront
          self.TemperatureRightFront = self.LastTemperatureRightFront

        return

      except Exception as ex:
        self.logger.error("[ERROR] %s" % ex)
        self.logger.error("[TERMINATING] We encountered an error in BBQ Monitor Run::run()" )


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
        self.logger.info("[%s]: Alert Pin %s" % self.config["NameSpace"], self.config["Status"]["Pins"]["Alert"])
        self.logger.info("[%s]: Wait Pin %s" % self.config["NameSpace"], self.config["Status"]["Pins"]["Wait"])
        self.logger.info("[%s]: Good Pin %s" % self.config["NameSpace"], self.config["Status"]["Pins"]["Good"])

        # --------------------------------------------------------
        # Set Temperature Scale
        # --------------------------------------------------------
        thermo_plate.setSCALE(self.config["ThermoPlate"]["TemperatureScale"])

        # Verbose
        self.logger.info("[%s]: ThermoPlate Temperature Scale %s" % self.config["NameSpace"], self.config["ThermoPlate"]["TemperatureScale"])

      except Exception as ex:
        self.logger.error("[ERROR] %s" % ex)
        self.logger.error("[TERMINATING] We encountered an error in BBQ Monitor Setup::setup()" )

      print("[%s]: Completed setting up the BBQ Monitor" % self.config["NameSpace"])

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