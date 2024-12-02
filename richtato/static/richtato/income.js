document.addEventListener('DOMContentLoaded', () => {
    const tableDataUrl = "get-table-data/";
    const yearFilter = document.getElementById('year-filter');
    const editTableButton = document.getElementById('detailsTableEditButton');
    
    const updateChart = () => {
        const selectedYear = yearFilter.value;
        const plotDataUrl = `/income/get-plot-data/${selectedYear}/`;

        // Create or update the ChartPlotter instance
        if (!window.expenseChart) {
            console.log('Creating new chart');
            window.expenseChart = new ChartPlotter(
                plotDataUrl,                    // chartUrl
                'incomeBarChart',              // canvasId
                'detailsTableIncome',          // tableID
                tableDataUrl,                   // tableUrl
                selectedYear,                   // year
                editTableButton,                // editButton
                'update/',
            );
        } else {
            console.log('Updating existing chart');
            window.expenseChart.chartUrl = plotDataUrl;
            window.expenseChart.year = selectedYear;
        }

        window.expenseChart.plotChart();
    };

    updateChart();
    yearFilter.addEventListener('change', updateChart);
});