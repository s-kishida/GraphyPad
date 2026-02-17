let currentFilename = null;

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('csv-upload');
const fileInfo = document.getElementById('file-info');
const filenameSpan = document.getElementById('filename');
const configPanel = document.getElementById('config-panel');
const noDataMsg = document.getElementById('no-data-msg');
const xAxisSelect = document.getElementById('x-axis');
const yAxisContainer = document.getElementById('y-axis-container');
const generateBtn = document.getElementById('generate-btn');
const graphImage = document.getElementById('graph-image');
const placeholder = document.getElementById('placeholder');
const loader = document.getElementById('loader');
const pythonCode = document.getElementById('python-code');
const calcBtn = document.getElementById('calc-btn');
const calcColA = document.getElementById('calc-col-a');
const calcNewCol = document.getElementById('calc-new-col');
const calcFactor = document.getElementById('calc-factor');

// Event Listeners
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--accent-color)';
    dropZone.style.backgroundColor = 'var(--card-bg)';
});

dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = 'var(--border-color)';
    dropZone.style.backgroundColor = 'transparent';
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--border-color)';
    dropZone.style.backgroundColor = 'transparent';
    if (e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

generateBtn.addEventListener('click', generateGraph);
calcBtn.addEventListener('click', calculateColumn);

async function handleFileUpload(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
        alert('CSVファイルを選択してください');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        const data = await response.json();
        currentFilename = data.filename;

        updateSelectors(data.columns);

        // Update UI
        filenameSpan.textContent = data.filename;
        fileInfo.style.display = 'block';
        configPanel.style.display = 'block';
        noDataMsg.style.display = 'none';

    } catch (error) {
        console.error(error);
        alert('ファイルのアップロードに失敗しました');
    }
}

function updateSelectors(columns) {
    xAxisSelect.innerHTML = '';
    yAxisContainer.innerHTML = '';
    calcColA.innerHTML = '';

    columns.forEach((col, index) => {
        // X-axis and Calc Selects
        const optX = document.createElement('option');
        optX.value = col;
        optX.textContent = col;
        xAxisSelect.appendChild(optX);

        const optA = document.createElement('option');
        optA.value = col;
        optA.textContent = col;
        calcColA.appendChild(optA);

        // Y-axis Checkboxes
        const div = document.createElement('div');
        div.style.display = 'flex';
        div.style.alignItems = 'center';
        div.style.gap = '8px';
        div.style.marginBottom = '4px';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = col;
        checkbox.id = `y-col-${index}`;
        checkbox.className = 'y-axis-checkbox';
        if (index === 1) checkbox.checked = true; // Default check second column

        const label = document.createElement('label');
        label.htmlFor = `y-col-${index}`;
        label.textContent = col;
        label.style.fontSize = '0.85rem';
        label.style.marginBottom = '0';
        label.style.cursor = 'pointer';

        div.appendChild(checkbox);
        div.appendChild(label);
        yAxisContainer.appendChild(div);
    });
}

async function calculateColumn() {
    if (!currentFilename || !calcNewCol.value) return;

    const formData = new FormData();
    formData.append('filename', currentFilename);
    formData.append('new_col', calcNewCol.value);
    formData.append('col_a', calcColA.value);
    formData.append('factor', calcFactor.value);

    try {
        const response = await fetch('/calculate', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Calculation failed');

        const data = await response.json();
        updateSelectors(data.columns);
        alert('新しい列を追加しました');
        calcNewCol.value = '';

    } catch (error) {
        console.error(error);
        alert('計算に失敗しました');
    }
}

async function generateGraph() {
    if (!currentFilename) return;

    loader.style.display = 'flex';

    const formData = new FormData();
    formData.append('filename', currentFilename);
    formData.append('x_axis', xAxisSelect.value);

    // Collect selected Y columns
    const selectedYSteps = Array.from(document.querySelectorAll('.y-axis-checkbox:checked'))
        .map(cb => cb.value);

    if (selectedYSteps.length === 0) {
        alert('Y軸の列を少なくとも1つ選択してください');
        loader.style.display = 'none';
        return;
    }

    formData.append('y_axis_list', JSON.stringify(selectedYSteps));
    formData.append('x_name', document.getElementById('x-name').value);
    formData.append('x_unit', document.getElementById('x-unit').value);
    formData.append('y_name', document.getElementById('y-name').value);
    formData.append('y_unit', document.getElementById('y-unit').value);
    formData.append('title', document.getElementById('title').value);

    const xMin = document.getElementById('x-min').value;
    const xMax = document.getElementById('x-max').value;
    if (xMin) formData.append('x_min', xMin);
    if (xMax) formData.append('x_max', xMax);

    formData.append('width', document.getElementById('graph-width').value);
    formData.append('height', document.getElementById('graph-height').value);
    formData.append('font_title', document.getElementById('font-title').value);
    formData.append('font_label', document.getElementById('font-label').value);
    formData.append('font_tick', document.getElementById('font-tick').value);
    formData.append('marker_size', document.getElementById('marker-size').value);
    formData.append('line_width', document.getElementById('line-width').value);

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Generation failed');

        const data = await response.json();

        graphImage.src = data.image;
        graphImage.style.display = 'block';
        placeholder.style.display = 'none';
        pythonCode.textContent = data.code;

    } catch (error) {
        console.error(error);
        alert('グラフの生成に失敗しました');
    } finally {
        loader.style.display = 'none';
    }
}

function copyCode() {
    const code = pythonCode.textContent;
    navigator.clipboard.writeText(code).then(() => {
        alert('コードをコピーしました');
    });
}
