// DOM Elements
const feedForm = document.getElementById('feedForm');
const resetBtn = document.getElementById('resetBtn');
const loadingSpinner = document.getElementById('loadingSpinner');
const feedContainer = document.getElementById('feedContainer');

// Chart instances
let scoreChart = null;
let compositionChart = null;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Initialize sliders
    initSliders();
    
    // Set up event listeners
    setupEventListeners();
    
    // Generate initial feed
    generateFeed();
});

// Initialize slider controls
function initSliders() {
    const sliders = document.querySelectorAll('.composition-slider');
    sliders.forEach(slider => {
        const valueElement = document.getElementById(`${slider.id}Value`);
        if (valueElement) {
            valueElement.textContent = `${slider.value}%`;
        }
        
        slider.addEventListener('input', function() {
            if (valueElement) {
                valueElement.textContent = `${this.value}%`;
            }
            updateSliderValues();
        });
    });
}

// Set up event listeners
function setupEventListeners() {
    // Form submission
    if (feedForm) {
        feedForm.addEventListener('submit', function(e) {
            e.preventDefault();
            generateFeed();
        });
    }
    
    // Reset button
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            resetToDefaults();
        });
    }
}

// Reset form to default values
function resetToDefaults() {
    document.getElementById('feedSize').value = 5;
    
    const defaults = {
        'personalConnections': 40,
        'interestBased': 30,
        'trending': 15,
        'discovery': 10,
        'community': 5
    };
    
    Object.entries(defaults).forEach(([id, value]) => {
        const slider = document.getElementById(id);
        const valueElement = document.getElementById(`${id}Value`);
        if (slider && valueElement) {
            slider.value = value;
            valueElement.textContent = `${value}%`;
        }
    });
    
    updateSliderValues();
    generateFeed();
}

// Update slider values to ensure they sum to 100%
function updateSliderValues() {
    const sliders = Array.from(document.querySelectorAll('.composition-slider'));
    const values = sliders.map(slider => parseInt(slider.value));
    const total = values.reduce((sum, value) => sum + value, 0);
    
    // If total is not 100, adjust the last slider
    if (total !== 100) {
        const lastSlider = sliders[sliders.length - 1];
        const lastValue = parseInt(lastSlider.value) + (100 - total);
        lastSlider.value = Math.max(0, Math.min(100, lastValue));
        document.getElementById(`${lastSlider.id}Value`).textContent = `${lastSlider.value}%`;
    }
}

