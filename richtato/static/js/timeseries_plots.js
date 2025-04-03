let chartInstance = null;

document.addEventListener("DOMContentLoaded", async () => {
    const lineChart = document
        .getElementById("lineChart")
        .getContext("2d");

    chartInstance = await plotLineChart(lineChart);

    monthsDropdown.addEventListener("change", async () => {
        if (chartInstance) {
            chartInstance.destroy();
        }

        const lineChart = document
            .getElementById("lineChart")
            .getContext("2d");

        chartInstance = await plotLineChart(lineChart);
    });
});

async function plotLineChart(ctx) {
    const monthsDropdown = document.getElementById("monthsDropdown");
    const selectedRange = monthsDropdown.value;
    const endpointUrl = `/get-timeseries-data/?month_range=${encodeURIComponent(selectedRange)}`;
    console.log("Selected month range:", selectedRange);
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
                        ticks: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim() || "#fff",
                        },
                        grid: {
                            color: "rgba(255, 255, 255, 0.2)", // Light grid lines for dark mode
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim() || "#fff",
                            callback: function (value, index, values) {
                                const roundedValue = Math.round(value);
                                return new Intl.NumberFormat('en-US', {
                                    style: 'currency',
                                    currency: 'USD',
                                    maximumFractionDigits: 0 // Ensure no decimal places are shown
                                }).format(roundedValue);
                            }
                        },
                        grid: {
                            color: "rgba(255, 255, 255, 0.2)", // Light grid lines for dark mode
                        }

                    },
                },
                plugins: {
                    legend: {
                        labels: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim() || "#000",
                        },
                        onClick: function (e, legendItem, legend) {
                            const index = legendItem.datasetIndex;
                            const ci = legend.chart;

                            // Check if only this dataset is currently visible
                            const isOnlyVisibleDataset = ci.data.datasets.every((dataset, i) => {
                                if (i === index) return !ci.getDatasetMeta(i).hidden;
                                return ci.getDatasetMeta(i).hidden;
                            });

                            if (isOnlyVisibleDataset) {
                                // If clicked dataset is the only one visible, show all datasets
                                ci.data.datasets.forEach((dataset, i) => {
                                    const meta = ci.getDatasetMeta(i);
                                    meta.hidden = false;
                                });
                            } else {
                                // Otherwise, hide all and show only the clicked one
                                ci.data.datasets.forEach((dataset, i) => {
                                    const meta = ci.getDatasetMeta(i);
                                    meta.hidden = (i !== index);
                                });
                            }

                            // Ensure animations are preserved
                            ci.update('show');
                        }
                    }
                }
            },
        });
        return myLineChart;
    } catch (error) {
        console.error("Error fetching or plotting data:", error);
    }
}