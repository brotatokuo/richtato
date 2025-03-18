const currencyInputs = document.getElementsByClassName('currency-input');
console.log('Currency inputs:', currencyInputs);
Array.from(currencyInputs).forEach(currencyInput => {

    currencyInput.addEventListener('input', () => {
        const value = currencyInput.value;
        const validCharacters = /^[0-9+\-*/().=]*$/;
        if (!validCharacters.test(value)) {
            currencyInput.value = value.replace(/[^0-9+\-*/().=]/g, '');
        }
    });

    currencyInput.addEventListener('blur', () => {
        let balance = currencyInput.value;

        if (balance) {
            let newBalance = computeBalance(balance);

            if (newBalance) {
                currencyInput.value = newBalance;
                console.log('New balance:', newBalance);
            }
        }
    });
});

const descriptionInput = document.getElementById('expense-description');
descriptionInput.addEventListener('blur', () => {
    const description = descriptionInput.value;
    guessCategoryFromDescription(description);
});

function guessCategoryFromDescription(description) {
    console.log('Guessing category for:', description);
    // Encode the description before sending it
    const url = `/expense/guess-category/?description=${encodeURIComponent(description)}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.category) {
                console.log('Category found:', data.category);
                const categoryInput = document.getElementById('category');
                categoryInput.value = data.category;
            } else {
                console.log('No category found');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });


}

function computeBalance(balance) {
    if (balance.startsWith('=')) {
        try {
            balance = eval(balance.slice(1));
            console.log('Evaluated formula:', balance);
        } catch (error) {
            console.error('Invalid formula:', error);
            return;
        }
    }
    else {
        balance = eval(balance);;
    }
    balance = parseFloat(balance).toFixed(2);
    return balance;
}