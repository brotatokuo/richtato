document.addEventListener('DOMContentLoaded', () => {
    const piedataUrl = "{% url 'plot_accounts_data_pie' %}";
    const graphDataUrl = "{% url 'plot_accounts_data' %}";
    const tableDataUrl = "{% url 'get_accounts_data_json' %}";
    const yearFilter = document.getElementById('year-filter');

    if (yearFilter) {
        const initialYear = yearFilter.value;
        console.log("Initial selected year:", initialYear);

        pieChartData(piedataUrl, 'pieChart');
        plotBarChart(graphDataUrl, 'barChart', 'details-table-accounts', tableDataUrl, initialYear);
        
        // Add event listener for when the year filter changes
        yearFilter.addEventListener('change', () => {
            const selectedYear = yearFilter.value;
            console.log("Year filter change event triggered, selected year:", selectedYear);
            plotBarChart(graphDataUrl, 'barChart', 'details-table-accounts', tableDataUrl, selectedYear);
        });
        
    } else {
        console.error("Year filter element not found!");
    }
});


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
