document.addEventListener("DOMContentLoaded", () => {
    const assetsTable = new RichTable(
        "#assetsTable",
        "/api/accounts/",
        ["name", "type", "entity"],
    );

    // Define table in outer scope so it's accessible across functions
    let table;

    const initialAccountId = document.querySelector("#accountDropdown").value;
    loadTableForAccount(initialAccountId);

    // On account change
    document.querySelector("#accountDropdown").addEventListener("change", function () {
        const selectedAccountId = this.value;
        loadTableForAccount(selectedAccountId);
    });

    function loadTableForAccount(accountId) {
        const endpoint = accountId
            ? `/api/accounts/details/${accountId}/`
            : `/api/accounts/details/`;

        if (table) {
            table.instance.destroy();
        }

        console.log("endpoint", endpoint);

        table = new RichTable(
            "#detailAssetsTable",
            endpoint,
            ["Date", "Amount", "Account"],
            10
        );
    }
});
