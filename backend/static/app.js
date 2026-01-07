let intervalId = null;
let refreshFrequency = 1000;
let threshold = 10;
let userRole = null;
//let userRole = null;
let usernameLogged = null;

// Main graph
let peopleChart = null;

//MAIN GRAPH
function initMainChart() {
    const ctx = document.getElementById("peopleChart");
    if (!ctx) return;

    peopleChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: "#ffffff",
                borderWidth: 3,
                pointRadius: 3,
                pointBackgroundColor: "#ffffff",
                pointBorderColor: "#ffffff",
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    ticks: { color: "#ffffff", font: { weight: "bold" } },
                    grid: {
                        color: "rgba(255,255,255,0.15)",
                        drawBorder: true,
                        borderColor: "#ffffff"
                    }
                },
                y: {
                    beginAtZero: true,
                    min: 0,
                    ticks: {
                        color: "#ffffff",
                        stepSize: 1,
                        font: { weight: "bold" }
                    },
                    grid: {
                        color: "rgba(255,255,255,0.15)",
                        drawBorder: true,
                        borderColor: "#ffffff"
                    }
                }
            }
        }
    });
}

//UPDATE DASHBOARD
async function update() {
    try {
        const res = await fetch("/get_count");
        if (!res.ok) return;

        const data = await res.json();
        const liveCount = Math.max(0, Math.floor(data.total_live));

        document.getElementById("live").innerText = liveCount;
        document.getElementById("total").innerText = data.total_cumulative;
        document.getElementById("last-update").innerText = data.timestamp;

        //MAIN GRAPH
        if (peopleChart) {
            peopleChart.data.labels.push(data.timestamp);
            peopleChart.data.datasets[0].data.push(liveCount);

            if (peopleChart.data.labels.length > 20) {
                peopleChart.data.labels.shift();
                peopleChart.data.datasets[0].data.shift();
            }
            peopleChart.update();
        }

        //ZONE TABLE
        const tbody = document.getElementById("zone-body");
        tbody.innerHTML = "";

        Object.entries(data.zones).forEach(([zone, values]) => {
            const row = document.createElement("tr");

            if (values.total > threshold) {
                row.style.background = "rgba(239,68,68,0.18)";
            }

            row.innerHTML = `
                <td>${zone}</td>
                <td>${values.live}</td>
                <td>${values.total}</td>
            `;

            tbody.appendChild(row);
        });

    } catch (e) {
        console.error("Update failed", e);
    }
}

//CONTROLS
function applyThreshold() {
    threshold = parseInt(document.getElementById("threshold").value) || 0;
}

function applyFrequency() {
    refreshFrequency = (parseInt(document.getElementById("frequency").value) || 1) * 1000;
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(update, refreshFrequency);
}

function downloadCSV() {
    window.location.href = "/download_logs";
}
//Login Function
async function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
        document.getElementById("login-error").innerText = "Invalid login";
        return;
    }

    const data = await res.json();

    //SAVE USER INFO
    usernameLogged = username;
    userRole = data.role;

    //SHOW USER ON DASHBOARD
    document.getElementById("user-info").innerText =
        `Logged in as: ${usernameLogged} (${userRole.toUpperCase()})`;

    //HIDE LOGIN OVERLAY (reliable)
    document.getElementById("login-overlay").style.display = "none";
    document.body.style.overflow = "auto";
    // Role-based UI
    if (userRole !== "admin") {
        document.getElementById("threshold").disabled = true;
        document.querySelector("button[onclick='applyThreshold()']").disabled = true;
        document.querySelector("button[onclick='downloadCSV()']").disabled = true;
    }

    initMainChart();
    update();
    intervalId = setInterval(update, refreshFrequency);
}


//START
window.onload = () => {
    initMainChart();
    update();
    intervalId = setInterval(update, refreshFrequency);
};
