document.addEventListener('DOMContentLoaded', (event) => {
    // Swap GIF with a static image after 2 seconds
    var gif = document.getElementById('growth-gif');
    if (gif) {
        setTimeout(function () {
            document.querySelector('.typewriter-text').style.borderRight = 'none';
            gif.src = staticImagePath; // Use the variable defined in the HTML
        }, 2000);
    }

    const currencyInput = document.getElementById('balance-input');
    if (currencyInput) {
        currencyInput.addEventListener('blur', function (e) {
            let value = parseFloat(e.target.value);
            // Ensure the value is a valid number before formatting
            if (!isNaN(value)) {
                e.target.value = value.toFixed(2); // Format to two decimal places
            } else {
                console.log("Invalid input:", e.target.value); // Handle invalid input
            }
        });
    }
});

function togglePasswordVisibility(id, button) {
    console.log("togglePasswordVisibility called with id:", id);
    var passwordInput = document.getElementById(id);
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        button.textContent = "Hide";
    } else {
        passwordInput.type = "password";
        button.textContent = "Show";
    }
}

function getCSRFToken() {
    const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)')?.pop();
    return cookieValue || '';
}

let chartInstances = {};  // Object to store chart instances by canvasId

async function plotBarChart(chartUrl, canvasId, tableID, tableUrl, year) {
    try {
        const response = await fetch(chartUrl);  // Fetch data from the provided chartUrl
        const data = await response.json();
        console.log("plotBarChart data received from API:", data, "filter by year:", year);
        const filteredDataByYear = data.filter(item => item.year === parseInt(year));
        console.log("Filtered data:", filteredDataByYear);

        const ctx = document.getElementById(canvasId).getContext('2d');

        lastChartUrl = chartUrl;
        lastCanvasId = canvasId;
        lastTableID = tableID;
        lastTableUrl = tableUrl;
        lastYear = year;

        // Destroy existing chart instance for this canvas if it exists
        if (chartInstances[canvasId]) {
            chartInstances[canvasId].destroy();
        }

        chartInstances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: filteredDataByYear.map(d => d.labels).flat(),
                datasets: filteredDataByYear.map(d => d.data).flat()
            },
            options: {
                responsive: true,
                scales: {
                    x: { stacked: true },
                    y: { beginAtZero: true, stacked: true }
                },
                plugins: {
                    legend: { position: 'top' }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        console.log("elements:", elements);
                        var datasetIndex = elements[0].datasetIndex;
                        var index = elements[0].index;
                        var datasetLabel = chartInstances[canvasId].data.datasets[datasetIndex].label;
                        var month = chartInstances[canvasId].data.labels[index];
                        console.log("Clicked:", year, month, datasetLabel);

                        fetchBarTableData(tableID, tableUrl, year, month, datasetLabel);

                        const title_1 = document.getElementById('detailed-table-title-1');
                        const title_2 = document.getElementById('detailed-table-title-2');

                        if (title_1 && title_2) {
                            title_1.textContent = `${year} ${month}`;
                            title_2.textContent = `${datasetLabel}`;
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error("Error fetching stacked chart data:", error);
    }
}

async function plotBudgetCategoryBarChart(chartUrl, canvasId) {
    try {
        const response = await fetch(chartUrl);
        const data = await response.json();
        console.log("plotBudgetCategoryBarChart data received from API:", data);

        const ctx = document.getElementById(canvasId).getContext('2d');

        lastChartUrl = chartUrl;
        lastCanvasId = canvasId;

        // Destroy existing chart instance for this canvas if it exists
        if (chartInstances[canvasId]) {
            chartInstances[canvasId].destroy();
        }

        chartInstances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                scales: {
                    x: { stacked: true },
                    y: { beginAtZero: true, stacked: true }
                },
                plugins: {
                    legend: { position: 'top' }
                },
            }
        });
    } catch (error) {
        console.error("Error fetching stacked chart data:", error);
    }
}

async function plotBudgetBarChart(chartUrl, canvasId, tableID, tableUrl, year, month) {
    try {
        const response = await fetch(chartUrl);  // Fetch data from the provided chartUrl
        const data = await response.json();
        console.log("Data received from API:", data);
        const filteredDataByYear = data.filter(item => item.year === parseInt(year))[0];
        console.log("Filtered data by year:", filteredDataByYear);
        const filteredDataByMonth = filteredDataByYear.data.find(monthData => monthData.month === parseInt(month));
        console.log("Filtered data by month:", filteredDataByMonth);
        const plotData = filteredDataByMonth.data;
        console.log("Plot data:", plotData);

        const ctx = document.getElementById(canvasId).getContext('2d');

        lastChartUrl = chartUrl;
        lastCanvasId = canvasId;
        lastTableID = tableID;
        lastTableUrl = tableUrl;
        lastYear = year;

        // Destroy existing chart instance for this canvas if it exists
        if (chartInstances[canvasId]) {
            chartInstances[canvasId].destroy();
        }
        // Create the chart
        chartInstances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: plotData,
            options: {
                responsive: true,
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        beginAtZero: true,
                        stacked: true,
                        suggestedMax: 100,
                        ticks: {
                            callback: function (value) {
                                return value + '%';  // Append '%' to each y-axis tick label
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        console.log("elements:", elements);
                        var datasetIndex = elements[0].datasetIndex;
                        var datasetLabel = chartInstances[canvasId].data.datasets[datasetIndex].label;
                        // var datasetLabel = chartInstances[canvasId].data.datasets[0].label;
                        console.log("Clicked:", year, month, datasetLabel);

                        fetchBarTableData(tableID, tableUrl, year, month, datasetLabel);

                        // Convert month number to 3-letter abbreviation (MMM) if it's a number
                        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

                        let displayMonth = month;

                        // Check if the month is a number and convert it to MMM
                        if (!isNaN(month) && month >= 1 && month <= 12) {
                            displayMonth = monthNames[month - 1]; // Convert month number to its respective abbreviation
                        }

                        const title_1 = document.getElementById('detailed-table-title-1');
                        const title_2 = document.getElementById('detailed-table-title-2');

                        if (title_1 && title_2) {
                            title_1.textContent = `${year} ${displayMonth}`;
                            title_2.textContent = `${datasetLabel}`;
                        }

                        // Change category chart to the same datasetLabel
                        categoryDropDown = document.getElementById('category-filter');
                        if (categoryDropDown) {
                            for (let i = 0; i < categoryDropDown.options.length; i++) {
                                if (categoryDropDown.options[i].value === datasetLabel) {
                                    categoryDropDown.selectedIndex = i;

                                    // Create and dispatch a change event to trigger the event listener
                                    var event = new Event('change');
                                    categoryDropDown.dispatchEvent(event);
                                    break;
                                }
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error("Error fetching stacked chart data:", error);
    }
}
