const API_BASE = (() => {
    if (typeof window === 'undefined') return '/api/v1';
    const h = window.location.hostname;
    if (h === 'localhost' || h === '127.0.0.1') return 'http://127.0.0.1:5000/api/v1';
    return '/api/v1';
})();

const TOKEN_KEY = 'hbnb_token';

function getToken() {
    return sessionStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
    sessionStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
    sessionStorage.removeItem(TOKEN_KEY);
}

function getPlaceIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

function checkAuthentication() {
    const token = getToken();
    const loginLink = document.getElementById('login-link');
    if (loginLink) {
        loginLink.style.display = token ? 'none' : 'inline-block';
    }
    return token;
}

function el(tag, attrs = {}, children = []) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
        if (k === 'className') e.className = v;
        else if (k === 'textContent') e.textContent = v;
        else if (k === 'style') Object.assign(e.style, v);
        else if (k.startsWith('data')) e.setAttribute(k.replace(/([A-Z])/g, '-$1').toLowerCase(), v);
        else if (k === 'href') e.setAttribute('href', v);
        else e.setAttribute(k, v);
    }
    for (const child of children) {
        if (typeof child === 'string') e.appendChild(document.createTextNode(child));
        else e.appendChild(child);
    }
    return e;
}

async function apiRequest(url, options = {}) {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const mergedHeaders = { ...headers, ...options.headers };
    const response = await fetch(url, { ...options, headers: mergedHeaders });
    if (response.status === 401 && token) {
        clearToken();
        window.location.href = 'login.html';
        return null;
    }
    return response;
}

function renderStars(rating) {
    const stars = el('span', { className: 'stars', 'aria-label': `${rating} out of 5 stars` });
    stars.textContent = '\u2605'.repeat(rating) + '\u2606'.repeat(5 - rating);
    return stars;
}

function setMessage(id, text, type) {
    const msg = document.getElementById(id);
    if (!msg) return;
    msg.textContent = text;
    msg.className = type;
}

function createPlaceCard(place) {
    const card = el('article', { className: 'place-card', dataPrice: place.price });

    const content = el('div', { className: 'card-content' });
    const title = el('h3', {}, [place.title]);
    const priceDisplay = typeof place.price === 'number'
        ? `$${place.price.toFixed(2)}`
        : `$${place.price}`;
    const price = el('p', { className: 'card-price' }, [`${priceDisplay} per night`]);
    const link = el('a', { className: 'details-button', href: `place.html?id=${place.id}` }, ['View Details']);
    content.appendChild(title);
    content.appendChild(price);
    content.appendChild(link);
    card.appendChild(content);
    return card;
}

async function fetchPlaces() {
    const container = document.getElementById('places-list');
    if (!container) return;
    try {
        const response = await fetch(`${API_BASE}/places/`);
        if (!response.ok) {
            container.innerHTML = '<p class="error-message">Failed to load places. Please try again later.</p>';
            return;
        }
        const places = await response.json();
        displayPlaces(places);
    } catch (error) {
        container.innerHTML = '<p class="error-message">Failed to load places. Please try again later.</p>';
    }
}

function displayPlaces(places) {
    const container = document.getElementById('places-list');
    if (!container) return;
    container.replaceChildren();
    if (!places || places.length === 0) {
        container.innerHTML = '<p class="no-reviews">No places available.</p>';
        return;
    }
    places.forEach(place => {
        container.appendChild(createPlaceCard(place));
    });
}

async function fetchPlaceDetails(placeId) {
    const container = document.getElementById('place-details');
    if (!container) return;
    try {
        const response = await fetch(`${API_BASE}/places/${placeId}`);
        if (!response.ok) {
            container.innerHTML = '<p class="error-message">Place not found.</p>';
            return;
        }
        const place = await response.json();
        displayPlaceDetails(place);
        fetchReviewsForPlace(placeId);
    } catch (error) {
        container.innerHTML = '<p class="error-message">Error loading place details. Please try again.</p>';
    }
}

function displayPlaceDetails(place) {
    const container = document.getElementById('place-details');
    if (!container) return;
    container.replaceChildren();

    const info = el('div', { className: 'place-info' });
    const priceDisplay = typeof place.price === 'number'
        ? `$${place.price.toFixed(2)}`
        : `$${place.price}`;
    const ownerName = place.owner
        ? `${place.owner.first_name} ${place.owner.last_name}`
        : 'Unknown';

    info.appendChild(el('h1', {}, [place.title]));
    info.appendChild(el('p', { className: 'price' }, [`${priceDisplay} per night`]));
    info.appendChild(el('p', { className: 'host' }, ['Hosted by ', el('span', {}, [ownerName])]));
    info.appendChild(el('p', { className: 'description' }, [place.description || 'No description available.']));

    if (place.amenities && place.amenities.length > 0) {
        const amenitiesDiv = el('div', { className: 'amenities' });
        amenitiesDiv.appendChild(el('h3', {}, ['Amenities']));
        place.amenities.forEach(a => {
            amenitiesDiv.appendChild(el('span', { className: 'amenity-tag' }, [a.name]));
        });
        info.appendChild(amenitiesDiv);
    }

    container.appendChild(info);
}

