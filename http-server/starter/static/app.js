
// MyHTTPServer JavaScript
console.log('🚀 MyHTTPServer is running!');

document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded successfully');
    
    // Add click tracking to all links
    const links = document.querySelectorAll('a');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            console.log('Navigation to:', this.href);
        });
    });
    
    // Add some interactive features
    const title = document.querySelector('h1');
    if (title) {
        title.style.cursor = 'pointer';
        title.addEventListener('click', function() {
            this.style.color = this.style.color === 'red' ? '#4a5568' : 'red';
        });
    }
    
    // Show current time
    function updateTime() {
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.textContent = new Date().toLocaleString();
        }
    }
    
    updateTime();
    setInterval(updateTime, 1000);
});

// API demo function
async function fetchApiData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        const output = document.getElementById('api-output');
        if (output) {
            output.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }
    } catch (error) {
        console.error('API request failed:', error);
    }
}
    