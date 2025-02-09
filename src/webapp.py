import dash
import dash_cytoscape as cyto
from dash import html, Input, Output, callback, dcc
import dash_ag_grid as dag
import dash_draggable as draggable

import requests

class PortStatisticsDescriptor():
    def __init__(self):
        self.RXPkts=0
        self.TXPkts=0
        self.RXBytes=0
        self.TXBytes=0

class SwitchDescriptor():
    def __init__(self):
        self.portIDs=None                                     
        self.portMACs=None                                  
        self.portStats=None                            
        self.portConfigs=None                              
        self.portStatistics=None                              
        self.portSpeeds=None    

        self.protocol=""                   
        self.datapathID=""      
        self.switchCapabilities=""

class HostDescriptor():
    def __init__(self):
        self.MAC=""      
        self.IPv4=""  
        self.IPv6=""  

class LinkDescriptor():
    def __init__(self):
        self.type=""
        self.device1=""
        self.device2=""
        self.deviceMAC1=""
        self.deviceMAC2=""
        self.linkStatus=""

class NetworkDescriptor():
    def __init__(self):
        self.hosts=[]
        self.switches=[]
        self.links=[]
    def getSwitchPortFromMAC(self,macAddress):
        for switch in self.switches:
            for portIndex in range(len(switch.portMACs)):
                if switch.portMACs[portIndex]==macAddress:
                    return switch.portIDs[portIndex]
        return None

networkDescription=NetworkDescriptor()

app = dash.Dash(__name__,external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"])

deviceListColumnDefs = [
    {"field":"Device"},
    {"field":"Connected with"},
    {"field":"Link status"},
]
deviceDetailsColumnDefs= [
    {"field":"Details"},
]


app.layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                dag.AgGrid(
                    id="deviceListGrid",
                    columnSize="sizeToFit",
                    rowData=[],
                    columnDefs=deviceListColumnDefs,
                    style={"width":"100%","height":"100%"}
                ),
            ],id="deviceListDiv"),
            html.Div([],id="hBar"),
            html.Div([
                dag.AgGrid(
                    id="deviceDetailsGrid",
                    columnSize="sizeToFit",
                    rowData=[],
                    columnDefs=deviceDetailsColumnDefs,
                    style={"width":"100%","height":"100%"}
                ),
            ],id="deviceDetailsDiv"),
        ],id="detailsDiv"),
        html.Div([],id="vBar"),
        html.Div([
            html.Div([
                html.Button([
                    html.I(className="fa-solid fa-arrow-left", id="fullscreenIcon")
                ], id="fullscreenButton", n_clicks=0),
                html.H1("SDN Network Layout",id="topBarText"),
            ],id="topBarDiv"), 
            html.Div([
                cyto.Cytoscape(
                id="topology",
                style={"width":"100%","height":"100%"},
                elements=[],
                layout={'name': 'circle'},
                stylesheet=[
                    {"selector": 'node', "style": {"content": "data(label)", "background-color": "#0074D9"}},
                    {"selector": 'edge', "style": {"line-color": "#FF4136"}}
                    ])
            ],id="topologyDiv"), 
        ],id="rightDiv"), 
    ],id="contentsDiv"),
    dcc.Interval(id="interval-component", interval=5000, n_intervals=0),
],id="pageDiv")

@app.callback(
    [Output("deviceListGrid", "rowData"),
     Output("topology", "elements"),],
    [Input("interval-component", "n_intervals")]
)

def update_device_grids(n):
    try:
        # Richiesta API Flask per ottenere lo stato della rete
        response = requests.get("http://localhost:5000/network_status")
        data = response.json()
        networkDescription.switches.clear()
        networkDescription.hosts.clear()
        networkDescription.links.clear()

        for switch in data["switches"]:
            newSwitch=SwitchDescriptor()
            newSwitch.datapathID=switch["datapathID"]
            newSwitch.protocol=switch["protocol"]
            newSwitch.portIDs=switch["portIDs"]
            newSwitch.portMACs=switch["portMACs"]
            newSwitch.portStats=switch["portStats"]
            newSwitch.portSpeeds=switch["portSpeeds"]
            newSwitch.portStatistics=[]
            for port in switch["portStatistics"]:
                newPortStatistics=PortStatisticsDescriptor()
                newPortStatistics.RXBytes=port["RXBytes"]
                newPortStatistics.TXBytes=port["TXBytes"]
                newPortStatistics.RXPkts=port["RXPkts"]
                newPortStatistics.TXPkts=port["TXPkts"]
                newSwitch.portStatistics.append(newPortStatistics)
            networkDescription.switches.append(newSwitch)

        for host in data["hosts"]:
            newHost=HostDescriptor()
            newHost.MAC=host["MAC"]
            newHost.IPv4=host["IPv4"]
            newHost.IPv6=host["IPv6"]
            networkDescription.hosts.append(newHost)

        for link in data["links"]:
            newLink=LinkDescriptor()
            newLink.type=link["type"]
            newLink.linkStatus=link["linkStatus"]
            if newLink.type=="SS":
                newLink.device1=link["switch1"]
                newLink.device2=link["switch2"]
                newLink.deviceMAC1=link["switchMAC1"]
                newLink.deviceMAC2=link["switchMAC2"]
            else:
                newLink.device1=link["host"]
                newLink.device2=link["switch"]
                newLink.deviceMAC1=link["host"]
                newLink.deviceMAC2=link["switchMACPort"]
            networkDescription.links.append(newLink)
        
        linkTableElements=[]
        for link in networkDescription.links:
            if link.type=="SS":
                linkTableElements.append({
                    "Device":"Switch "+str(link.device1)+ " port "+str(networkDescription.getSwitchPortFromMAC(link.deviceMAC1)),
                    "Connected with":"Switch "+str(link.device2)+" port "+str(networkDescription.getSwitchPortFromMAC(link.deviceMAC2)),
                    "Link status":link.linkStatus,
                })
            else:
                linkTableElements.append({
                    "Device":"Host "+str(link.device1),
                    "Connected with":"Switch "+str(link.device2)+" port "+str(networkDescription.getSwitchPortFromMAC(link.deviceMAC2)),
                    "Link status":link.linkStatus,
                })
        topologyNodes=[]
        topologyEdges=[]
        for switch in networkDescription.switches:
            topologyNodes.append({
                'data': {'id': str(switch.datapathID), 'label': str(switch.datapathID)},
                'classes': 'switch-node'
            })
        for host in networkDescription.hosts:
            topologyNodes.append({
                'data': {'id': str(host.MAC), 'label': str(host.MAC)},
                'classes': 'switch-node'
            })
        for link in networkDescription.links:
            topologyEdges.append({
                'data': {'source': str(link.device1), 'target': str(link.device2)}
            })
        return linkTableElements,topologyNodes+topologyEdges
    except Exception as e:
        print(f"Errore nel caricamento dei dati: {str(e)}")
        return [],[]
if __name__ == '__main__':
    app.run_server(debug=True)