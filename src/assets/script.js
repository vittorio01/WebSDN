document.addEventListener("DOMContentLoaded", function() {
    const observer = new MutationObserver(function(mutations) {
        let hBar = document.getElementById("hBar");
        let vBar = document.getElementById("vBar");
        let detailsDiv = document.getElementById("detailsDiv");
        let rightDiv = document.getElementById("rightDiv");
        let topologyDiv = document.getElementById("topologyDiv");
        let topBarDiv=document.getElementById("topBarDiv");
        let deviceListDiv = document.getElementById("deviceListDiv");
        let deviceDetailsDiv = document.getElementById("deviceDetailsDiv");
        let deviceListGrid = document.getElementById("deviceListGrid");
        let deviceDetailsGrid = document.getElementById("deviceDetailsGrid");
        let toggleButton = document.getElementById("toggleButton");
        if (hBar && vBar && detailsDiv && rightDiv && deviceListDiv && deviceDetailsDiv && topologyDiv && topBarDiv && deviceListGrid && deviceDetailsGrid && toggleButton)  {
            hBar.addEventListener("mousedown", (e) => {
                document.addEventListener("mousemove", resizeHorizontal);
                document.addEventListener("mouseup", () => {
                    document.removeEventListener("mousemove", resizeHorizontal);
                }, { once: true });
            });
            vBar.addEventListener("mousedown", (e) => {
                document.addEventListener("mousemove", resizeVertical);
                document.addEventListener("mouseup", () => {
                    document.removeEventListener("mousemove", resizeVertical);
                }, { once: true });
            });
            toggleButton.addEventListener("click", function() {
                toggleDetails();
            });
            observer.disconnect();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
});


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

function toggleDetails() {
    let detailsDiv = document.getElementById("detailsDiv");
    let rightDiv = document.getElementById("rightDiv");
    let originalDetailsTransition=detailsDiv.style.transition;
    let originalRightTransition=rightDiv.style.transition;
    detailsDiv.style.transition = "width 0.5s ease-in-out";
    rightDiv.style.transition = "width 0.5s ease-in-out";
    if (detailsDiv.style.width == "0%") {
        detailsDiv.style.width = "40%";
        rightDiv.style.width="60%";

    } else {
        detailsDiv.style.width = "0%";
        rightDiv.style.width="100%"
    }
    setTimeout(function() {
        rightDiv.style.transition = originalRightTransition;
        detailsDiv.style.transition = originalDetailsTransition; 
    }, 500); 
}