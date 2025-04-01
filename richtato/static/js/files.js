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

    const fileUploadButton = document.getElementById('file-upload-button');
    fileUploadButton.addEventListener('click', () => {
        fileManager.uploadFiles();
    });
}

// Initialize the file manager
initializeFileManager();

class File {
    constructor(file, cardTypes, onRemoveCallback) {
        this.path = URL.createObjectURL(file); // Temporary path for preview
        this.name = file.name;
        this.file_size = file.size;
        this.file = file;
        this.cardTypes = cardTypes;
        console.log("cardTypes", cardTypes);
        this.onRemoveCallback = onRemoveCallback; // Store the callback for removal
    }

    // Create a dropdown for selecting the card account
    createDropdown() {
        const dropdown = document.createElement("select");
        dropdown.classList.add("card-account-dropdown");

        this.cardTypes.cards.forEach(cardType => {
            const option = document.createElement("option");
            option.value = cardType.value;
            option.textContent = cardType.label;
            dropdown.appendChild(option);
        });

        return dropdown;
    }

    // Create a remove button for this file
    createRemoveButton() {
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

        // Use the callback provided by FileManager
        removeButton.addEventListener('click', (e) => {
            e.stopPropagation();
            if (this.onRemoveCallback) {
                this.onRemoveCallback(this);
            }
        });

        return removeButton;
    }

    // Create the file box element with file details and a remove button
    createFileBox() {
        const fileBox = document.createElement('div');
        fileBox.id = `file-box-${this.name}`;
        fileBox.classList.add('file-box');
        fileBox.style.position = 'relative';

        // Create the remove button (X mark)
        const removeButton = this.createRemoveButton();
        fileBox.appendChild(removeButton);

        const cardBody = document.createElement('div');
        cardBody.classList.add('file-box-card-body');

        const img = document.createElement('img');
        if (this.name.endsWith('.xls') || this.name.endsWith('.xlsx')) {
            img.src = '../static/images/excel.svg';
        } else {
            img.src = '../static/images/csv.svg';
        }
        img.alt = this.name;

        const fileName = document.createElement('p');
        fileName.textContent = this.name;

        const fileSize = document.createElement('p');
        fileSize.textContent = `${(this.file_size / 1024).toFixed(2)} KB`;
        fileSize.classList.add('file-size');

        // Create dropdown from this instance
        this.dropdown = this.createDropdown();

        // Append elements to the cardBody
        cardBody.appendChild(img);
        cardBody.appendChild(fileName);
        cardBody.appendChild(fileSize);
        cardBody.appendChild(this.dropdown);

        // Append the cardBody to the fileBox
        fileBox.appendChild(cardBody);

        return fileBox;
    }
}


class FileManager {
    constructor(filesContainerId, statisticsContainerId, cardTypes) {
        this.filesContainer = document.getElementById(filesContainerId);
        this.statisticsContainer = document.getElementById(statisticsContainerId);
        this.uploadedFiles = []; // Stores instances of File
        this.cardTypes = cardTypes;
    }

    // Validate if the file is of a valid type (Excel or CSV)
    isValidFileType(file) {
        const validTypes = [
            "application/vnd.ms-excel", // .xls
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx
            "text/csv" // .csv
        ];
        return validTypes.includes(file.type);
    }

    // Check if the file is a duplicate (based on name and size)
    isDuplicateFile(file) {
        return this.uploadedFiles.some(f => f.name === file.name && f.file_size === file.size);
    }

    // Add a new file and display it in the UI
    addFile(file) {
        if (!this.isValidFileType(file)) {
            alert(`${file.name} is not a valid Excel or CSV file.`);
            return;
        }

        if (this.isDuplicateFile(file)) {
            alert(`${file.name} has already been uploaded.`);
            return;
        }

        // Create a new File instance with a callback to removeFile
        const newFile = new File(file, this.cardTypes, (fileToRemove) => {
            this.removeFile(fileToRemove);
        });
        this.uploadedFiles.push(newFile);

        // Use the File's createFileBox method to generate the UI element
        const fileBox = newFile.createFileBox();
        this.filesContainer.appendChild(fileBox);

        // Show the statistics container if there are files
        this.updateStatisticsVisibility();
    }

    // Remove a file from the uploadedFiles array and the UI
    removeFile(file) {
        // Remove the file from the uploadedFiles array
        this.uploadedFiles = this.uploadedFiles.filter(f => f !== file);

        // Remove the file box from the UI
        const fileBox = document.getElementById(`file-box-${file.name}`);
        if (fileBox) {
            fileBox.remove();
        }

        // Update the visibility of the statistics container
        this.updateStatisticsVisibility();
    }

    // Update the visibility of the statistics container based on file count
    updateStatisticsVisibility() {
        if (this.uploadedFiles.length === 0) {
            this.statisticsContainer.style.display = 'none';
        } else {
            this.statisticsContainer.style.display = 'flex';
        }
    }

    async uploadFiles() {
        const formData = new FormData();

        // Append each file and its associated card account
        this.uploadedFiles.forEach(fileObj => {
            formData.append('files', fileObj.file);

            const selectedCardType = fileObj.dropdown.value;
            const selectedCardName = fileObj.dropdown.options[fileObj.dropdown.selectedIndex].textContent;

            formData.append('card_types', selectedCardType);
            formData.append('file_names', fileObj.name);
            formData.append('card_names', selectedCardName);

            console.log('File name:', fileObj.name, 'Card Type:', selectedCardType, 'Card Name:', selectedCardName);
        });

        const csrftoken = getCSRFToken();

        try {
            const response = await fetch('/expense/upload-card-statements/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Failed to upload files: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            alert('Files uploaded successfully!');
            return data;
        } catch (error) {
            console.error('Error uploading files:', error);
            alert('Error uploading files. Please try again.');
            throw error;
        }
    }
}

