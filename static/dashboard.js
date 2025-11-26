let currentResults = null;
let proportionsChart = null;
let confidenceChart = null;

document.getElementById('measurementForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const heightCm = document.getElementById('height_cm').value;
    const heightInches = document.getElementById('height_inches').value;
    
    if (!heightCm && !heightInches) {
        alert('Please provide your height in either cm or inches');
        return;
    }
    
    const formData = new FormData();
    const imageFiles = document.getElementById('images').files;
    
    if (imageFiles.length === 0) {
        alert('Please select at least one image');
        return;
    }
    
    for (let file of imageFiles) {
        formData.append('images', file);
    }
    
    if (heightCm) formData.append('height_cm', heightCm);
    if (heightInches) formData.append('height_inches', heightInches);
    
    const gender = document.getElementById('gender').value;
    if (gender) formData.append('gender', gender);
    
    showPanel('loading');
    document.getElementById('submitBtn').disabled = true;
    
    try {
        const response = await fetch('/api/measure/enhanced', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to process images');
        }
        
        currentResults = await response.json();
        displayResults(currentResults);
        showPanel('results');
    } catch (error) {
        alert('Error: ' + error.message);
        showPanel('welcome');
    } finally {
        document.getElementById('submitBtn').disabled = false;
    }
});

document.getElementById('images').addEventListener('change', function(e) {
    const container = document.getElementById('previewContainer');
    container.innerHTML = '';
    
    for (let file of e.target.files) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.className = 'preview-image';
            container.appendChild(img);
        };
        reader.readAsDataURL(file);
    }
});

document.getElementById('height_cm').addEventListener('input', function() {
    if (this.value) document.getElementById('height_inches').value = '';
});

document.getElementById('height_inches').addEventListener('input', function() {
    if (this.value) document.getElementById('height_cm').value = '';
});

function showPanel(panelName) {
    document.getElementById('welcomePanel').style.display = panelName === 'welcome' ? 'block' : 'none';
    document.getElementById('loadingPanel').style.display = panelName === 'loading' ? 'block' : 'none';
    document.getElementById('resultsPanel').style.display = panelName === 'results' ? 'block' : 'none';
}

function displayResults(data) {
    document.getElementById('accuracyBadge').querySelector('.accuracy-value').textContent = 
        Math.round(data.accuracy_rating * 100) + '%';
    
    displayMeasurements(data.measurements);
    displayImageAnalyses(data.image_analyses);
    displayWarnings(data.warnings);
    createProportionsChart(data.measurements);
    createConfidenceChart(data.measurements);
}

function displayMeasurements(measurements) {
    const grid = document.getElementById('measurementsGrid');
    grid.innerHTML = '';
    
    const measurementLabels = {
        'chest_cm': 'Chest',
        'waist_cm': 'Waist',
        'hips_cm': 'Hips',
        'shoulder_cm': 'Shoulders',
        'inseam_cm': 'Inseam',
        'left_arm_cm': 'Left Arm',
        'right_arm_cm': 'Right Arm',
        'torso_cm': 'Torso'
    };
    
    const orderedKeys = ['chest_cm', 'waist_cm', 'hips_cm', 'shoulder_cm', 'inseam_cm', 'torso_cm', 'left_arm_cm', 'right_arm_cm'];
    
    for (const key of orderedKeys) {
        if (measurements[key]) {
            const m = measurements[key];
            const label = measurementLabels[key] || key.replace('_cm', '').replace('_', ' ');
            
            const item = document.createElement('div');
            item.className = 'measurement-item';
            item.innerHTML = `
                <div class="measurement-label">${label}</div>
                <div class="measurement-value">${m.value.toFixed(1)} cm</div>
                <div class="measurement-confidence">${Math.round(m.confidence * 100)}% confidence</div>
                <div class="confidence-bar-small">
                    <div class="confidence-fill-small" style="width: ${m.confidence * 100}%"></div>
                </div>
            `;
            grid.appendChild(item);
        }
    }
}

function displayImageAnalyses(analyses) {
    const container = document.getElementById('imageAnalysisContainer');
    container.innerHTML = '';
    
    for (const img of analyses) {
        const item = document.createElement('div');
        item.className = 'image-analysis-item';
        
        const icon = img.used ? '✓' : '⚠';
        const iconClass = img.used ? 'used' : 'unused';
        
        item.innerHTML = `
            <div class="image-analysis-icon ${iconClass}">${icon}</div>
            <div class="image-analysis-info">
                <div class="image-analysis-name">${img.name}</div>
                <div class="image-analysis-details">
                    ${img.view_type} view | Quality: ${Math.round(img.quality.overall_score * 100)}%
                </div>
            </div>
            <div class="image-analysis-score">${Math.round(img.pose_confidence * 100)}%</div>
        `;
        container.appendChild(item);
    }
}

function displayWarnings(warnings) {
    const card = document.getElementById('warningsCard');
    const list = document.getElementById('warningsList');
    
    if (warnings && warnings.length > 0) {
        card.style.display = 'block';
        list.innerHTML = warnings.map(w => `<li>${w}</li>`).join('');
    } else {
        card.style.display = 'none';
    }
}

function createProportionsChart(measurements) {
    const ctx = document.getElementById('proportionsChart').getContext('2d');
    
    if (proportionsChart) {
        proportionsChart.destroy();
    }
    
    const labels = [];
    const values = [];
    const colors = [];
    
    const colorMap = {
        'chest_cm': '#667eea',
        'waist_cm': '#764ba2',
        'hips_cm': '#f093fb',
        'shoulder_cm': '#4facfe',
        'inseam_cm': '#43e97b',
        'torso_cm': '#fa709a'
    };
    
    for (const [key, value] of Object.entries(measurements)) {
        if (key.includes('arm')) continue;
        labels.push(key.replace('_cm', '').replace('_', ' '));
        values.push(value.value);
        colors.push(colorMap[key] || '#999');
    }
    
    proportionsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Measurements (cm)',
                data: values,
                backgroundColor: colors,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0,0,0,0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

function createConfidenceChart(measurements) {
    const ctx = document.getElementById('confidenceChart').getContext('2d');
    
    if (confidenceChart) {
        confidenceChart.destroy();
    }
    
    const labels = [];
    const values = [];
    
    for (const [key, value] of Object.entries(measurements)) {
        labels.push(key.replace('_cm', '').replace('_', ' '));
        values.push(Math.round(value.confidence * 100));
    }
    
    confidenceChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Confidence %',
                data: values,
                fill: true,
                backgroundColor: 'rgba(102, 126, 234, 0.2)',
                borderColor: '#667eea',
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#667eea'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(0,0,0,0.1)' },
                    grid: { color: 'rgba(0,0,0,0.1)' },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function exportJSON() {
    if (!currentResults) return;
    
    const blob = new Blob([JSON.stringify(currentResults, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'body_measurements.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function printResults() {
    window.print();
}