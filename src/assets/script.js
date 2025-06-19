//scripts that defines the behaviour for dragging the corners and redimensioning the tables.

document.addEventListener("DOMContentLoaded", function() {
    const observer = new MutationObserver(function(mutations) {
        let hBar = document.getElementById("hBar1");
        let hBar2 = document.getElementById("hBar2");
        let vBar = document.getElementById("vBar");
        let detailsDiv = document.getElementById("detailsDiv");
        let rightDiv = document.getElementById("rightDiv");
        let topologyDiv = document.getElementById("topologyDiv");
        let topBarDiv=document.getElementById("topBarDiv");
        let deviceListDiv = document.getElementById("deviceListDiv");
        let deviceDetailsDiv = document.getElementById("deviceDetailsDiv");
        let switchFlowTableDiv = document.getElementById("switchFlowTableDiv");
        let deviceListGrid = document.getElementById("deviceListGrid");
        let deviceDetailsGrid = document.getElementById("deviceDetailsGrid");
        let detailsButton = document.getElementById("detailsButton");
        let flowTableButton = document.getElementById("flowTableButton");
        
        if (hBar && vBar && hBar2 && flowTableButton && switchFlowTableDiv && hBar2  && deviceListGrid && deviceDetailsGrid  && detailsDiv  && rightDiv  && topologyDiv  && topBarDiv  && deviceListDiv  && deviceDetailsDiv  && switchFlowTableDiv) {
            hBar.addEventListener("mousedown", (e) => {
                document.addEventListener("mousemove", resizeHorizontal);
                document.addEventListener("mouseup", () => {
                    document.removeEventListener("mousemove", resizeHorizontal);
                }, { once: true });
            });
            hBar2.addEventListener("mousedown", (e) => {
                document.addEventListener("mousemove", resizeHorizontal2);
                document.addEventListener("mouseup", () => {
                    document.removeEventListener("mousemove", resizeHorizontal2);
                }, { once: true });
            });
            vBar.addEventListener("mousedown", (e) => {
                document.addEventListener("mousemove", resizeVertical);
                document.addEventListener("mouseup", () => {
                    document.removeEventListener("mousemove", resizeVertical);
                }, { once: true });
            });
            detailsButton.addEventListener("click", function() {
                toggleDetails();
            });
            flowTableButton.addEventListener("click", function() {
                toggleFlowTable();
            });
            observer.disconnect();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
});

//Resize for vertical corner
function resizeVertical(e) {
    let detailsDiv = document.getElementById("detailsDiv");
    let rightDiv = document.getElementById("rightDiv");
    let newValueLeft=(e.clientX-detailsDiv.getBoundingClientRect().left);
    let newValueRight=(rightDiv.parentElement.getBoundingClientRect().width - e.clientX);
    if (newValueRight > 500 && (newValueLeft > 300)) {
        detailsDiv.style.width = newValueLeft + "px";
        rightDiv.style.width = newValueRight + "px";
    }
}

//Resize for the second horizontal corner
function resizeHorizontal2(e) {
    let switchFlowTableDiv = document.getElementById("switchFlowTableDiv");
    let topologyDiv = document.getElementById("topologyDiv");
    let newValueTop=(e.clientY - topologyDiv.getBoundingClientRect().top);
    let newValueBottom=(switchFlowTableDiv.parentElement.getBoundingClientRect().height + topologyDiv.getBoundingClientRect().top - e.clientY );
    if (newValueTop > 60 && newValueBottom > 60) {
        topologyDiv.style.height = newValueTop + "px";
        switchFlowTableDiv.style.height = newValueBottom + "px";
    }

}

//Resize for the first horizontal corner

function resizeHorizontal(e) {
    let deviceListDiv = document.getElementById("deviceListDiv");
    let deviceDetailsDiv = document.getElementById("deviceDetailsDiv");
    let newValueTop=(e.clientY - deviceListDiv.getBoundingClientRect().top);
    let newValueBottom=(deviceDetailsDiv.parentElement.getBoundingClientRect().height + deviceListDiv.getBoundingClientRect().top - e.clientY );
    if (newValueTop > 60 && newValueBottom > 60) {
        deviceListDiv.style.height = newValueTop + "px";
        deviceDetailsDiv.style.height = newValueBottom + "px";
    }
}

//Behavuour for toggling the details button
function toggleDetails() {
    let detailsDiv = document.getElementById("detailsDiv");
    let rightDiv = document.getElementById("rightDiv");
    let originalDetailsTransition=detailsDiv.style.transition;
    let originalRightTransition=rightDiv.style.transition;
    detailsDiv.style.transition = "width 0.5s ease-in-out";
    rightDiv.style.transition = "width 0.5s ease-in-out";
    if (detailsButton.className == 'topBarButton') {
        detailsDiv.style.width = "40%";
        rightDiv.style.width="60%";
        detailsButton.className = 'topBarButton-active';

    } else {
        detailsDiv.style.width = "0%";
        rightDiv.style.width="100%";
        detailsButton.className = 'topBarButton';
    }
    setTimeout(function() {
        rightDiv.style.transition = originalRightTransition;
        detailsDiv.style.transition = originalDetailsTransition; 
    }, 500); 
}

//Behavuour for toggling the flow table button
function toggleFlowTable() {
    let switchFlowTableDiv = document.getElementById("switchFlowTableDiv");
    let topologyDiv = document.getElementById("topologyDiv");
    let originalFlowTableTransition=detailsDiv.style.transition;
    let originalTopologyDivTransition=topologyDiv.style.transition;
    let flowTableButton=document.getElementById("flowTableButton");
    switchFlowTableDiv.style.transition = "height 0.5s ease-in-out";
    topologyDiv.style.transition = "height 0.5s ease-in-out";
    if (flowTableButton.className == 'topBarButton') {
        switchFlowTableDiv.style.height = "40%";
        topologyDiv.style.height = "60%";
        flowTableButton.className = 'topBarButton-active';
    } else {
        switchFlowTableDiv.style.height = "0%";
        topologyDiv.style.height = "100%";
        flowTableButton.className = 'topBarButton';
    }
    setTimeout(function() {
        switchFlowTableDiv.style.transition = originalFlowTableTransition;
        topologyDiv.style.transition = originalTopologyDivTransition; 
    }, 500); 
}
