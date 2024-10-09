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
    
    const editButton = document.getElementById('editButton');
    if (editButton) {
        editButton.style.display = 'none';
        console.log("Edit button hidden");
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

myChart = null;
async function plotBarChart(url, canvasId, tableData, group_by) {
    try {
        const year = parseInt(document.getElementById('year-filter').value);
        console.log("Year:", year); 
        const response = await fetch(url);  // Fetch data from the provided URL
        const data = await response.json();
        console.log("Original data:", data);
        // Filter the data by year
        const filteredDataByYear = data.filter(item => item.year === year);
        console.log("Filtered data:", filteredDataByYear);
        
        const ctx = document.getElementById(canvasId).getContext('2d');

        // Destroy existing chart instance if it exists
        if (myChart) {
            myChart.destroy();
        }

        myChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: filteredDataByYear.map(d => d.labels).flat(),  // Ensure your data structure supports this
                datasets: filteredDataByYear.map(d => d.data).flat()  // Adjust if your data structure is different
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        beginAtZero: true,
                        stacked: true
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        var datasetIndex = elements[0].datasetIndex;
                        var index = elements[0].index;
                        var datasetLabel = myChart.data.datasets[datasetIndex].label;
                        var month = myChart.data.labels[index];
                        console.log("Clicked:", year, month, datasetLabel);

                        updateTable(tableData, year, month, datasetLabel, group_by);
                    }   

                    // Update the table with the dataset details
                    // updateTable(datasetLabel, label);
                }
            }
        });
    } catch (error) {
        console.error("Error fetching stacked chart data:", error);
    }
}


function updateTable(tableData, year, month, account, group_by) { 
    const monthToNumber = (month) => ({
        jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6,
        jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12
    }[month.toLowerCase()] || null);

    const tableData_year_grouped = (tableData[year] || {})[account] || [];
    const monthNumber = monthToNumber(month);
    const title1 = document.getElementById('detailed-table-title-1');
    const title2 = document.getElementById('detailed-table-title-2');
    const table = document.getElementById('detailsTable');
    console.log("table", table);

    const headers = {
        "Account Name": ["Delete", "ID", "Date", "Description", "Amount", "Category"],
        "Description": ["Delete", "ID", "Date", "Account Name", "Amount"],
        "Account": ["Delete", "ID", "Date", "Account Name", "Amount"]
    };

    table.innerHTML = `
        <thead>
            <tr>${headers[group_by].map(header => `<th>${header}</th>`).join('')}</tr>
        </thead>
        <tbody></tbody>
    `;

    let total = 0;

    tableData_year_grouped.forEach(transaction => {
        const transactionDate = transaction.Date.split("T")[0];
        const transactionMonth = transactionDate.split("-")[1];

        if (transactionMonth == monthNumber) {
            const row = document.createElement('tr');
            const group_by_value = group_by === "Account Name" ? transaction.Description :
                                   group_by === "Description" ? transaction["Account Name"] :
                                   transaction.account__name;

            row.innerHTML = `
                <td><input type="checkbox" class="delete-checkbox"></td>
                <td>'ID'</td>
                <td>${transactionDate}</td>
                <td>${group_by_value}</td>
                <td>$${parseFloat(transaction.Amount || transaction.balance_history).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}</td>
                ${group_by === "Account Name" ? `<td>${transaction.Category}</td>` : ""}
                <td style="display: none;">${transaction.id}</td>
            `;
            total += parseFloat(transaction.Amount || transaction.balance_history);
            const tableBody = table.querySelector('tbody');
            tableBody.appendChild(row);
            console.log("Row added:", row);
            console.log("Table body:", tableBody);  
        }
    });

    title1.innerHTML = `${account}`;
    title2.innerHTML = `[${year} ${month}]: $${total.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`;
    toggleEditButton();
}


function editTable(tableID, editButtonID) {
    console.log("Edit button clicked", tableID, editButtonID);
    const table = document.getElementById(tableID);
    console.log("Table:", table);
    const rows = table.rows;

    for (let i = 1; i < rows.length; i++) {  // Skip header row
        const cells = rows[i].cells;
        console.log("Row cells:", cells);
    
        for (let j = 0; j < cells.length; j++) {
            const cell = cells[j];
    
            if (j === 0) {
                console.log("Unhiding delete column");
                // Show the delete column (remove the display: none style)
                cell.style.display = '';  // Make the delete checkbox column visible
            } else if (j===1){
                console.log("don't show id column");
            }
            else {
                // Convert the other cells into input fields
                const value = cell.textContent.trim();
                cell.innerHTML = `<input type="text" value="${value}">`;
            }
        }
    }
    
    // Make sure to also make the header of the delete column visible
    const headerRow = table.rows[0].cells[0];  // Assuming the delete column header is in the first cell
    headerRow.style.display = '';  // Make the header for the delete column visible
    
    
    // Change the button text to 'Save'
    const editButton = document.getElementById(editButtonID);
    console.log("Edit button:", editButton);
    editButton.textContent = 'Save';
    editButton.style.backgroundColor = 'gold';

    // Assign the saveTable function as the click handler
    editButton.onclick = function() {
        saveTable(tableID, editButtonID);
    };
}


function toggleEditButton() {
    const table = document.getElementById('detailsTable');
    const editButton = document.getElementById('editButton');
    console.log("Edit Button:", editButton);
    console.log("Table rows:", table.rows.length);
    if (table.rows.length > 0) {
        editButton.style.display = 'block';
    } else {
        editButton.style.display = 'none';
    }
}