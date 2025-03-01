document.addEventListener('DOMContentLoaded', () => {
    const tableDataUrl = "get-table-data/";
    const yearFilter = document.getElementById('year-filter');
    const monthFilter = document.getElementById('month-filter');
    const editTableButton = document.getElementById('detailsTableEditButton');

    const updateChart = () => {
        const selectedYear = yearFilter.value;
        const selectedMonth = document.getElementById('month-filter').value;
        const plotDataUrl = `/budget/get-plot-data/${selectedYear}/${selectedMonth}`;
        console.log("plot data url: ", plotDataUrl);

        // Create or update the ChartPlotter instance
        if (!window.expenseChart) {
            console.log('Creating new chart');
            window.expenseChart = new ChartPlotter(
                plotDataUrl,                    // chartUrl
                'budgetBarChart',              // canvasId
                'detailsTableBudget',          // tableID
                tableDataUrl,                   // tableUrl
                selectedYear,                   // year
                editTableButton,                // editButton
                'update/',
                'percentage'
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
    monthFilter.addEventListener('change', updateChart);
}
);
