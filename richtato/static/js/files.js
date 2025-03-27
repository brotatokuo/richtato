const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragging');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragging');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragging');
    const files = e.dataTransfer.files;
    handleFiles(files);
});

dropZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    const files = fileInput.files;
    handleFiles(files);
});


function handleFiles(files) {
    const filesBoxes = document.getElementById('files-boxes');

    Array.from(files).forEach(file => {
        // Create the file-box div
        const fileBox = document.createElement('div');
        fileBox.classList.add('file-box');

        const removeButton = document.createElement('button');
        removeButton.innerHTML = '&times;'; // X mark
        removeButton.classList.add('remove-button');
        removeButton.style.position = 'absolute';
        removeButton.style.top = '5px';
        removeButton.style.right = '5px';
        removeButton.style.background = 'transparent';
        removeButton.style.border = 'none';
        removeButton.style.fontSize = '16px';
        removeButton.style.cursor = 'pointer';

        // Attach event listener to remove the file box
        removeButton.addEventListener('click', () => {
            fileBox.remove();
        });

        const icon = document.createElement('i');
        icon.classList.add('fa-solid', 'fa-download');

        // Create the file-box card body
        const cardBody = document.createElement('div');
        cardBody.classList.add('file-box-card-body');

        const img = document.createElement('img');
        img.src = '../static/images/png.svg';
        img.alt = file.name;

        const fileName = document.createElement('p');
        fileName.textContent = file.name;

        const dropdown = document.createElement('select');
        const options = ['Designer', 'Developer', 'Manager', 'Tester']; // Example options
        options.forEach(optionText => {
            const option = document.createElement('option');
            option.value = optionText;
            option.textContent = optionText;
            dropdown.appendChild(option);
        });

        // Append img, fileName, and designer to cardBody
        cardBody.appendChild(img);
        cardBody.appendChild(fileName);
        cardBody.appendChild(dropdown);

        // Create the file-box card footer
        const cardFooter = document.createElement('div');
        cardFooter.classList.add('file-box-card-footer');


        // Append the icon, cardBody, and cardFooter to the fileBox
        fileBox.appendChild(icon);
        fileBox.appendChild(cardBody);
        fileBox.appendChild(cardFooter);

        // Finally, append the fileBox to the filesBoxes container
        filesBoxes.appendChild(fileBox);
    });
}