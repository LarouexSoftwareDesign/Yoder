# BBQ Monitor Software Overview

## Setting up Your Development Toolchain
The code in this repository depends on Visual Studio Code and Python.

### Your Local Machine

The development "toolchain" refers to all of the various tools, SDK's and bits we need to install on your machine to facilitate a smooth experience developing our project. Our main development tool will be Visual Studio code. 

This project was developed on Python version 3.8.5 and you should be using the latest version of Python as certain libraries like asyncio may not work in older versions.


| - | Install These Tools |
|---|---|
| ![Python](../Img/python-icon-100.png) | [LINK: Python 3 Installation Page](https://www.python.org/downloads/) - Python is the programming language we will use to build our applications. |
| ![Visual Studio Code](../Img/vs-code-icon-100.png) | [LINK: Visual Studio Code Installation Page](https://code.visualstudio.com/download) - Visual Studio Code is a lightweight but powerful source code editor which runs on your desktop and is available for Windows, macOS and Linux. This is the IDE we will use to write code and deploy to the our BLE Devices and the Raspberry Pi Gateway.  |

### Install all the Tools for Visual Studio Code
These are a set of tools we will use to develop our apps. You can open the Extensions sidebar with "Shift+Ctrl+X) or click the icon in the side navigator bar.

![alt text](../Img/vs-code-python-sml.png "VS Code Python")


### Clone this project "BBQ Monitor Software"...
Find a working folder for this project on your machine...
````bash
git clone https://github.com/LarouexSoftwareDesign/Yoder.git
cd Yoder
cd bbq-monitor
cd src
pip3 install -r requirements.txt
````

Open the "src" folder in Visual Studio Code.


## SECRETS!!! - Azure Connectivity and Protecting Your Secrets
### THIS SECTION IS OPTIONAL AND IS INCLUDED AS A "BEST PRACTICE" FOR HANDLING SECRETS FOR AZURE IOT CENTRAL CONNECTIONS
<b>NOTE:</b> You can skip this section if you do not plan to use Azure Key Vault to store and retrieve connection secrets. [Click here to jump to the section: I don't want to use Key Vault](#i-dont-want-to-use-key-vault)

Azure IoT Central is used for our telemetry, visualizations and managing devices. It is a powerful SaaS offering and we will be using the tools and visualizations to build out a rich application for our scenario. In order to connect our devices and gateway to IoT Central, we need to manage a set of secrets that we need to protect I highly recomnmend that you store those secrets in Azure Key Vault and that you do this so as not to make a mistake and expose access to your application, gateway or devices.

I am going to assume the following when we work with Azure and Azure Portal...

* That you already have an Azure Account (If you don't, get started here [LINK: Create your Azure free account today](https://azure.microsoft.com/en-us/free/)
* That you have sufficient permissions in your Azure account to create Resource Groups and assolciated resources
* That you are familiar creating and using resources with the Azure CLI or the Azure Portal [LINK: Azure Portal](https://portal.azure.com/)

### Create our Connection Secrets...
| Name | Secret (IoT Central Admin [Device Connection] Page)  | Content Type |
|---|---|---|
| larouex-industrial-manufacturing-scopeid | Admin, Device Connection, Copy [ID scope] | Client Secret |
| larouex-industrial-manufacturing-saskey-device-primary | Admin, Device Connection, Devices, View Keys, Copy [Primary Key] | Client Secret |
| larouex-industrial-manufacturing-saskey-device-secondary | Admin, Device Connection, Devices, View Keys, Copy [Secondary Key] | Client Secret |
| larouex-industrial-manufacturing-saskey-gateway-primary | Admin, Device Connection, Azure Edge devices, View Keys, Copy [Primary Key] | Client Secret |
| larouex-industrial-manufacturing-saskey-gateway-secondary | Admin, Device Connection, Azure Edge devices, View Keys, Copy [Secondary Key] | Client Secret |

Once these are all created in Key Vault, your list should look like this...
![alt text](../Img/azure-portal-key-vault-secrets-list.png "Azure Portal Key Vault Secrets List") 

https://docs.microsoft.com/en-us/azure/key-vault/certificates/quick-create-python

## Get Your Credentials for Azure Login
<b>NOTE:</b> You can skip this section if you do not plan to use Azure Key Vault to Store and Access secrets.

* Open a Terminal or Powershell session
* Login to the Azure CLI...

````bash
az login
````

* If the CLI can open your default browser, it will do so and load an Azure sign-in page.
* Otherwise, open a browser page at https://aka.ms/devicelogin and enter the authorization code displayed in your terminal.
* Sign in with your account credentials in the browser.

````bash
az ad sp create-for-rbac --name http://larouex-industrial-manufacturing --skip-assignment
````

````json
{
  "appId": "<your appID>",
  "displayName": "larouex-industrial-manufacturing",
  "name": "http://larouex-industrial-manufacturing",
  "password": "<your password>",
  "tenant": "<your tenant>"
}
````

````bash
az keyvault set-policy --name <your key vault url> --spn <your password> --secret-permissions get set list delete backup recover restore purge
````

## Configure our Secrets for Local Development
There is a file in the root folder of the project named "secrets_template.json" and this file outlines the shape of Json we use to retreive secrets. It supports Local Secrets and Key Vault usage. Copy the "secrets_template.json" to a new file named "secrets.json" in the root folder of the project. Open this file in Visual Studio Code and let's start configuring the options.

<b>IMPORTANT: Make sure to check your .gitignore to verify that "secrets.json" is in the list so it does not get checked in! The file should be dithered in your Visual Studio Code Explorer window.</b>


### I want to use the security and awesomeness of Key Vault!
See the Json below the bullets for reference...

* Set "UseKeyVault" to true
* From the Azure Portal, Goto your Key Vault Resource
* Goto Secrets
* Click onto your secret for Scope ID that we set up previously
* Click the copy button next to the "Secret Identifier"
* Paste it into the "KeyVaultUri" in the "secrets.json" file.
* Highlight and cut the remainder of url after .../secrets/ 
* Paste into the ScopeId field
* Repeat for all the secrets we setup previously and put into the right fields!

<b>Your file should look like this when completed...</b>

```` json
{
  "UseKeyVault": true,
  "ProvisioningHost": "global.azure-devices-provisioning.net",
  "LocalSecrets": {
    "ScopeId": "",
    "DeviceConnect":{
      "SaSKeys":{
          "Primary": "",
          "Secondary": ""
      }
    },
    "GatewayConnect":{
      "SaSKeys":{
          "Primary": "",
          "Secondary": ""
      }
    }
  },
  "KeyVaultSecrets":{
    "KeyVaultUri": "<Your Key Vault UIR>",
    "TenantId":"<Your Tenant ID>",
    "ClientId":"<Your Client ID>",
    "ClientSecret":"<Your Client Secret>",
    "ScopeId": "larouex-industrial-manufacturing-scopeid",
    "DeviceConnect":{
      "SaSKeys":{
          "Primary": "larouex-industrial-manufacturing-saskey-device-primary",
          "Secondary": "larouex-industrial-manufacturing-saskey-device-secondary"
      }
    },
    "GatewayConnect":{
      "SaSKeys":{
          "Primary": "larouex-industrial-manufacturing-saskey-gateway-primary",
          "Secondary": "larouex-industrial-manufacturing-saskey-gateway-secondary"
      }
    }
  }
}
````
Save the file and you can ignore the "LocalSecrets" section.

### I don't want to use Key Vault!
If you are working locally and do not want to implement the security and awesomeness of Key Vault, then go ahead and set "UseKeyVault" to false and fillout the section "LocalSecrets" with all our your SaS key values from the Admin, Device Connection page in IoT Central...

````json
{
  "UseKeyVault": false,
  "ProvisioningHost": "global.azure-devices-provisioning.net",
  "LocalSecrets": {
    "ScopeId": "<Your Scope ID from IoT Central Device Connect Page>",
    "DeviceConnect":{
      "SaSKeys":{
          "Primary": "<Your Primary Key from IoT Central Device Connect Page>",
          "Secondary": "<Your Secondary Key from IoT Central Device Connect Page>"
      }
    },
    "GatewayConnect":{
      "SaSKeys":{
          "Primary": "<Your Gateway Primary Key from IoT Central Device Connect Page>",
          "Secondary": "<Your Gateway Secondary Key from IoT Central Device Connect Page>"
      }
    }
  },
  "KeyVaultSecrets":{
    "KeyVaultUri": "",
    "TenantId":"",
    "ClientId":"",
    "ClientSecret":"",
    "ScopeId": "",
    "DeviceConnect":{
      "SaSKeys":{
          "Primary": "",
          "Secondary": ""
      }
    },
    "GatewayConnect":{
      "SaSKeys":{
          "Primary": "",
          "Secondary": ""
      }
    }
  }
}
````
Save the file and you can ignore the "KeyVaultSecrets" section.

## Provisioning our BBQ Monitor as a Device in Azure IoT Central
Provisioning is factored into a "stand-alone" operation. 

There are excellent tutorials on connecting devices to IoT Central and using Device Provisioning Services online and we won't try to repeat that here. If you are not familiar, take a break and visit these topics...

* [LINK: Get connected to Azure IoT Central](https://docs.microsoft.com/en-us/azure/iot-central/core/concepts-get-connected)
* [LINK: Tutorial: Create and connect a client application to your Azure IoT Central application (Python)](https://docs.microsoft.com/en-us/azure/iot-central/core/tutorial-connect-device-python)

Provisioning in our Gateway project is one of key pillars of capabilities we have created and we have lots of options so you can try the various Gateway scenarios. Let's look at all the options by runnning with --help...

````bash
python3 ./provisiondevices.py -h
````

<b>Output</b>
````bash
  HELP for provisiondevices.py
  ------------------------------------------------------------------------------------------------------------------
  -h or --help - Print out this Help Information
  -v or --verbose - Verbose Mode with lots of INFO will be Output to Assist with Tracing and Debugging
  -d or --debug - Debug Mode with lots of DEBUG Data will be Output to Assist with Tracing and Debugging
  -w or --whatif - Combine with Verbose it will Output the Configuration sans starting the Server
  -i or --iddevice - This ID will get appended to your Device. Example "001" = larouex-industrial-manufacturing-001
  ------------------------------------------------------------------------------------------------------------------
````

You will see a lot of useful information that will "play back" all of the actions that will be taken when provisioning the OPC Server as a device in our IoT Central Application. Lot's of options to test and see how our device will end up in Azure IoT Central, let's actually provision our Device now...

````bash
python3 ./provisiondevices.py -v -i "001"
````

You will get simliar verbose output to the What If scenario we ran previously along with this confirmation...

````bash
...
WARNING: [PROVISIONING] larouex-industrial-manufacturing-001
INFO: Updated Devices Cache file:
````

This is the data that will be written to our "devicescache.json" for the device information reflecting our OPC Server...

````json
  {
    "DeviceName": "larouex-industrial-manufacturing-001",
    "DeviceCapabilityModelId": "urn:LarouexIndustrialManufacturing:Server:1",
    "Interfaces": [
      {
        "Name": "Ambient",
        "InterfacelId": "urn:larouexindustrialmanufacturing:AmbientInterface:1",
        "InterfaceInstanceName": "AmbientInterface"
      },
      {
        "Name": "Process",
        "InterfacelId": "urn:larouexindustrialmanufacturing:ProcessInterface:1",
        "InterfaceInstanceName": "ProcessInterface"
      }
    ],
    "LastProvisioned": "2020-08-04 14:22:06.216106"
  }
 ````

This is the secret data that will be written to our "secrets.json" for the device connectivity reflecting our OPC Server details to connect to Azure IoT Central...

````json
  "Devices": [
    {
      "Name": "larouex-industrial-manufacturing-001",
      "AssignedHub": "-- hidden assigned-hub --",
      "DeviceSymmetricKey": "-- hidden device-symmetric-key --"
    }
  ]
````

## The BBQ Monitor Device is Provisioned!

![alt text](../Img/azure-iotc-provisioned-device-1.png "Device Provisioned")

