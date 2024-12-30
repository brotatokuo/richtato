document.addEventListener('DOMContentLoaded', () => {
    const tableDataUrl = "get-table-data/";
    const yearFilter = document.getElementById('year-filter');
    const editTableButton = document.getElementById('detailsTableEditButton');
    const groupByFilter = document.getElementById('group-by-filter');
    
    const updateChart = () => {
        const selectedYear = parseInt(yearFilter.value, 10);
        const groupBy = groupByFilter.value;
        console.log('Updating chart for year:', selectedYear, 'group by:', groupBy);
        const plotDataUrl = `/expense/get-plot-data?year=${selectedYear}&group_by=${groupBy}`;

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

    // Add event listener to group by
    groupByFilter.addEventListener('change', updateChart);

    const balanceInput = document.getElementById('balance-input');

    balanceInput.addEventListener('blur', () => {
        let balance = balanceInput.value;
        newBalance = computeBalance(balance);

        if (newBalance) {
            balanceInput.value = newBalance;
            console.log('New balance:', newBalance);
        }
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

function computeBalance(balance){
        // Check if it's a formula starting with '='
        if (balance.startsWith('=')) {
            try {
                // Evaluate the formula (strip the leading '=')
                balance = eval(balance.slice(1));  // Caution: Use math.js for safety in production
                console.log('Evaluated formula:', balance);
            } catch (error) {
                console.error('Invalid formula:', error);
                return;  // Stop further processing if the formula is invalid
            }
        }
    
        // Convert to a float for regular numbers or evaluated formulas
        balance = parseFloat(balance).toFixed(2);
        return balance;
}