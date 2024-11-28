document.addEventListener('DOMContentLoaded', () => {
    const graphDataUrl = "{% url 'plot_earnings_data' %}";
    const tableDataUrl = "{% url 'get_earnings_data_json' %}";
    const yearFilter = document.getElementById('year-filter');

    if (yearFilter) {
        const initialYear = yearFilter.value;
        console.log("Initial selected year:", initialYear);

        plotBarChart(graphDataUrl, 'barChart', 'details-table-earnings', tableDataUrl, initialYear);

        // Add event listener for when the year filter changes
        yearFilter.addEventListener('change', () => {
            const selectedYear = yearFilter.value;
            console.log("Year filter change event triggered, selected year:", selectedYear);
            plotBarChart(graphDataUrl, 'barChart', 'details-table-earnings', tableDataUrl, selectedYear);
        });

    } else {
        console.error("Year filter element not found!");
    }
});
