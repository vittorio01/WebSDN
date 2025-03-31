import dash
import dash_cytoscape as cyto
from dash import html, Input, Output, callback, dcc, State
import dash_ag_grid as dag
import dash_draggable as draggable

import requests
import json

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
        self.flows=[]

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

class selectedDetailsDevice():
    def __init__ (self):
        self.deviceType = None 
        self.deviceId = None 

networkDescription = NetworkDescriptor()
selectedDevice = selectedDetailsDevice()

app = dash.Dash(__name__,external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"])

deviceListColumnDefs = [
    {"field":"Device"},
    {"field":"Connected with"},
    {"field":"Link Status"},
]
deviceDetailsColumnDefs= [
    {"field":"Device Attribute"},
    {"field":"Value"},
]
switchFlowTableColumnDefs= [
    {"field":"Port In"},
    {"field":"Source"},
    {"field":"Destination"},
    {"field":"Protocol"},
    {"field":"Operation"},
]


app.layout = html.Div([
    dcc.Store(id="stored-elements", data=[]),
    dcc.Store(id="grid-update-trigger", data=0),
    html.Div([
        html.Div([
            html.Div([
                dag.AgGrid(
                    id="deviceListGrid",
                    columnSize="sizeToFit",
                    rowData=[],
                    columnDefs=deviceListColumnDefs,
                    style={"width":"100%","height":"100%"},
                ),
            ],id="deviceListDiv"),
            html.Div([],className="hBar",id="hBar1"),
            html.Div([
                dag.AgGrid(
                    id="deviceDetailsGrid",
                    columnSize="sizeToFit",
                    rowData=[],
                    columnDefs=deviceDetailsColumnDefs,
                    rowClassRules={
                        'bold-row': 'params.data["Device Attribute"] === "Port Number"',
                    },
                    style={"width":"100%","height":"100%"},
                ),
            ],id="deviceDetailsDiv"),
        ],id="detailsDiv"),
        html.Div([],id="vBar"),
        html.Div([
            html.Div([
                html.Button([
                    html.I(className="fa-solid fa-table-list", id="detailsIcon")
                ], id="detailsButton",className="topBarButton-active", n_clicks=0),
                html.Button([
                    html.I(className="fa-solid fa-table", id="flowTableIcon")
                ], id="flowTableButton",className="topBarButton-active", n_clicks=0),
                html.H1("SDN Network Layout",id="topBarText"),
            ],id="topBarDiv"), 
            html.Div([
                cyto.Cytoscape(
                id="topology",
                style={"width":"100%","height":"100%"},
                elements=[],
                layout={'name': 'concentric',
                        'minNodeSpacing': 80,
                        },
                zoom=1,
                pan={"x": 0, "y": 0},
                stylesheet=[
                    {"selector": 'node', "style": {
                        "width": "35px",
                        "height": "35px",
                        "shape":"rectangle",
                        "background-fit": "cover",
                        "background-image": "data(image)",
                        "background-opacity":0,
                        "label": "data(label)",
                        "font-size": "10px",
                        "text-valign": "bottom",
                        "text-halign": "center",
                        "text-background-color": "#F5F3F5",  
                        "text-background-opacity": 0.9,  
                        "background-color": "transparent",  
                        "border-width": "0px",
                        "border-color": "#000"}
                    },
                    {"selector": 'edge', "style": {
                        "line-color": "#gray",
                        "width":"1.5px"                        
                        }
                    },
                    {
                        "selector": ".host-node",
                        "style": {
                            "background-image": "/assets/host-icon.png"
                        }
                    },
                    {
                        "selector": ".switch-node",
                        "style": {
                            "background-image": "/assets/switch-icon.png"
                        }
                    }
                    ],
                zoomingEnabled=True,  # Disabilita zoom
                userPanningEnabled=True,  # Disabilita pan
                userZoomingEnabled=True,  # Disabilita zoom con la rotella del mouse
                boxSelectionEnabled=False,  # Disabilita la selezione dei nodi tramite il box di selezione
                autounselectify=False,  # Non permette la selezione di nodi (anche se cliccati)
                ),
            ],id="topologyDiv"),
            html.Div([],className="hBar",id="hBar2"), 
            html.Div([
                dag.AgGrid(
                    id="switchFlowTableGrid",
                    columnSize="sizeToFit",
                    rowData=[],
                    columnDefs=switchFlowTableColumnDefs,
                    style={"width":"100%","height":"100%"},
                ),
                dcc.Store(id="grid-scroll-position", data=0),
            ],id="switchFlowTableDiv"),
            

        ],id="rightDiv"), 
    ],id="contentsDiv"),
    dcc.Interval(id="interval-component", interval=5000, n_intervals=0),
],id="pageDiv")


@app.callback(
    [Output("deviceListGrid", "rowData"),
     Output("topology", "elements"),
     Output("topology", "zoom"),
     Output("topology", "pan"),
     Output("stored-elements", "data"),
     Output("grid-update-trigger", "data")],
    [Input("interval-component", "n_intervals")],
    [State("topology", "zoom"),
     State("topology", "pan"),
     State("stored-elements", "data"),
     State("grid-update-trigger", "data")]
)

def update_device_grids(n,current_zoom, current_pan,previous_elements,trigger):
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
            newSwitch.flows=switch['flows']
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
                    "Link Status":link.linkStatus,
                })
            else:
                linkTableElements.append({
                    "Device":"Host "+str(link.device1),
                    "Connected with":"Switch "+str(link.device2)+" port "+str(networkDescription.getSwitchPortFromMAC(link.deviceMAC2)),
                    "Link Status":link.linkStatus,
                })
        topologyNodes=[]
        topologyEdges=[]
        for switch in networkDescription.switches:
            topologyNodes.append({
                'data': {'id': str(switch.datapathID), 'label': "Switch "+str(switch.datapathID)},
                'classes': 'switch-node',
            })
        for host in networkDescription.hosts:
            topologyNodes.append({
                'data': {'id': str(host.MAC), 'label': "Host "+str(host.MAC)},
                'classes': 'host-node',
            })
        for link in networkDescription.links:
            link_status = "solid" if link.linkStatus == "Link Up" else "dashed"
            topologyEdges.append({
                'data': {'source': str(link.device1), 'target': str(link.device2)},
                'style': {
                    'line-color': '#gray',
                    'width': '1.5px',
                    'line-style': link_status 
                }
            })


        new_elements = topologyNodes + topologyEdges
        if json.dumps(new_elements, sort_keys=True) == json.dumps(previous_elements, sort_keys=True):
            return linkTableElements, dash.no_update, current_zoom, current_pan, previous_elements, trigger + 1
        return linkTableElements, new_elements, current_zoom, current_pan, new_elements, trigger + 1
    except Exception as e:
        print(f"Errore nel caricamento dei dati: {str(e)}")
        return [], [], 1, {"x": 0, "y": 0}, [], dash.no_update

