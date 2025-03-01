document.addEventListener('DOMContentLoaded', function () {

    // Card Accounts Table
    const cardAccountsTable = new TableManager(
        'settings-card-table',
        'get-cards/',
        document.getElementById('settingsCardEditButton'),
        'update-cards/',
    );

    cardAccountsTable.loadTableData();
    document.getElementById('settingsCardEditButton').onclick = function() {
        cardAccountsTable.toggleEditMode();
    };

    // Accounts Table
    const accountsTable = new TableManager(
        'settings-accounts-table',
        'get-accounts/',
        document.getElementById('settingsAccountEditButton'),
        'update-accounts/',
    );

    accountsTable.loadTableData();
    document.getElementById('settingsAccountEditButton').onclick = function() {
        accountsTable.toggleEditMode();
    };

    // Categories Table
    const categoriesTable = new TableManager(
        'settings-categories-table',
        'get-categories/',
        document.getElementById('settingsCategoryEditButton'),
        'update-categories/',
    );

    categoriesTable.loadTableData();
    document.getElementById('settingsCategoryEditButton').onclick = function() {
        categoriesTable.toggleEditMode();
    };

    // Import Data Table
    const generateTemplateButton = document.getElementById('generateGoogleSheetsTempalateButton');
    generateTemplateButton.onclick = function() {
        alert('Are you sure you want to generate a new Google Sheets template? This will overwrite any existing template.');
    };

    const importData = document.getElementById('importGoogleSheetsButton');
    importData.onclick = function() {
        alert('Are you sure you want to import data from Google Sheets?');
    };

    toggleEditButton('settings-card-table', 'settingsCardEditButton');
    toggleEditButton('settings-accounts-table', 'settingsAccountEditButton');
    toggleEditButton('settings-categories-table', 'settingsCategoryEditButton');

});

function toggleEditButton(tableId, buttonId) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    const editButton = document.getElementById(buttonId);

    // Check if tbody has any rows
    if (tbody && tbody.rows.length === 0) {
        // Hide the button if tbody is empty
        editButton.style.display = 'none';
    } else {
        // Show the button if tbody has rows
        editButton.style.display = 'block';
    }
}
