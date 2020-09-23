# Saluminator “BBQ Monitor” Internet of Things (IoT) Appliance

That is a big title! It describes the cool things that the device does. Here is a list of features…

- Monitor 6 different zones in your BBQ
- You set the frequency to capture the temperature readings
- Transmit the telemetry to the cloud for visualizations, cook history and analysis
- Set the baseline temperature variance for each zone
- Configure rules and alerts that are triggered by your variance settings
- Load the telemetry from a previous cook to set variances
- Mobile monitoring and notifications
- Alexa integration “Alexa, what are the temperatures at BBQ Monitor #1?”

Let’s talk about the design and details. From here on out, we will refer to our hardware appliance as teh <b>“BBQ Monitor”</b>.

The BBQ Monitor was designed to be open sourced and shared as a DIY project that most electromnic hobbiests or software developer can do. That said, maybe not all of the harder bits like CNC’n the project case, power-coating, soldering and labeling... and if that is help you need, we do offer up pieces you want from a kit that span all the way from the indiviudal boards to a fully completed appliance that we will ship to you. The BBQ Monitor is an advanced piece of kit and you need some software chops in order to bring the whole thing together. We will do our very best to explain things and be accurate in the details.

Raspberry Pi Pinout Schematic for Yoder:
![alt text](./Assets/pi-pin-schematic.png "Raspberry Pi Pinout Schematic for Yoder")

Pi-EZConnect Hat Pinout Schematic for Yoder:
![alt text](./Assets/pi-ezconnect-hat.png "Pi-EZConnect Hat Pinout Schematic for Yoder")

Pi-Plates THERMOplate Pinout Schematic for Yoder:
![alt text](./Assets/pi-plates-THERMOplate.png "Pi-Plates THERMOplate Pinout Schematic for Yoder")

Lora Phat for Node:
![alt text](./Assets/lora-phat-node-pi-supply.png "Lora Phat for Node")

```
GPIO
-----------------------------------------------------------------------------------------------------------------------
| 2     4     6     8    10     12    14    16    18    20    22    24    26    28    30    32    34    36    38    40 |
|5V     5V    GND   #    #      o     GND   o     o     GND   o     o     o     #     GND   o     GND   o     o     o  |
|3V3    #     #     #     GND   #     o     o     3V3   o     o     o     GND   #     o     o     o     o     #     GND|
| 1     3     5     7     9     11    13    15    17    19    21    23    25    27    29    31    33    35    37    39 |
-----------------------------------------------------------------------------------------------------------------------
```

# Used

```
o Available

3 SDA1 I2C connected to JP1
5 SCL1 I2C connected to JP1
7 GPIO 4 connected to JP1
8 Tx Connects to Rx on RAK811 module
10 Rx Connects to Tx on RAK811 module
11 GPIO 17 Reset pin
27 ID SD EEPROM
28 ID SC EEPROM
37 ID WP EEPROM

GPS I2C
--------------------------------
| 1     2     3     4     5    |
|VCC    SDA  SCL  GPIO4   GND  |
--------------------------------
This is the same as the first 5 pins from 3v3 to GND on the Raspberry Pi

RAK811 Breakout U$3
---------------------------------------------------------------
| 1     2     3     4     5     6     7     8     9     10    |
|3V3   PA13  PA14  PA15  PB3   PB5   PB8   PB9   PA2   GND    |
---------------------------------------------------------------
```

Sensor Box Pinout Schematic for Yoder:
![alt text](./Assets/sensor-breakout-box.png "Sensor Box Pinout Schematic for Yoder")
