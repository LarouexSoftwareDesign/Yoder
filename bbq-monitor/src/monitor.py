#!/home/Larouex/Python
# ==================================================================================
#   File:   monitor.py
#   Author: Larry W Jordan Jr (larouex@gmail.com)
#   Use:    Creates an instance of the BBQ Monitor
#
#   Online: https://github.com/LarouexSoftwareDesign/Yoder
#
#   (c) 2020 Larouex Software Design LLC
#   This code is licensed under MIT license (see LICENSE.txt for details)
# ==================================================================================
import  getopt, sys, time, string, threading, asyncio, os
import logging as Log

# our classes
from classes.monitor import Monitor
from classes.config import Config

# -------------------------------------------------------------------------------
#   Setup the BBQ Monitor
# -------------------------------------------------------------------------------
async def setup_bbq_monitor(BBQMonitor):

  try:

    Log.info("[SETUP] setup_bbq_monitor...")
    return await BBQMonitor.setup()

  except Exception as ex:
    Log.error("[ERROR] %s" % ex)
    Log.error("[TERMINATING] We encountered an error in [setup_bbq_monitor]" )
    return

# -------------------------------------------------------------------------------
#   Load the Devices previously registered and provisioned and set to Namespaces
#   for Device or Twin when browsing
# -------------------------------------------------------------------------------
async def load_nodes_from_devicecache(BBQMonitor):

  try:

    Log.info("[LOAD] load_nodes_from_devicecache...")
    return await BBQMonitor.load_nodes_from_devicecache()

  except Exception as ex:
    Log.error("[ERROR] %s" % ex)
    Log.error("[TERMINATING] We encountered an error in [load_nodes_from_devicecache]" )
    return

# -------------------------------------------------------------------------------
#   Start the BBQ Monitor Telemetry Loop
# -------------------------------------------------------------------------------
async def run_bbq_monitor(BBQMonitor):

  try:

    Log.info("[RUN] run_bbq_monitor...")
    return await BBQMonitor.run()

  except Exception as ex:
    Log.error("[ERROR] %s" % ex)
    Log.error("[TERMINATING] We encountered an error in [run_bbq_monitor]" )

# -------------------------------------------------------------------------------
#   main()
# -------------------------------------------------------------------------------
async def main(argv):

  # execution state from args
  short_options = "hvd"
  long_options = ["help", "verbose", "debug"]
  full_cmd_arguments = sys.argv
  argument_list = full_cmd_arguments[1:]
  try:
    arguments, values = getopt.getopt(argument_list, short_options, long_options)
  except getopt.error as err:
    print (str(err))

  for current_argument, current_value in arguments:

    if current_argument in ("-h", "--help"):
      print("------------------------------------------------------------------------------------------------------------------------------------------")
      print("HELP for monitor.py")
      print("------------------------------------------------------------------------------------------------------------------------------------------")
      print("")
      print("  BASIC PARAMETERS...")
      print("")
      print("  -h or --help - Print out this Help Information")
      print("  -v or --verbose - Debug Mode with lots of Data will be Output to Assist with Debugging")
      print("  -d or --debug - Debug Mode with lots of DEBUG Data will be Output to Assist with Tracing and Debugging")
      print("------------------------------------------------------------------------------------------------------------------------------------------")
      return

    if current_argument in ("-v", "--verbose"):
      Log.basicConfig(format="%(levelname)s: %(message)s", level = Log.INFO)
      Log.info("Verbose Logging Mode...")
    else:
      Log.basicConfig(format="%(levelname)s: %(message)s")

    if current_argument in ("-d", "--debug"):
      Log.basicConfig(format="%(levelname)s: %(message)s", level = Log.DEBUG)
      Log.info("Debug Logging Mode...")
    else:
      Log.basicConfig(format="%(levelname)s: %(message)s")

  # Configure
  bbq_monitor = Monitor(Log)
  await setup_bbq_monitor(bbq_monitor)
  Log.info("[SERVER] Instance Info (bbq_monitor): %s" % bbq_monitor)

  # Load the meta-data and map OPC-UA to IoTC Interfaces
  await load_nodes_from_devicecache(bbq_monitor)

  # Start the loop
  await run_bbq_monitor(bbq_monitor)

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