def newline_renderer(params):
    # Sostituisce \n con <br> per i ritorni a capo
    if params.value:
        return params.value.replace("\n", "<br>")  # Sostituisci \n con <br>
    return ""
 

@app.callback(
    [Output("deviceDetailsGrid", "rowData"),
     Output("switchFlowTableGrid", "rowData"),
     Output("grid-scroll-position", "data")],
    [Input("topology", "selectedNodeData"),
     Input("deviceListGrid", "cellClicked"),
     Input("grid-update-trigger", "data"),
     Input("deviceDetailsGrid", "rowData")],
    [State("grid-scroll-position", "data")]
)
def update_device_details_grid(selected_nodes, cell, trigger, current_details,scroll_position):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update, scroll_position 

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "grid-update-trigger":
        if selectedDevice.deviceId and selectedDevice.deviceType:
            new_details = updateDetails(selectedDevice.deviceType, selectedDevice.deviceId)
            if new_details == current_details:
                return dash.no_update,dash.no_update, scroll_position
            return new_details, scroll_position

    elif trigger_id == "topology":
        if selected_nodes:
            node_data = selected_nodes[0]
            node_id = node_data["id"]
            node_label = node_data["label"]
            if "Switch" in node_label:
                deviceType = "Switch"
            elif "Host" in node_label:
                deviceType = "Host"
            else:
                return dash.no_update, dash.no_update, scroll_position
            new_details = updateDetails(deviceType, node_id)
            if new_details == current_details:
                return dash.no_update,dash.no_update, scroll_position
            return new_details, scroll_position

    elif trigger_id == "deviceListGrid":
        if cell:
            value = cell.get("value", "N/A")
            col_name = cell.get("colId", "Unknown Column")
            if col_name != "Link Status" and value != "N/A":
                valueStrings = value.split()
                deviceType = " ".join(valueStrings[:1])
                deviceID = " ".join(valueStrings[1:2])
                new_details = updateDetails(deviceType, deviceID)
                if new_details == current_details:
                    return dash.no_update,dash.no_update,  scroll_position
                return new_details, scroll_position

    return dash.no_update, dash.no_update, scroll_position 

def updateDetails(deviceType,deviceID):
    if deviceType == "Switch":
        for switch in networkDescription.switches:
            if str(switch.datapathID)==deviceID:
                details = [
                    {"Device Attribute": "Datapath ID","Value": str(switch.datapathID)},
                    {"Device Attribute": "Protocol","Value": str(switch.protocol)},
                    {"Device Attribute": "Capabilities","Value": str(switch.switchCapabilities)},
                ]
                flowTable= []
                for flow in switch.flows:
                    flowTable.append([{
                        "Port In":flow['portIn'],
                        "Source":str(flow['sourceIP']+"("+flow['sourceMAC']+")"),
                        "Destination":str(flow['destinationIP']+"("+flow['destinationMAC']+")"),
                        "Protocol":flow['protocol'],
                        "Operation":flow['operation'],
                    }])
                for portIndex in range(len(switch.portIDs)):
                    details.append({"Device Attribute": "Port Number", "Value": str(switch.portIDs[portIndex])})
                    details.append({"Device Attribute": "MAC address", "Value": switch.portMACs[portIndex]})
                    details.append({"Device Attribute": "State", "Value": switch.portStats[portIndex]})
                    details.append({"Device Attribute": "Speed", "Value": str(switch.portSpeeds[portIndex])+" bit/s"})
                    details.append({"Device Attribute": "Packets sent", "Value": str(switch.portStatistics[portIndex].TXPkts)+" pkts ("+str(switch.portStatistics[portIndex].TXBytes)+" bytes)"})
                    details.append({"Device Attribute": "Packets received", "Value": str(switch.portStatistics[portIndex].RXPkts)+" pkts ("+str(switch.portStatistics[portIndex].RXBytes)+" bytes)"})
                selectedDevice.deviceId=deviceID 
                selectedDevice.deviceType=deviceType
                return details,flowTable
    elif deviceType == "Host":
        for host in networkDescription.hosts:
            if host.MAC==deviceID:
                details = [
                    {"Device Attribute": "MAC address", "Value": host.MAC},
                    {"Device Attribute": "IPv4", "Value": host.IPv4},
                    {"Device Attribute": "IPv6", "Value": host.IPv6},
                ]
                selectedDevice.deviceId=deviceID 
                selectedDevice.deviceType=deviceType
                return details, []
    return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True)