// Generate feed based on current form values
function generateFeed() {
    const userId = parseInt(document.getElementById('userSelect').value);
    const size = parseInt(document.getElementById('feedSize').value);
    
    // Get composition values
    const composition = {
        personal_connections: parseInt(document.getElementById('personalConnections').value) / 100,
        interest_based: parseInt(document.getElementById('interestBased').value) / 100,
        trending: parseInt(document.getElementById('trending').value) / 100,
        discovery: parseInt(document.getElementById('discovery').value) / 100,
        community: parseInt(document.getElementById('community').value) / 100
    };
    
    // Show loading state
    loadingSpinner.classList.remove('d-none');
    feedContainer.innerHTML = '<p class="text-center my-5">Generating feed...</p>';
    
    // Make API call
    fetch('/api/generate_feed', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: userId,
            size: size,
            ...composition
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            renderFeed(data.feed);
            renderCharts(data.feed, data.composition);
        } else {
            throw new Error(data.error || 'Failed to generate feed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        feedContainer.innerHTML = `
            <div class="alert alert-danger" role="alert">
                Error generating feed: ${error.message}
            </div>
        `;
    })
    .finally(() => {
        loadingSpinner.classList.add('d-none');
    });
}

// Render the feed items
function renderFeed(feed) {
    if (!feed || feed.length === 0) {
        feedContainer.innerHTML = '<p class="text-muted text-center my-5">No items found for the selected criteria.</p>';
        return;
    }
    
    const feedItems = feed.map((item, index) => {
        const scorePercent = Math.round(item.score * 100);
        const scoreClass = scorePercent > 70 ? 'bg-success' : 
                          scorePercent > 40 ? 'bg-primary' : 'bg-secondary';
        
        return `
            <div class="card feed-item">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5 class="card-title">${item.title}</h5>
                            <h6 class="card-subtitle mb-2 text-muted">
                                ${item.type.charAt(0).toUpperCase() + item.type.slice(1)} 
                                <span class="badge bg-light text-dark">#${item.id}</span>
                            </h6>
                        </div>
                        <span class="badge ${scoreClass} score-badge">${scorePercent}%</span>
                    </div>
                    
                    <div class="mt-2">
                        ${renderTags(item.tags)}
                    </div>
                    
                    <div class="score-breakdown mt-3">
                        <div class="d-flex justify-content-between mb-1">
                            <small>Interest: ${(item.scores.interest * 100).toFixed(1)}%</small>
                            <small>Connection: ${(item.scores.connection * 100).toFixed(1)}%</small>
                            <small>Time: ${(item.scores.time * 100).toFixed(1)}%</small>
                        </div>
                        <div class="progress">
                            <div class="progress-bar interest" role="progressbar" 
                                 style="width: ${item.scores.interest * 100}%" 
                                 aria-valuenow="${item.scores.interest * 100}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">
                            </div>
                            <div class="progress-bar connection" role="progressbar" 
                                 style="width: ${item.scores.connection * 100}%" 
                                 aria-valuenow="${item.scores.connection * 100}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">
                            </div>
                            <div class="progress-bar time" role="progressbar" 
                                 style="width: ${item.scores.time * 100}%" 
                                 aria-valuenow="${item.scores.time * 100}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-2 text-muted">
                        <small>Author: User ${item.author} • ${new Date(item.timestamp).toLocaleString()}</small>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    feedContainer.innerHTML = feedItems;
}

// Render tags as badges
function renderTags(tags) {
    if (!tags || !tags.length) return '';
    return tags.map(tag => 
        `<span class="badge bg-light text-dark me-1">${tag}</span>`
    ).join('');
}

// Render charts
function renderCharts(feed, composition) {
    renderScoreChart(feed);
    renderCompositionChart(composition);
}

// Render score distribution chart
function renderScoreChart(feed) {
    const ctx = document.getElementById('scoreChart').getContext('2d');
    const labels = feed.map((item, index) => `#${index + 1} ${item.title.substring(0, 15)}...`);
    const scores = feed.map(item => item.score * 100);
    const backgroundColors = scores.map(score => 
        score > 70 ? 'rgba(25, 135, 84, 0.7)' : 
        score > 40 ? 'rgba(13, 110, 253, 0.7)' : 'rgba(108, 117, 125, 0.7)'
    );
    
    if (scoreChart) {
        scoreChart.destroy();
    }
    
    scoreChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score (%)',
                data: scores,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Score (%)'
                    }
                },
                x: {
                    ticks: {
                        autoSkip: false,
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const item = feed[context.dataIndex];
                            return [
                                `Score: ${(item.score * 100).toFixed(1)}%`,
                                `Interest: ${(item.scores.interest * 100).toFixed(1)}%`,
                                `Connection: ${(item.scores.connection * 100).toFixed(1)}%`,
                                `Time: ${(item.scores.time * 100).toFixed(1)}%`
                            ];
                        }
                    }
                },
                legend: {
                    display: false
                }
            }
        }
    });
}

// Render composition pie chart
function renderCompositionChart(composition) {
    const ctx = document.getElementById('compositionChart').getContext('2d');
    const labels = [
        'Personal Connections',
        'Interest Based',
        'Trending',
        'Discovery',
        'Community'
    ];
    
    const data = [
        composition.personal_connections * 100,
        composition.interest_based * 100,
        composition.trending * 100,
        composition.discovery * 100,
        composition.community * 100
    ];
    
    const backgroundColors = [
        'rgba(13, 110, 253, 0.7)',
        'rgba(25, 135, 84, 0.7)',
        'rgba(255, 193, 7, 0.7)',
        'rgba(13, 202, 240, 0.7)',
        'rgba(111, 66, 193, 0.7)'
    ];
    
    if (compositionChart) {
        compositionChart.destroy();
    }
    
    compositionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            return `${label}: ${value.toFixed(1)}%`;
                        }
                    }
                }
            }
        }
    });
}
