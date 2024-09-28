async function pieChartData(url, canvasId) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        console.log("Pie chart data:", data);
        const ctx = document.getElementById(canvasId).getContext('2d');
        const myChart = new Chart(ctx, {
            type: 'doughnut',  // Use 'doughnut' type for the chart
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top'  // Position the legend at the top
                    },
                    tooltip: {
                        enabled: true  // Enable tooltips
                    },
                }
            },
        });
    } catch (error) {
        console.error("Error fetching pie chart data:", error);
    }
}