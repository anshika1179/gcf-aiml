document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('search-input');
    const loadingDiv = document.getElementById('loading');
    const resultsSection = document.getElementById('results-section');
    const recommendationList = document.getElementById('recommendation-list');

    // Hide results initially if empty
    resultsSection.style.display = 'none';

    searchBtn.addEventListener('click', fetchRecommendations);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') fetchRecommendations();
    });

    function fetchRecommendations() {
        const query = searchInput.value.trim();
        if (!query) return;

        // UI Updates
        loadingDiv.classList.remove('hidden');
        resultsSection.style.display = 'none';
        recommendationList.innerHTML = '';
        
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
            resultsSection.style.display = 'block';
            
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
            resultsSection.style.display = 'block';
            displayError("Failed to fetch recommendations. Please check your connection.");
            console.error('Error:', error);
        });
    }

    function displayRecommendations(books) {
        if (!books || books.length === 0) {
            recommendationList.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; color: white; padding: 2rem;">
                    <h3>Your next great read is waiting.</h3>
                    <p style="opacity: 0.8; margin-top: 0.5rem;">Try searching for a different book to discover personalized recommendations.</p>
                </div>`;
            return;
        }

        books.forEach((book, index) => {
            const card = document.createElement('div');
            card.className = 'book-card';
            // Stagger animation delay
            card.style.animationDelay = `${index * 0.1}s`;
            
            // Heart Icon SVG
            const heartHtml = `
                <svg class="heart-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>`;
            
            // Cover Image Logic
            let coverHtml = '';
            if (book.cover && book.cover.startsWith('http')) {
                coverHtml = `<img src="${book.cover}" alt="Cover of ${book.title}" class="book-cover" onerror="this.onerror=null; this.outerHTML='<div class=\\'placeholder-cover\\'>Book Cover</div>';">`;
            } else {
                coverHtml = `<div class="placeholder-cover">BookNest</div>`;
            }

            // Info HTML
            const scorePercent = (book.score * 100).toFixed(1);
            const infoHtml = `
                <div class="book-info">
                    <div class="book-title">${book.title}</div>
                    <div class="book-author">by ${book.author}</div>
                    <div class="book-score">Match Score: ${scorePercent}%</div>
                </div>`;
            
            card.innerHTML = heartHtml + coverHtml + infoHtml;
            
            // Heart toggle logic
            const heartIcon = card.querySelector('.heart-icon');
            heartIcon.addEventListener('click', function(e) {
                e.stopPropagation();
                const isFilled = this.getAttribute('fill') === 'currentColor';
                this.setAttribute('fill', isFilled ? 'none' : 'currentColor');
                this.style.color = isFilled ? '#cbd5e0' : '#e53e3e';
            });

            recommendationList.appendChild(card);
        });
    }

    function displayError(message) {
        recommendationList.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; color: #fc8181; background: rgba(0,0,0,0.5); padding: 1rem; border-radius: 8px;">
                <p>Error: ${message}</p>
            </div>`;
    }
});
