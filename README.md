## WebSDN 
WebSDN is an implementation of a SDN network controller in Ryu connected with a dedicated web interface for visualizing the connections and the traffic of the available switches. 

## Repository structure ## 
The repositoriy contains scripts and files for different functions of webSDN:
- `src\` contains the source code for the implementation of the Ryu controller and the web interface. 
    - `controller.py` is the python implementation of the SDN controller.
    - `NetworkLayout.py` is the source code of the data structure used by `controller.py` to take track of the network layout and status. 
    - `NetworkLayoutParser.py` is used to convert the NetworkLayout class to a json format. 
    - `webapp.py` is the implementation of the web interface in dash.
    - `assets/` contains contains the stylesheef, the javascript funzions and the icons used for the frontend.
- `mininet/` contains some examples for network layouts useful for testing the behaviour of the application.
- `mininet_run.sh` is a convenience script useful for atomating the launch of a mininet network for testing purposes. 
- `application.py`, the python scripts which launchs the entire application. 

## How to run ##
To execute webSDN correctly some python dependencies are required:
```
ryu
dash
dash_cytoscape
dash_ag_grid
dash_draggables
networkx
```

All of them can be installed using pip3 command:
```
pip3 install ryu dash dash_cytoscape dash_ag_grid dash_draggables networkx
```
> [!IMPORTANT]
> In distribution like Arch Linux or NixOS the installation of python dependency can be made only trought python virtual environments or custom methods.
> Take note that the Ryu library is actually deprecated and there are problems during the compilation of the source code.
> For this motivation is it recommended to use distribution like Ubuntu 20.04 with virtual environments (see testing environment section).

To run the application is only necessary to clone the repository and run the file `application.py`, which launchs automatically all modules:
```
python3 application.py
```
After webSDN starts, the webapp will be available on the HTTP port 8050 at the addess `http:\\127.0.0.1:8050`.
## Testing environment ##
During the development process a virtualbox VM based on comnetsemu was used. It is possible to retrieve the .ova image from [this link](https://www.granelli-lab.org/researches/relevant-projects/comnetsemu-labs), which shows also how to run the virtual image using multipass. 

There is also the possibility to use vagrant to create an up to date virtual environment by folloging the official method for [comnetsemu](https://git.comnets.net/public-repo/comnetsemu#installation).

> [!NOTE]
> The virtualbox OVA contains python dependencies which are not updated to the last version. For this motivation is recommended to upgrade python packages to guarantee that the dash webapp runs correctly, or at least the typing_extensions package:
> ```
> pip3 install --upgrade typing_extensions
> ```

The VM image have also mininet preinstalled, useful for testing SDN switches in an emulated network. The repository contains also a convenience script used for launching a custom network layout specified in the folder `mininet/` in a simple way:
```
./mininet_run topology_loop.py
```
This script launches an interactive shell with mininet. To use mininet and webSDN at the same time with the VM is it recommended to open an SSH port and create two sessions (one for mininet and one for the application). 

![Port forwarding in Virtualbox](docs/ports.png)