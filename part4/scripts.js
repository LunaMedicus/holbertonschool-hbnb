const API_BASE = 'http://127.0.0.1:5000/api/v1';

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function getPlaceIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

function checkAuthentication() {
    const token = getCookie('token');
    const loginLink = document.getElementById('login-link');
    if (loginLink) {
        loginLink.style.display = token ? 'none' : 'inline-block';
    }
    return token;
}

async function apiRequest(url, options = {}) {
    const token = getCookie('token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(url, { ...options, headers: { ...headers, ...options.headers } });
    if (response.status === 401) {
        document.cookie = 'token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        window.location.href = 'login.html';
        return null;
    }
    return response;
}

function renderStars(rating) {
    return '\u2605'.repeat(rating) + '\u2606'.repeat(5 - rating);
}

function createPlaceCard(place) {
    const card = document.createElement('article');
    card.className = 'place-card';
    card.dataset.price = place.price;

    const priceDisplay = typeof place.price === 'number'
        ? `$${place.price.toFixed(2)}`
        : `$${place.price}`;

    card.innerHTML = `
        <div class="card-content">
            <h3>${place.title}</h3>
            <p class="card-price">${priceDisplay} per night</p>
            <a href="place.html?id=${place.id}" class="details-button">View Details</a>
        </div>
    `;
    return card;
}

async function fetchPlaces() {
    try {
        const response = await fetch(`${API_BASE}/places/`);
        if (!response.ok) return [];
        const places = await response.json();
        displayPlaces(places);
    } catch (error) {
        console.error('Error fetching places:', error);
    }
}

function displayPlaces(places) {
    const container = document.getElementById('places-list');
    if (!container) return;
    container.innerHTML = '';
    places.forEach(place => {
        const card = createPlaceCard(place);
        container.appendChild(card);
    });
}

async function fetchPlaceDetails(placeId) {
    try {
        const response = await fetch(`${API_BASE}/places/${placeId}`);
        if (!response.ok) {
            document.getElementById('place-details').innerHTML = '<p>Place not found.</p>';
            return;
        }
        const place = await response.json();
        displayPlaceDetails(place);
        fetchReviewsForPlace(placeId);
    } catch (error) {
        console.error('Error fetching place details:', error);
    }
}

function displayPlaceDetails(place) {
    const container = document.getElementById('place-details');
    if (!container) return;

    const priceDisplay = typeof place.price === 'number'
        ? `$${place.price.toFixed(2)}`
        : `$${place.price}`;

    const amenitiesHtml = place.amenities && place.amenities.length > 0
        ? `<div class="amenities"><h3>Amenities</h3>${place.amenities.map(a => `<span class="amenity-tag">${a.name}</span>`).join('')}</div>`
        : '';

    const ownerName = place.owner
        ? `${place.owner.first_name} ${place.owner.last_name}`
        : 'Unknown';

    container.innerHTML = `
        <div class="place-info">
            <h1>${place.title}</h1>
            <p class="price">${priceDisplay} per night</p>
            <p class="host">Hosted by <span>${ownerName}</span></p>
            <p class="description">${place.description || 'No description available.'}</p>
            ${amenitiesHtml}
        </div>
    `;
}

async function fetchReviewsForPlace(placeId) {
    try {
        const response = await fetch(`${API_BASE}/places/${placeId}/reviews`);
        if (!response.ok) return;
        const reviews = await response.json();
        displayReviews(reviews);
    } catch (error) {
        console.error('Error fetching reviews:', error);
    }
}

function displayReviews(reviews) {
    const container = document.getElementById('reviews-list');
    if (!container) return;
    container.innerHTML = '';

    if (!reviews || reviews.length === 0) {
        container.innerHTML = '<p class="no-reviews">No reviews yet. Be the first to leave one!</p>';
        return;
    }

    reviews.forEach(review => {
        const card = document.createElement('article');
        card.className = 'review-card';
        card.innerHTML = `
            <div class="review-header">
                <span class="reviewer">${review.user_id}</span>
                <span class="stars">${renderStars(review.rating)}</span>
            </div>
            <p class="comment">${review.text}</p>
        `;
        container.appendChild(card);
    });
}

async function loginUser(email, password) {
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (response.ok) {
            const data = await response.json();
            document.cookie = `token=${data.access_token}; path=/; SameSite=Lax`;
            window.location.href = 'index.html';
        } else {
            const errorEl = document.getElementById('error-message');
            if (errorEl) {
                errorEl.textContent = 'Invalid email or password. Please try again.';
            }
        }
    } catch (error) {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.textContent = 'An error occurred. Please try again.';
        }
    }
}

