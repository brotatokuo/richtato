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

async function initializeFileManager() {
    const cardTypes = await getCardTypes();

    // Create the fileManager instance after fetching cardTypes
    const fileManager = new FileManager('files-boxes', 'files-statistics', cardTypes);

    // Define the handleFiles function inside to ensure fileManager is available
    function handleFiles(files) {
        Array.from(files).forEach(file => fileManager.addFile(file));
    }

    // Now, set up event listeners after fileManager is initialized
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

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
}

// Initialize the file manager
initializeFileManager();


class FileManager {
    constructor(filesContainerId, statisticsContainerId, cardTypes) {
        this.filesContainer = document.getElementById(filesContainerId);
        this.statisticsContainer = document.getElementById(statisticsContainerId);
        this.uploadedFiles = [];
        this.cardTypes = cardTypes;
    }


    // Validate if the file is of a valid type (Excel or CSV)
    isValidFileType(file) {
        const validTypes = [
            'application/vnd.ms-excel',                    // .xls
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
            'text/csv'                                      // .csv
        ];
        return validTypes.includes(file.type);
    }

    // Check if the file is a duplicate (based on name and size)
    isDuplicateFile(file) {
        return this.uploadedFiles.some(f => f.name === file.name && f.size === file.size);
    }

    // Add a new file to the list and create a file box for it
    addFile(file) {
        if (!this.isValidFileType(file)) {
            alert(`${file.name} is not a valid Excel or CSV file.`);
            return;
        }

        if (this.isDuplicateFile(file)) {
            alert(`${file.name} has already been uploaded.`);
            return;
        }

        // Add the file to the uploadedFiles array
        this.uploadedFiles.push(file);

        // Create the file box element and append it to the container
        const fileBox = this.createFileBox(file);
        this.filesContainer.appendChild(fileBox);

        // Show the statistics container if there are files
        this.updateStatisticsVisibility();
    }

    // Remove a file from the uploadedFiles array and the UI
    removeFile(file) {
        // Remove the file from the uploadedFiles array
        this.uploadedFiles = this.uploadedFiles.filter(f => f.name !== file.name || f.size !== file.size);

        // Remove the file box from the UI
        const fileBox = document.getElementById(`file-box-${file.name}`);
        if (fileBox) {
            fileBox.remove();
        }

        // Update the visibility of the statistics container
        this.updateStatisticsVisibility();
    }

    // Create the file box element with file details and a remove button
    createFileBox(file) {
        const fileBox = document.createElement('div');
        fileBox.id = `file-box-${file.name}`;
        fileBox.classList.add('file-box');
        fileBox.style.position = 'relative';

        // Create the remove button (X mark)
        const removeButton = this.createRemoveButton(file);
        fileBox.appendChild(removeButton);

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

        const fileSize = document.createElement('p');
        fileSize.textContent = `${(file.size / 1024).toFixed(2)} KB`;
        fileSize.classList.add('file-size');

        const dropdown = this.createDropdown();

        // Append elements to the cardBody
        cardBody.appendChild(img);
        cardBody.appendChild(fileName);
        cardBody.appendChild(fileSize);
        cardBody.appendChild(dropdown);

        // Append the cardBody to the fileBox
        fileBox.appendChild(cardBody);

        return fileBox;
    }

    // Create a dropdown populated with card types
    createDropdown() {
        const dropdown = document.createElement('select');
        this.cardTypes.forEach(cardType => {
            const option = document.createElement('option');
            option.value = cardType.value;
            option.textContent = cardType.label;
            dropdown.appendChild(option);
        });
        return dropdown;
    }

    // Create a remove button (X mark) to remove the file
    createRemoveButton(file) {
        const removeButton = document.createElement('button');
        removeButton.innerHTML = '&times;';
        removeButton.classList.add('remove-button');
        removeButton.style.position = 'absolute';
        removeButton.style.top = '5px';
        removeButton.style.right = '5px';
        removeButton.style.background = 'transparent';
        removeButton.style.border = 'none';
        removeButton.style.fontSize = '16px';
        removeButton.style.cursor = 'pointer';

        // Attach event listener to remove the file when clicked
        removeButton.addEventListener('click', () => {
            this.removeFile(file);
        });

        return removeButton;
    }

    // Update the visibility of the statistics container based on file count
    updateStatisticsVisibility() {
        if (this.uploadedFiles.length === 0) {
            this.statisticsContainer.style.display = 'none';
        } else {
            this.statisticsContainer.style.display = 'flex';
        }
    }
}

