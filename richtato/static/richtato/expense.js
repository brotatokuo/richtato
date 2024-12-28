document.addEventListener('DOMContentLoaded', () => {
    const tableDataUrl = "get-table-data/";
    const yearFilter = document.getElementById('year-filter');
    const editTableButton = document.getElementById('detailsTableEditButton');
    
    const updateChart = () => {
        const selectedYear = yearFilter.value;
        const plotDataUrl = `/expense/get-plot-data/${selectedYear}/`;

        // Create or update the ChartPlotter instance
        if (!window.expenseChart) {
            console.log('Creating new chart');
            window.expenseChart = new ChartPlotter(
                plotDataUrl,                    // chartUrl
                'expenseBarChart',              // canvasId
                'detailsTableExpense',          // tableID
                tableDataUrl,                   // tableUrl
                selectedYear,                   // year
                editTableButton,                // editButton
                'update/',
            );
        } else {
            window.expenseChart.chartUrl = plotDataUrl;
            window.expenseChart.year = selectedYear;
        }

        window.expenseChart.plotChart();
    };

    updateChart();
    yearFilter.addEventListener('change', updateChart);

    // Add event listener to description
    const descriptionInput = document.getElementById('description');
    descriptionInput.addEventListener('blur', () => {
        const description = descriptionInput.value;
        guessCategoryFromDescription(description);
    });
});

function guessCategoryFromDescription(description) {
    console.log('Guessing category for:', description);
    // Encode the description before sending it
    const url = `/expense/guess-category/?description=${encodeURIComponent(description)}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.category) {
                console.log('Category found:', data.category);
                const categoryInput = document.getElementById('category');
                categoryInput.value = data.category;
            } else {
                console.log('No category found');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}