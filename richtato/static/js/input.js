const currencyInputs = document.getElementsByClassName("currency-input");
Array.from(currencyInputs).forEach((currencyInput) => {
  currencyInput.addEventListener("input", () => {
    const value = currencyInput.value;
    const validCharacters = /^[0-9+\-*/().=]*$/;
    if (!validCharacters.test(value)) {
      currencyInput.value = value.replace(/[^0-9+\-*/().=]/g, "");
    }
  });

  currencyInput.addEventListener("blur", () => {
    let balance = currencyInput.value;

    if (balance) {
      let newBalance = computeBalance(balance);

      if (newBalance) {
        currencyInput.value = newBalance;
        console.log("New balance:", newBalance);
      }
    }
  });
});

const descriptionInput = document.getElementById("expense-description");

document.addEventListener("DOMContentLoaded", () => {
  const expenseGraph = new SimpleTimeseriesGraph(
    expenseLineChart,
    "/api/expenses/graph"
  );
  expenseGraph.init();

  const incomeGraph = new SimpleTimeseriesGraph(
    incomeLineChart,
    "/api/incomes/graph"
  );
  incomeGraph.init();

  const expenseTable = new RichTable(
    "#expenseTable",
    "/api/expenses/",
    ["date", "description", "amount", "account", "category"],
    5
  );

  const incomeTable = new RichTable(
    "#incomeTable",
    "/api/incomes/",
    ["date", "description", "amount", "account"],
    5
  );
});