async function fetchReviewsForPlace(placeId) {
    const container = document.getElementById('reviews-list');
    if (!container) return;
    try {
        const response = await fetch(`${API_BASE}/places/${placeId}/reviews`);
        if (!response.ok) {
            container.innerHTML = '<p class="error-message">Failed to load reviews.</p>';
            return;
        }
        const reviews = await response.json();
        displayReviews(reviews);
    } catch (error) {
        container.innerHTML = '<p class="error-message">Failed to load reviews.</p>';
    }
}

function displayReviews(reviews) {
    const container = document.getElementById('reviews-list');
    if (!container) return;
    container.replaceChildren();

    if (!reviews || reviews.length === 0) {
        container.innerHTML = '<p class="no-reviews">No reviews yet. Be the first to leave one!</p>';
        return;
    }

    reviews.forEach(review => {
        const card = el('article', { className: 'review-card' });
        const header = el('div', { className: 'review-header' });
        const reviewerName = review.reviewer_name || review.user_id;
        header.appendChild(el('span', { className: 'reviewer' }, [reviewerName]));
        header.appendChild(renderStars(review.rating));
        card.appendChild(header);
        card.appendChild(el('p', { className: 'comment' }, [review.text]));
        container.appendChild(card);
    });
}

async function loginUser(email, password) {
    const errorEl = document.getElementById('error-message');
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        if (response.ok) {
            const data = await response.json();
            setToken(data.access_token);
            window.location.href = 'index.html';
        } else {
            if (errorEl) errorEl.textContent = 'Invalid email or password. Please try again.';
        }
    } catch (error) {
        if (errorEl) errorEl.textContent = 'An error occurred. Please try again.';
    }
}

async function submitReview(placeId, text, rating) {
    try {
        const response = await apiRequest(`${API_BASE}/reviews/`, {
            method: 'POST',
            body: JSON.stringify({ text, rating: parseInt(rating), place_id: placeId }),
        });
        if (!response) return { success: false, error: 'Session expired. Please log in again.' };
        if (response.ok) return { success: true };
        const data = await response.json();
        return { success: false, error: data.error || 'Failed to submit review' };
    } catch (error) {
        return { success: false, error: 'An error occurred. Please try again.' };
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    const body = document.body;

    // Login page
    if (path.endsWith('login.html') || path.endsWith('login')) {
        const token = getToken();
        if (token) {
            window.location.href = 'index.html';
            return;
        }
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const email = document.getElementById('email').value.trim();
                const password = document.getElementById('password').value;
                loginUser(email, password);
            });
        }
    }

    // Index / Places list
    if (path.endsWith('index.html') || path.endsWith('/') || path.endsWith('index') || path === '/') {
        checkAuthentication();
        fetchPlaces();
        const priceFilter = document.getElementById('price-filter');
        if (priceFilter) {
            priceFilter.addEventListener('change', (e) => {
                const selectedPrice = e.target.value;
                document.querySelectorAll('.place-card').forEach(card => {
                    const price = parseFloat(card.dataset.price);
                    if (isNaN(price)) { card.style.display = 'none'; return; }
                    card.style.display = (selectedPrice === 'all' || price <= parseFloat(selectedPrice))
                        ? 'block' : 'none';
                });
            });
        }
    }

    // Place details
    if (path.endsWith('place.html') || path.endsWith('place')) {
        const token = checkAuthentication();
        const placeId = getPlaceIdFromURL();
        if (placeId) fetchPlaceDetails(placeId);

        const addReviewSection = document.getElementById('add-review');
        if (addReviewSection) {
            if (token) {
                addReviewSection.classList.remove('hidden');
            } else {
                addReviewSection.classList.add('hidden');
            }
        }

        const reviewForm = document.getElementById('review-form-inline');
        if (reviewForm && token && placeId) {
            reviewForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const text = document.getElementById('review-text').value.trim();
                const rating = document.getElementById('review-rating').value;
                if (!text) return;
                const result = await submitReview(placeId, text, rating);
                if (result.success) {
                    setMessage('review-message', 'Review submitted successfully!', 'success-message');
                    reviewForm.reset();
                    fetchReviewsForPlace(placeId);
                } else {
                    setMessage('review-message', result.error, 'error-message');
                }
            });
        }
    }

    // Add review standalone
    if (path.endsWith('add_review.html') || path.endsWith('add_review')) {
        const token = getToken();
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
                    if (display && place) display.textContent = `Reviewing: ${place.title}`;
                })
                .catch(() => {
                    const display = document.getElementById('place-name-display');
                    if (display) display.textContent = 'Error loading place.';
                });
        }
        const reviewForm = document.getElementById('review-form');
        if (reviewForm) {
            reviewForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const text = document.getElementById('text').value.trim();
                const rating = document.getElementById('rating').value;
                if (!text || !placeId) return;
                const result = await submitReview(placeId, text, rating);
                if (result.success) {
                    setMessage('review-message', 'Review submitted successfully!', 'success-message');
                    reviewForm.reset();
                } else {
                    setMessage('review-message', result.error, 'error-message');
                }
            });
        }
    }
});