document.addEventListener('DOMContentLoaded', () => {
    const tableDataUrl = "get-table-data/";
    const yearFilter = document.getElementById('year-filter');
    const editTableButton = document.getElementById('detailsTableEditButton');
    const groupByFilter = document.getElementById('group-by-filter');

    const updateChart = () => {
        const selectedYear = parseInt(yearFilter.value, 10);
        const groupBy = groupByFilter.value;
        console.log('Updating chart for year:', selectedYear, 'group by:', groupBy);
        const plotDataUrl = `/income/get-plot-data?year=${selectedYear}&group_by=${groupBy}`;

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

    // Add event listener to group by
    groupByFilter.addEventListener('change', updateChart);
});