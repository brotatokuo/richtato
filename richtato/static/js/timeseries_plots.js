document.addEventListener("DOMContentLoaded", () => {
    const lineChart = document
        .getElementById("lineChart")
        .getContext("2d");
    plotLineChart(lineChart, "/get-timeseries-data/");
});

async function plotLineChart(ctx, endpointUrl) {
    try {
        const response = await fetch(endpointUrl);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const chartData = await response.json();
        const dataset = chartData.datasets[0];
        console.log("Fetched chart data:", chartData);
        const myLineChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: chartData.labels, // Use the labels from the response
                datasets: chartData.datasets.map(dataset => ({
                    label: dataset.label,
                    data: dataset.data,
                    backgroundColor: dataset.borderColor, // Semi-transparent background color
                    borderColor: dataset.borderColor, // Border color for the line
                    borderWidth: dataset.borderWidth || 2,
                    fill: dataset.fill !== undefined ? dataset.fill : false,
                    tension: dataset.tension !== undefined ? dataset.tension : 0.1,
                })),
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value, index, values) {
                                const roundedValue = Math.round(value);
                                return new Intl.NumberFormat('en-US', {
                                    style: 'currency',
                                    currency: 'USD',
                                    maximumFractionDigits: 0 // Ensure no decimal places are shown
                                }).format(roundedValue);
                            }
                        }
                    },
                },
                plugins: {
                    legend: {
                        display: true, // Set to true if you want to display the legend
                    },
                }
            },
        });
    } catch (error) {
        console.error("Error fetching or plotting data:", error);
    }
}