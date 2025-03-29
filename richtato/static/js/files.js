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

let uploadedFiles = [];
async function getCardTypes() {
    try {
        const response = await fetch('/get-card-types');
        if (!response.ok) {
            throw new Error('Failed to fetch card types');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching card types:', error);
        return [];
    }
}

let cardTypes = [];

// Fetch the card types and store them in cardTypes array
(async () => {
    cardTypes = await getCardTypes();
})();

function handleFiles(files) {
    const filesBoxes = document.getElementById('files-boxes');

    Array.from(files).forEach(file => {
        // Check file type (Excel or CSV)
        const fileType = file.type;
        const validTypes = [
            'application/vnd.ms-excel',                    // .xls
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
            'text/csv'                                      // .csv
        ];

        // If the file is not a valid type, ignore it
        if (!validTypes.includes(fileType)) {
            alert(`${file.name} is not a valid Excel or CSV file.`);
            return;  // Skip to the next file
        }

        // Check for duplicate file (based on name and size)
        if (uploadedFiles.some(f => f.name === file.name && f.size === file.size)) {
            alert(`${file.name} has already been uploaded.`);
            return;  // Skip this file if it's a duplicate
        }

        // Add the file to the list of uploaded files
        uploadedFiles.push({ name: file.name, size: file.size });

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

        // Attach event listener to remove the file box and file from uploadedFiles
        removeButton.addEventListener('click', () => {
            fileBox.remove();
            uploadedFiles = uploadedFiles.filter(f => f.name !== file.name || f.size !== file.size);
        });

        const icon = document.createElement('i');
        icon.classList.add('fa-solid', 'fa-download');

        // Create the file-box card body
        const cardBody = document.createElement('div');
        cardBody.classList.add('file-box-card-body');

        const img = document.createElement('img');
        if (file.name.endsWith('.xls') || file.name.endsWith('.xlsx')) {
            img.src = '../static/images/excel.svg';
        } else {
            img.src = '../static/images/csv.svg';
        }
        img.alt = file.name;

        const fileName = document.createElement('p');
        fileName.textContent = file.name;

        const dropdown = document.createElement('select');

        // Populate the dropdown using cardTypes (with value and label)
        cardTypes.forEach(cardType => {
            const option = document.createElement('option');
            option.value = cardType.value;
            option.textContent = cardType.label;
            dropdown.appendChild(option);
        });

        // Append img, fileName, and dropdown to cardBody
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