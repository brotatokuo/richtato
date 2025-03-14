document.addEventListener('DOMContentLoaded', () => {
    // Add event listener to description
    const descriptionInput = document.getElementById('expense-description');
    descriptionInput.addEventListener('blur', () => {
        const description = descriptionInput.value;
        guessCategoryFromDescription(description);
    });
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
