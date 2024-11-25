document.addEventListener('DOMContentLoaded', () => {
    console.log("budget.js loaded!");
    const graphDataUrl = "{% url 'plot_budget_data' %}";
    const tableDataUrl = "{% url 'get_budget_data_json' %}";

    const yearFilter = document.getElementById('year-filter');
    const monthFilter = document.getElementById('month-filter');
    const errorMessage = document.getElementById('error-message');

    if (yearFilter && monthFilter) {
        // Event listeners for year and month filter changes
        yearFilter.addEventListener('change', () => updateMonths(yearFilter, monthFilter, errorMessage, graphDataUrl, tableDataUrl));
        monthFilter.addEventListener('change', () => updateChart(graphDataUrl, tableDataUrl, yearFilter, monthFilter));

        // Run updateMonths at startup to load months for the initial year
        updateMonths(yearFilter, monthFilter, errorMessage, graphDataUrl, tableDataUrl);
    } else {
        console.error("Year or Month filter element not found!");
    }
    
    const graphCategoryDataUrl = "/plot-category-budget-data/";
    const categoryFilter = document.getElementById('category-filter');

    function updateCategoryChart() {
        const urlWithParams = `${graphCategoryDataUrl}?year=${yearFilter.value}&category=${encodeURIComponent(categoryFilter.value)}`;
        console.log("URL with params:", urlWithParams);
        plotBudgetCategoryBarChart(urlWithParams, 'barChartCategory');
    }

    // Plot the category-wise budget chart
    categoryFilter.addEventListener('change', updateCategoryChart);
    updateCategoryChart();
});



// Function to update chart based on selected filters
function updateChart(graphDataUrl, tableDataUrl, yearFilter, monthFilter) {
    const selectedYear = yearFilter.value;
    const selectedMonth = monthFilter.value;
    console.log("Filter change event triggered:", selectedYear, selectedMonth);
    plotBudgetBarChart(graphDataUrl, 'barChart', 'details-table-budget', tableDataUrl, selectedYear, selectedMonth);
}

// Function to update months based on the selected year
function updateMonths(yearFilter, monthFilter, errorMessage, graphDataUrl, tableDataUrl) {
    const selectedYear = yearFilter.value;

    // Clear the month dropdown
    monthFilter.innerHTML = '';

    // Fetch months based on the selected year (adjust this path based on your actual URL)
    fetch(`/get-budget-months/?year=${selectedYear}`)
        .then(response => response.json())
        .then(data => {
            console.log('Months:', data);
            data.forEach(month => {
                const option = document.createElement('option');
                option.value = month;
                option.textContent = month;
                monthFilter.appendChild(option);
            });
            // Trigger chart update after months have been refreshed
            updateChart(graphDataUrl, tableDataUrl, yearFilter, monthFilter);
        })
        .catch(error => {
            if (errorMessage) {
                errorMessage.textContent = "Failed to load months.";
            }
            console.error('Error fetching months:', error);
        });
}
