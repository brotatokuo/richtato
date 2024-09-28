document.addEventListener('DOMContentLoaded', (event) => {
    // Swap GIF with a static image after 2 seconds
    var gif = document.getElementById('growth-gif');
    if (gif) {
        setTimeout(function() {
            document.querySelector('.typewriter-text').style.borderRight = 'none';
            gif.src = staticImagePath; // Use the variable defined in the HTML
        }, 2000);
    }

    const currencyInput = document.getElementById('balance-input');
    if (currencyInput) {
        currencyInput.addEventListener('blur', function(e) {
            console.log("Currency input blur event triggered");
            
            let value = parseFloat(e.target.value);

            // Ensure the value is a valid number before formatting
            if (!isNaN(value)) {
                e.target.value = value.toFixed(2); // Format to two decimal places
            } else {
                console.log("Invalid input:", e.target.value); // Handle invalid input
            }
        });
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

async function stackedFetchChartData(url, canvasId, tableData, group_by) {
    try {
        const response = await fetch(url);  // Fetch data from the provided URL
        console.log("response:", response); 
        const data = await response.json();

        const ctx = document.getElementById(canvasId).getContext('2d');
        const myChart = new Chart(ctx, {
            type: 'bar',
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
                        updateTable(tableData, label, datasetLabel, monthNumber, group_by);

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
                        position: 'top'  // Move the legend to the top
                    }
                }
            }
        });
    } catch (error) {
        console.error("Error fetching stacked chart data:", error);
    }
}

function updateTable(transactions, month, account, monthNumber, group_by) {
    const title1 = document.getElementById('detailed-table-title-1');
    const title2 = document.getElementById('detailed-table-title-2');
    const table = document.getElementById('detailsTable');
    
    // Determine the non group_by field
    if (group_by == "Account Name") {
        var non_group_by = "Decscription";
    } else {
        var non_group_by = "Account Name";
    }

    // Loop through transactions and append rows to the table
    table.innerHTML = `
        <thead>
            <tr>
                <th>Date</th>
                <th>${non_group_by}</th>
                <th>Amount</th>
                <th>Category</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    const tableBody = table.querySelector('tbody');
    var total = 0;

    if (Array.isArray(transactions)) {
        transactions.forEach(transactions => {
        const row = document.createElement('tr');
        
        console.log("transactions:", transactions);
        const accountName = transactions[group_by];
        const transactionDate = transactions.Date.split("T")[0];
        const transactionYear = transactionDate.split("-")[0];
        const transactionMonth = transactionDate.split("-")[1];

        // Skip transactions that don't match the selected month and account
        if (accountName == account && transactionMonth == monthNumber) {
            if (group_by == "Account Name") {
                var group_by_value = transactions.Description;
            } else {
                var group_by_value = transactions["Account Name"];
            }
            
            row.innerHTML = `
            <td>${transactionDate}</td>
            <td>${group_by_value}</td>
            <td>${transactions.Amount}</td>
            <td>${transactions.Category}</td>
        `;
        total += parseFloat(transactions.Amount);

        // Append the row to the table body
        tableBody.appendChild(row);
        }
        
    });

    // Update the table title
    title1.innerHTML = `${account}`;
    // Add total to title
    title2.innerHTML = `[${month}]: $${total.toFixed(2)}`;

    } else {
        // Handle cases where transactions is not an array
        console.error("datasets is not an array:", datasets);
    }
}

