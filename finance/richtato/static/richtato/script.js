
// async function fetchChartData(url, canvasId) {
//     try {
//         const response = await fetch(url);  // Use the URL passed from the template
//         const data = await response.json();

//         const ctx = document.getElementById(canvasId).getContext('2d');
//         new Chart(ctx, {
//             type: 'bar',  // Change this to 'line', 'pie', etc., as needed
//             data: data,
//             options: {
//                 responsive: true,
//                 scales: {
//                     y: {
//                         beginAtZero: true
//                     }
//                 }
//             }
//         });
//     } catch (error) {
//         console.error("Error fetching chart data:", error);
//     }
// }

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
                        updateTable(datasetLabel, label);
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

function updateTable(account, month) {
    const tableTitle = document.getElementById('table-title');
    const table = document.getElementById('detailsTable');

    // Clear the table before updating
    table.innerHTML = `
        <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Category</th>
            <th>Amount</th>
        </tr>
    `;
    tableTitle.textContent = " [" + label + "] " + datasetLabel;
    
    // Insert a new row with the data
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${date}</td>
        <td>${description}</td>
        <td>${category}</td>
        <td>${amount}</td>
    `;
    table.appendChild(row);
}