document.addEventListener('DOMContentLoaded', () => {
    const graphDataUrl = "{% url 'plot_spendings_data' %}";
    const tableDataUrl = "{% url 'get_spendings_data_json' %}";
    const yearFilter = document.getElementById('year-filter');

    if (yearFilter) {
        const initialYear = yearFilter.value;
        console.log("Initial selected year:", initialYear);

        plotBarChart(graphDataUrl, 'barChart', 'details-table-spendings', tableDataUrl, initialYear);

        // Add event listener for when the year filter changes
        yearFilter.addEventListener('change', () => {
            const selectedYear = yearFilter.value;
            console.log("Year filter change event triggered, selected year:", selectedYear);
            plotBarChart(graphDataUrl, 'barChart', 'details-table-spendings', tableDataUrl, selectedYear);
        });

    } else {
        console.error("Year filter element not found!");
    }

    const description = document.getElementById('description');
    if (description) {
        description.addEventListener('blur', () => {
            const descriptionValue = description.value;
            console.log("Description value:", descriptionValue);
            fetch('/get-category?description=' + description.value)
                .then(response => response.json())
                .then(data => {
                    console.log('Category:', data);
                    const categorySelect = document.getElementById('category');
                    if (categorySelect) {
                        categorySelect.value = data.category;
                    }
                })
                .catch(error => console.error('Error fetching category:', error));
        });
    } else {
        console.error("Description element not found!");
    }
});
