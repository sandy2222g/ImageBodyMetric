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
    
    if (heightCm) {
        formData.append('height_cm', heightCm);
    }
    if (heightInches) {
        formData.append('height_inches', heightInches);
    }
    
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('submitBtn').disabled = true;
    
    try {
        const response = await fetch('/api/measure', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to process images');
        }
        
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('submitBtn').disabled = false;
    }
});

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    const measurementsDiv = document.getElementById('measurements');
    const metadataDiv = document.getElementById('metadata');
    const warningsDiv = document.getElementById('warnings');
    
    measurementsDiv.innerHTML = '';
    metadataDiv.innerHTML = '';
    warningsDiv.innerHTML = '';
    
    if (Object.keys(data.measurements).length === 0) {
        measurementsDiv.innerHTML = '<p style="text-align: center; color: #666;">No measurements could be extracted.</p>';
    } else {
        const grid = document.createElement('div');
        grid.className = 'measurement-grid';
        
        for (const [key, value] of Object.entries(data.measurements)) {
            const card = document.createElement('div');
            card.className = 'measurement-card';
            
            const name = key.replace('_cm', '').replace('_', ' ');
            const capitalizedName = name.split(' ').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
            
            card.innerHTML = `
                <div class="measurement-name">${capitalizedName}</div>
                <div class="measurement-value">${value.value.toFixed(1)} cm</div>
                <div class="confidence">Confidence: ${(value.confidence * 100).toFixed(0)}%</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${value.confidence * 100}%"></div>
                </div>
            `;
            
            grid.appendChild(card);
        }
        
        measurementsDiv.appendChild(grid);
    }
    
    metadataDiv.innerHTML = `
        <div class="metadata">
            <h3>Details</h3>
            <p><strong>Your Height:</strong> ${data.height_cm.toFixed(1)} cm (${(data.height_cm / 2.54).toFixed(1)} inches)</p>
            <p><strong>Images Used:</strong> ${data.used_images.join(', ')}</p>
        </div>
    `;
    
    if (data.warnings && data.warnings.length > 0) {
        warningsDiv.innerHTML = `
            <div class="warnings">
                <h3>Warnings</h3>
                <ul>
                    ${data.warnings.map(w => `<li>${w}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

document.getElementById('height_cm').addEventListener('input', function() {
    if (this.value) {
        document.getElementById('height_inches').value = '';
    }
});

document.getElementById('height_inches').addEventListener('input', function() {
    if (this.value) {
        document.getElementById('height_cm').value = '';
    }
});