async function stackedFetchChartData(url, canvasId) {
    try {
        const response = await fetch(url);  // Use the URL passed from the template
        const data = await response.json();

        const ctx = document.getElementById(canvasId).getContext('2d');
        new Chart(ctx, {
            type: 'bar',  // Change this to 'line', 'pie', etc., as needed
            data: data,
            options: {
                responsive: true,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const element = elements[0];
                        const datasetIndex = element.datasetIndex;
                        const dataIndex = element.index;

                        const datasetLabel = data.datasets[datasetIndex].label;
                        const value = data.datasets[datasetIndex].data[dataIndex];
                        const label = data.labels[dataIndex];

                        // Display the clicked bar data
                        // alert(`Label: ${label}\nDataset: ${datasetLabel}\nValue: ${value}`);

                        // Update the table with the dataset details
                        updateTable(data);
                    }
                    
                },
                scales: {
                    x: {
                        stacked: true  // Stack the bars along the x-axis
                    },
                    y: {
                        beginAtZero: true,
                        stacked: true  // Stack the bars along the y-axis
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'  // Move the legend to the right
                    }
                }
            }
        });
    } catch (error) {
        console.error("Error fetching stacked chart data:", error);
    }
}

function updateTable(transactions) {
    const tableTitle = document.getElementById('table-title');
    const table = document.getElementById('detailsTable');
    console.log(typeof transactions);
    console.log(transactions)
    const datasets = transactions.datasets;

    // Loop through transactions and append rows to the table
    table.innerHTML = `
        <tr>
            <th>Date</th>
            <th>Account Name</th>
            <th>Description</th>
            <th>Amount</th>
            <th>Category</th>
        </tr>
    `;
    if (Array.isArray(datasets)) {
        datasets.forEach(datasets => {
        const row = document.createElement('tr');

        // Create columns for each field in the transaction
        row.innerHTML = `
            <td>${datasets.label}</td>
            <td>${datasets.Data}</td>
            <td>${datasets.Description}</td>
            <td>${datasets.Amount}</td>
            <td>${datasets.Category}</td>
        `;

        // Append the row to the table body
        table.appendChild(row);
    });
    } else {
        // Handle cases where transactions is not an array
        console.error("datasets is not an array:", datasets);
    }
}