async function submitReview(placeId, text, rating) {
    const token = getCookie('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/reviews/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                text: text,
                rating: parseInt(rating),
                place_id: placeId
            })
        });

        if (response.ok) {
            return { success: true };
        } else {
            const data = await response.json();
            return { success: false, error: data.error || 'Failed to submit review' };
        }
    } catch (error) {
        return { success: false, error: 'An error occurred. Please try again.' };
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;

    if (path.endsWith('login.html') || path.endsWith('login')) {
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            const token = getCookie('token');
            if (token) {
                window.location.href = 'index.html';
                return;
            }
            loginForm.addEventListener('submit', (event) => {
                event.preventDefault();
                const email = document.getElementById('email').value.trim();
                const password = document.getElementById('password').value;
                loginUser(email, password);
            });
        }
    }

    if (path.endsWith('index.html') || path.endsWith('/') || path.endsWith('index') || path === '/') {
        checkAuthentication();
        fetchPlaces();

        const priceFilter = document.getElementById('price-filter');
        if (priceFilter) {
            priceFilter.addEventListener('change', (event) => {
                const selectedPrice = event.target.value;
                const cards = document.querySelectorAll('.place-card');
                cards.forEach(card => {
                    const price = parseFloat(card.dataset.price);
                    if (selectedPrice === 'all' || price <= parseFloat(selectedPrice)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        }
    }

    if (path.endsWith('place.html') || path.endsWith('place')) {
        const token = checkAuthentication();
        const placeId = getPlaceIdFromURL();
        if (placeId) {
            fetchPlaceDetails(placeId);
        }

        const addReviewSection = document.getElementById('add-review');
        if (addReviewSection) {
            if (token) {
                addReviewSection.style.display = 'block';
            } else {
                addReviewSection.style.display = 'none';
            }
        }

        const reviewForm = document.getElementById('review-form-inline');
        if (reviewForm && token && placeId) {
            reviewForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const text = document.getElementById('review-text').value.trim();
                const rating = document.getElementById('review-rating').value;
                if (!text) return;
                const result = await submitReview(placeId, text, rating);
                if (result.success) {
                    document.getElementById('review-message').textContent = 'Review submitted successfully!';
                    document.getElementById('review-message').className = 'success-message';
                    reviewForm.reset();
                    fetchReviewsForPlace(placeId);
                } else {
                    document.getElementById('review-message').textContent = result.error;
                    document.getElementById('review-message').className = 'error-message';
                }
            });
        }
    }

    if (path.endsWith('add_review.html') || path.endsWith('add_review')) {
        const token = getCookie('token');
        if (!token) {
            window.location.href = 'index.html';
            return;
        }

        const placeId = getPlaceIdFromURL();
        if (placeId) {
            fetch(`${API_BASE}/places/${placeId}`)
                .then(res => res.ok ? res.json() : null)
                .then(place => {
                    const display = document.getElementById('place-name-display');
                    if (display && place) {
                        display.textContent = `Reviewing: ${place.title}`;
                    }
                })
                .catch(() => {});
        }

        const reviewForm = document.getElementById('review-form');
        if (reviewForm) {
            reviewForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const text = document.getElementById('text').value.trim();
                const rating = document.getElementById('rating').value;
                if (!text || !placeId) return;

                const result = await submitReview(placeId, text, rating);
                if (result.success) {
                    document.getElementById('review-message').textContent = 'Review submitted successfully! Redirecting...';
                    document.getElementById('review-message').className = 'success-message';
                    reviewForm.reset();
                    setTimeout(() => {
                        window.location.href = `place.html?id=${placeId}`;
                    }, 1500);
                } else {
                    document.getElementById('review-message').textContent = result.error;
                    document.getElementById('review-message').className = 'error-message';
                }
            });
        }
    }
});