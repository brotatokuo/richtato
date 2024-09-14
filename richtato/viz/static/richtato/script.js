document.addEventListener('DOMContentLoaded', (event) => {
    // Swap GIF with a static image after 2 seconds
    var gif = document.getElementById('growth-gif');
    if (gif) {
        setTimeout(function() {
            document.querySelector('.typewriter-text').style.borderRight = 'none';
            gif.src = staticImagePath; // Use the variable defined in the HTML
        }, 2000);
    }
});

// Toggle password visibility
function togglePasswordVisibility(id, button) {
    console.log("togglePasswordVisibility called with id:", id);
    var passwordInput = document.getElementById(id);
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        button.textContent = "Hide";
    } else {
        passwordInput.type = "password";
        button.textContent = "Show";
    }
}


async function stackedFetchChartData(url, canvasId, tableData) {
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
                        const monthNumber = dataIndex + 1;

                        // Display the clicked bar data
                        // alert(`Label: ${label}\nDataset: ${datasetLabel}\nValue: ${value}\nData Index: ${dataIndex}`);

                        // Update the table with the dataset details
                        updateTable(tableData, label, datasetLabel, monthNumber);
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

function updateTable(transactions, month, account, monthNumber) {
    const tableTitle = document.getElementById('table-title');
    const table = document.getElementById('detailsTable');

    // Update the table title
    tableTitle.innerHTML = `${account}<br>${month}`;
    // Loop through transactions and append rows to the table
    table.innerHTML = `
        <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Amount</th>
            <th>Category</th>
        </tr>
    `;
    if (Array.isArray(transactions)) {
        transactions.forEach(transactions => {
        const row = document.createElement('tr');
        
        const accountName = transactions["Account Name"];
        const transactionDate = transactions.Date.split("T")[0];
        const transactionYear = transactionDate.split("-")[0];
        const transactionMonth = transactionDate.split("-")[1];

        // Skip transactions that don't match the selected month and account
        if (accountName == account && transactionMonth == monthNumber) {
            // Create columns for each field in the transaction
            row.innerHTML = `
            <td>${transactionDate}</td>
            <td>${transactions.Description}</td>
            <td>${transactions.Amount}</td>
            <td>${transactions.Category}</td>
        `;

        // Append the row to the table body
        table.appendChild(row);
        }
        
    });
    } else {
        // Handle cases where transactions is not an array
        console.error("datasets is not an array:", datasets);
    }
}