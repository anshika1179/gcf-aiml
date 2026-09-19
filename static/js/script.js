document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('search-input');
    const loadingDiv = document.getElementById('loading');
    const resultsSection = document.getElementById('results-section');
    const recommendationList = document.getElementById('recommendation-list');

    searchBtn.addEventListener('click', () => {
        const query = searchInput.value.trim();
        if (!query) return;

        // Show loading, clear previous results
        loadingDiv.classList.remove('hidden');
        recommendationList.innerHTML = '';
        
        // Fetch recommendations from Flask backend
        fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => response.json())
        .then(data => {
            loadingDiv.classList.add('hidden');
            
            if (data.status === 'success' || data.status === 'warning') {
                displayRecommendations(data.recommendations);
                if (data.status === 'warning') {
                    console.warn(data.message);
                }
            } else {
                displayError(data.message);
            }
        })
        .catch(error => {
            loadingDiv.classList.add('hidden');
            displayError("Failed to fetch recommendations.");
            console.error('Error:', error);
        });
    });

    function displayRecommendations(books) {
        if (!books || books.length === 0) {
            recommendationList.innerHTML = '<p>No recommendations found.</p>';
            return;
        }

        books.forEach(book => {
            const card = document.createElement('div');
            card.className = 'book-card';
            
            const title = document.createElement('div');
            title.className = 'book-title';
            title.textContent = book.title;
            
            const author = document.createElement('div');
            author.className = 'book-author';
            author.textContent = `by ${book.author}`;
            
            const score = document.createElement('div');
            score.className = 'book-score';
            score.textContent = `Match Score: ${(book.score * 100).toFixed(1)}%`;
            
            card.appendChild(title);
            card.appendChild(author);
            card.appendChild(score);
            
            recommendationList.appendChild(card);
        });
    }

    function displayError(message) {
        recommendationList.innerHTML = `<p style="color: red;">Error: ${message}</p>`;
    }
});
