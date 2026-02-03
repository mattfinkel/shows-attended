// Shows Attended - Frontend JavaScript

const API_BASE = window.location.origin;

// State
let currentView = 'shows';
let showsOffset = 0;
let bandsAdded = [];
let editBandsAdded = [];
let currentFilters = {
    showSearch: '',
    year: '',
    bandSearch: '',
    minShows: 1,
    venueSearch: '',
    minVenueShows: 1
};

// Utility Functions
function formatDate(dateStr) {
    // Parse as local date to avoid timezone issues
    // "2025-07-18" should display as July 18, not July 17
    const [year, month, day] = dateStr.split('-');
    const date = new Date(year, month - 1, day); // month is 0-indexed
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// API Calls
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (!response.ok) throw new Error('API request failed');
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast('Failed to load data', 'error');
        return null;
    }
}

async function loadShows(reset = false) {
    if (reset) showsOffset = 0;

    const params = new URLSearchParams({
        limit: 50,
        offset: showsOffset
    });

    if (currentFilters.showSearch) {
        params.append('band', currentFilters.showSearch);
    }
    if (currentFilters.year) {
        params.append('year', currentFilters.year);
    }

    const shows = await fetchAPI(`/api/shows?${params}`);
    if (!shows) return;

    const showsList = document.getElementById('shows-list');

    if (reset) {
        showsList.innerHTML = '';
    }

    if (shows.length === 0 && reset) {
        showsList.innerHTML = '<div class="empty-state"><div class="icon">🎸</div><div>No shows found</div></div>';
        return;
    }

    shows.forEach(show => {
        const showCard = document.createElement('div');
        showCard.className = 'show-card';

        // Create clickable band links
        const bandLinks = show.bands.map(band =>
            `<span class="band-link" data-band-name="${band}">${band}</span>`
        ).join(', ');

        showCard.innerHTML = `
            <button class="edit-btn" data-show-id="${show.id}">Edit</button>
            <div class="show-header">
                <div class="show-number">#${show.show_number}</div>
                <div class="show-date">${formatDate(show.date)}</div>
            </div>
            <div class="show-bands">${bandLinks || 'No bands listed'}</div>
            <div class="show-venue venue-link" data-venue-name="${show.venue_name}">${show.venue_name}</div>
            ${show.event ? `<div class="show-event event-link" data-event-name="${show.event}">${show.event}</div>` : ''}
        `;
        showsList.appendChild(showCard);
    });

    // Add click handlers for band and venue links
    addNavigationHandlers();

    // Add click handlers for edit buttons
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const showId = parseInt(e.target.dataset.showId);
            await openEditShowModal(showId);
        });
    });

    showsOffset += shows.length;
}

async function loadBands() {
    const params = new URLSearchParams({
        limit: 100,
        min_shows: currentFilters.minShows
    });

    if (currentFilters.bandSearch) {
        params.append('search', currentFilters.bandSearch);
    }

    const bands = await fetchAPI(`/api/bands/stats?${params}`);
    if (!bands) return;

    const bandsList = document.getElementById('bands-list');
    bandsList.innerHTML = '';

    if (bands.length === 0) {
        bandsList.innerHTML = '<div class="empty-state"><div class="icon">🎤</div><div>No bands found</div></div>';
        return;
    }

    bands.forEach(band => {
        const bandCard = document.createElement('div');
        bandCard.className = 'band-card';
        bandCard.innerHTML = `
            <div class="band-name">${band.name}</div>
            <div class="band-stats">Seen ${band.times_seen} time${band.times_seen !== 1 ? 's' : ''}</div>
        `;
        bandCard.onclick = () => showBandDetail(band.id);
        bandsList.appendChild(bandCard);
    });
}

async function loadVenues() {
    const params = new URLSearchParams({
        limit: 100,
        min_shows: currentFilters.minVenueShows
    });

    if (currentFilters.venueSearch) {
        params.append('search', currentFilters.venueSearch);
    }

    const venues = await fetchAPI(`/api/venues/stats?${params}`);
    if (!venues) return;

    const venuesList = document.getElementById('venues-list');
    venuesList.innerHTML = '';

    if (venues.length === 0) {
        venuesList.innerHTML = '<div class="empty-state"><div class="icon">📍</div><div>No venues found</div></div>';
        return;
    }

    venues.forEach(venue => {
        const venueCard = document.createElement('div');
        venueCard.className = 'venue-card';
        venueCard.innerHTML = `
            <div class="venue-name">${venue.name}</div>
            ${venue.location ? `<div class="venue-location">${venue.location}</div>` : ''}
            <div class="venue-stats">${venue.show_count} show${venue.show_count !== 1 ? 's' : ''}</div>
        `;
        venueCard.onclick = () => showVenueDetail(venue.id);
        venuesList.appendChild(venueCard);
    });
}

async function showBandDetail(bandId) {
    const data = await fetchAPI(`/api/bands/${bandId}/shows`);
    if (!data) return;

    const modal = document.getElementById('band-modal');
    const modalName = document.getElementById('band-modal-name');
    const modalStats = document.getElementById('band-modal-stats');
    const modalShows = document.getElementById('band-modal-shows');

    modalName.textContent = data.band_name;
    modalStats.textContent = `Seen ${data.times_seen} time${data.times_seen !== 1 ? 's' : ''}`;

    modalShows.innerHTML = '';
    data.shows.forEach(show => {
        const showCard = document.createElement('div');
        showCard.className = 'show-card';

        // Create clickable band links
        const bandLinks = show.bands.map(band =>
            `<span class="band-link" data-band-name="${band}">${band}</span>`
        ).join(', ');

        showCard.innerHTML = `
            <div class="show-header">
                <div class="show-number">#${show.show_number}</div>
                <div class="show-date">${formatDate(show.date)}</div>
            </div>
            <div class="show-bands">${bandLinks}</div>
            <div class="show-venue venue-link" data-venue-name="${show.venue_name}">${show.venue_name}</div>
            ${show.event ? `<div class="show-event event-link" data-event-name="${show.event}">${show.event}</div>` : ''}
        `;
        modalShows.appendChild(showCard);
    });

    addNavigationHandlers();

    modal.classList.add('active');
}

async function showVenueDetail(venueId) {
    const data = await fetchAPI(`/api/venues/${venueId}/shows`);
    if (!data) return;

    const modal = document.getElementById('venue-modal');
    const modalName = document.getElementById('venue-modal-name');
    const modalLocation = document.getElementById('venue-modal-location');
    const modalStats = document.getElementById('venue-modal-stats');
    const modalShows = document.getElementById('venue-modal-shows');

    modalName.textContent = data.venue_name;
    modalLocation.textContent = data.venue_location || '';
    modalStats.textContent = `${data.show_count} show${data.show_count !== 1 ? 's' : ''}`;

    modalShows.innerHTML = '';
    data.shows.forEach(show => {
        const showCard = document.createElement('div');
        showCard.className = 'show-card';

        // Create clickable band links
        const bandLinks = show.bands.map(band =>
            `<span class="band-link" data-band-name="${band}">${band}</span>`
        ).join(', ');

        showCard.innerHTML = `
            <div class="show-header">
                <div class="show-number">#${show.show_number}</div>
                <div class="show-date">${formatDate(show.date)}</div>
            </div>
            <div class="show-bands">${bandLinks || 'No bands listed'}</div>
            ${show.event ? `<div class="show-event event-link" data-event-name="${show.event}">${show.event}</div>` : ''}
        `;
        modalShows.appendChild(showCard);
    });

    addNavigationHandlers();

    modal.classList.add('active');
}

async function showEventDetail(eventId) {
    const data = await fetchAPI(`/api/events/${eventId}/shows`);
    if (!data) return;

    const modal = document.getElementById('event-modal');
    const modalName = document.getElementById('event-modal-name');
    const modalStats = document.getElementById('event-modal-stats');
    const modalShows = document.getElementById('event-modal-shows');

    modalName.textContent = data.event_name;
    modalStats.textContent = `${data.show_count} show${data.show_count !== 1 ? 's' : ''}`;

    modalShows.innerHTML = '';
    data.shows.forEach(show => {
        const showCard = document.createElement('div');
        showCard.className = 'show-card';

        // Create clickable band links
        const bandLinks = show.bands.map(band =>
            `<span class="band-link" data-band-name="${band}">${band}</span>`
        ).join(', ');

        showCard.innerHTML = `
            <div class="show-header">
                <div class="show-number">#${show.show_number}</div>
                <div class="show-date">${formatDate(show.date)}</div>
            </div>
            <div class="show-bands">${bandLinks || 'No bands listed'}</div>
            <div class="show-venue venue-link" data-venue-name="${show.venue_name}">${show.venue_name}</div>
        `;
        modalShows.appendChild(showCard);
    });

    addNavigationHandlers();

    modal.classList.add('active');
}

async function loadStats() {
    const summary = await fetchAPI('/api/stats/summary');
    if (!summary) return;

    document.getElementById('total-shows').textContent = summary.total_shows;
    document.getElementById('total-bands').textContent = summary.total_bands;
    document.getElementById('total-venues').textContent = summary.total_venues;

    const firstYear = new Date(summary.first_show).getFullYear();
    const lastYear = new Date(summary.last_show).getFullYear();
    document.getElementById('date-range').textContent = `${firstYear}-${lastYear}`;

    // Years list
    const years = await fetchAPI('/api/stats/by-year');
    const yearsList = document.getElementById('years-list');
    yearsList.innerHTML = '';

    if (years) {
        years.forEach(yearData => {
            const item = document.createElement('div');
            item.className = 'year-item';
            item.innerHTML = `
                <div class="year-number">${yearData.year}</div>
                <div class="year-count">${yearData.show_count} show${yearData.show_count !== 1 ? 's' : ''}</div>
            `;
            item.onclick = () => showYearDetail(yearData.year);
            yearsList.appendChild(item);
        });
    }

    // Top bands
    const topBands = await fetchAPI('/api/bands/stats?limit=10&min_shows=1');
    const topBandsList = document.getElementById('top-bands-list');
    topBandsList.innerHTML = '';

    if (topBands) {
        topBands.forEach(band => {
            const item = document.createElement('div');
            item.className = 'top-item';
            item.innerHTML = `
                <div class="top-item-name">${band.name}</div>
                <div class="top-item-count">${band.times_seen}x</div>
            `;
            item.onclick = () => showBandDetail(band.id);
            topBandsList.appendChild(item);
        });
    }

    // Top venues
    const topVenues = await fetchAPI('/api/venues/stats?limit=10');
    const topVenuesList = document.getElementById('top-venues-list');
    topVenuesList.innerHTML = '';

    if (topVenues) {
        topVenues.forEach(venue => {
            const item = document.createElement('div');
            item.className = 'top-item';
            item.innerHTML = `
                <div class="top-item-name">${venue.name}</div>
                <div class="top-item-count">${venue.show_count}x</div>
            `;
            item.onclick = () => showVenueDetail(venue.id);
            topVenuesList.appendChild(item);
        });
    }
}

async function showYearDetail(year) {
    const data = await fetchAPI(`/api/stats/year/${year}`);
    if (!data) return;

    const modal = document.getElementById('year-modal');
    const modalTitle = document.getElementById('year-modal-title');
    const totalShows = document.getElementById('year-total-shows');
    const uniqueBands = document.getElementById('year-unique-bands');
    const uniqueVenues = document.getElementById('year-unique-venues');
    const topBands = document.getElementById('year-top-bands');
    const topVenues = document.getElementById('year-top-venues');

    modalTitle.textContent = year;
    totalShows.textContent = data.total_shows;
    uniqueBands.textContent = data.unique_bands;
    uniqueVenues.textContent = data.unique_venues;

    // Top bands for year
    topBands.innerHTML = '';
    data.top_bands.forEach(band => {
        const item = document.createElement('div');
        item.className = 'top-item';
        item.innerHTML = `
            <div class="top-item-name">${band.name}</div>
            <div class="top-item-count">${band.times_seen}x</div>
        `;
        item.onclick = () => {
            modal.classList.remove('active');
            showBandDetail(band.id);
        };
        topBands.appendChild(item);
    });

    // Top venues for year
    topVenues.innerHTML = '';
    data.top_venues.forEach(venue => {
        const item = document.createElement('div');
        item.className = 'top-item';
        item.innerHTML = `
            <div class="top-item-name">${venue.name}</div>
            <div class="top-item-count">${venue.show_count}x</div>
        `;
        item.onclick = () => {
            modal.classList.remove('active');
            showVenueDetail(venue.id);
        };
        topVenues.appendChild(item);
    });

    modal.classList.add('active');
}

async function autocomplete(input, type) {
    const query = input.value.trim();
    if (query.length < 2) return [];

    return await fetchAPI(`/api/autocomplete/${type}?q=${encodeURIComponent(query)}&limit=10`);
}

async function findBandByName(bandName) {
    const results = await fetchAPI(`/api/autocomplete/bands?q=${encodeURIComponent(bandName)}&limit=5`);
    // Look for exact match first, otherwise use first result
    return results.find(b => b.name.toLowerCase() === bandName.toLowerCase()) || results[0];
}

async function findVenueByName(venueName) {
    const results = await fetchAPI(`/api/autocomplete/venues?q=${encodeURIComponent(venueName)}&limit=5`);
    // Look for exact match first, otherwise use first result
    return results.find(v => v.name.toLowerCase() === venueName.toLowerCase()) || results[0];
}

async function findEventByName(eventName) {
    const results = await fetchAPI(`/api/autocomplete/events?q=${encodeURIComponent(eventName)}&limit=5`);
    // Look for exact match first, otherwise use first result
    return results.find(e => e.name.toLowerCase() === eventName.toLowerCase()) || results[0];
}

function addNavigationHandlers() {
    // Band links
    document.querySelectorAll('.band-link').forEach(link => {
        link.addEventListener('click', async (e) => {
            e.stopPropagation();
            const bandName = e.target.dataset.bandName;
            const band = await findBandByName(bandName);
            if (band) {
                showBandDetail(band.id);
            }
        });
    });

    // Venue links
    document.querySelectorAll('.venue-link').forEach(link => {
        link.addEventListener('click', async (e) => {
            e.stopPropagation();
            const venueName = e.target.dataset.venueName;
            const venue = await findVenueByName(venueName);
            if (venue) {
                showVenueDetail(venue.id);
            }
        });
    });

    // Event links
    document.querySelectorAll('.event-link').forEach(link => {
        link.addEventListener('click', async (e) => {
            e.stopPropagation();
            const eventName = e.target.dataset.eventName;
            const event = await findEventByName(eventName);
            if (event) {
                showEventDetail(event.id);
            }
        });
    });
}

// Event Handlers
function switchView(viewName) {
    // Update nav
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-view="${viewName}"]`).classList.add('active');

    // Update views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(`${viewName}-view`).classList.add('active');

    currentView = viewName;

    // Load data for view
    if (viewName === 'shows') {
        loadShows(true);
    } else if (viewName === 'bands') {
        loadBands();
    } else if (viewName === 'venues') {
        loadVenues();
    } else if (viewName === 'stats') {
        loadStats();
    } else if (viewName === 'add') {
        // Set today's date as default
        document.getElementById('show-date').valueAsDate = new Date();
    }
}

function setupAutocomplete(inputId, type, suggestionsId, onSelect) {
    const input = document.getElementById(inputId);
    const suggestions = document.getElementById(suggestionsId);

    input.addEventListener('input', debounce(async () => {
        const results = await autocomplete(input, type);

        if (!results || results.length === 0) {
            suggestions.classList.remove('active');
            return;
        }

        suggestions.innerHTML = '';
        results.forEach(item => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.textContent = type === 'venues' ? `${item.name} ${item.location || ''}` : item.name;
            div.onclick = () => {
                onSelect(item);
                suggestions.classList.remove('active');
            };
            suggestions.appendChild(div);
        });

        suggestions.classList.add('active');
    }, 300));

    // Close suggestions on outside click
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !suggestions.contains(e.target)) {
            suggestions.classList.remove('active');
        }
    });
}

function setupEventAutocomplete(inputId, suggestionsId) {
    const input = document.getElementById(inputId);
    const suggestions = document.getElementById(suggestionsId);

    input.addEventListener('input', debounce(async () => {
        const query = input.value.trim();
        if (query.length < 2) {
            suggestions.classList.remove('active');
            return;
        }

        const results = await fetchAPI(`/api/autocomplete/events?q=${encodeURIComponent(query)}&limit=10`);

        if (!results || results.length === 0) {
            suggestions.classList.remove('active');
            return;
        }

        suggestions.innerHTML = '';
        results.forEach(item => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.textContent = item.name;
            div.onclick = () => {
                input.value = item.name;
                suggestions.classList.remove('active');
            };
            suggestions.appendChild(div);
        });

        suggestions.classList.add('active');
    }, 300));

    // Close suggestions on outside click
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !suggestions.contains(e.target)) {
            suggestions.classList.remove('active');
        }
    });
}

function addBandChip(bandName) {
    if (bandsAdded.some(b => b.name === bandName)) {
        showToast('Band already added', 'error');
        return;
    }

    const order = bandsAdded.length + 1;
    bandsAdded.push({ name: bandName, order });

    const container = document.getElementById('bands-added');
    const chip = document.createElement('div');
    chip.className = 'band-chip';
    chip.innerHTML = `
        <span class="band-chip-order">${order}</span>
        <span>${bandName}</span>
        <button type="button" class="band-chip-remove" onclick="removeBandChip('${bandName}')">&times;</button>
    `;
    container.appendChild(chip);

    document.getElementById('band-input').value = '';
}

function removeBandChip(bandName) {
    bandsAdded = bandsAdded.filter(b => b.name !== bandName);

    // Re-render chips with updated order
    const container = document.getElementById('bands-added');
    container.innerHTML = '';

    bandsAdded.forEach((band, index) => {
        band.order = index + 1;
        const chip = document.createElement('div');
        chip.className = 'band-chip';
        chip.innerHTML = `
            <span class="band-chip-order">${band.order}</span>
            <span>${band.name}</span>
            <button type="button" class="band-chip-remove" onclick="removeBandChip('${band.name}')">&times;</button>
        `;
        container.appendChild(chip);
    });
}

function removeEditBandChip(bandName) {
    editBandsAdded = editBandsAdded.filter(b => b.name !== bandName);

    // Re-render chips with updated order
    const container = document.getElementById('edit-bands-added');
    container.innerHTML = '';

    editBandsAdded.forEach((band, index) => {
        band.order = index + 1;
        const chip = document.createElement('div');
        chip.className = 'band-chip';
        chip.innerHTML = `
            <span class="band-chip-order">${band.order}</span>
            <span>${band.name}</span>
            <button type="button" class="band-chip-remove" onclick="removeEditBandChip('${band.name}')">&times;</button>
        `;
        container.appendChild(chip);
    });
}

async function openEditShowModal(showId) {
    const data = await fetchAPI(`/api/shows/${showId}`);
    if (!data) return;

    // Populate form
    document.getElementById('edit-show-id').value = data.id;
    document.getElementById('edit-show-date').value = data.date;
    document.getElementById('edit-show-venue').value = data.venue_name;
    document.getElementById('edit-show-event').value = data.event || '';

    // Populate bands
    editBandsAdded = data.bands.map(b => ({ name: b.name, order: b.order }));
    const container = document.getElementById('edit-bands-added');
    container.innerHTML = '';

    editBandsAdded.forEach(band => {
        const chip = document.createElement('div');
        chip.className = 'band-chip';
        chip.innerHTML = `
            <span class="band-chip-order">${band.order}</span>
            <span>${band.name}</span>
            <button type="button" class="band-chip-remove" onclick="removeEditBandChip('${band.name}')">&times;</button>
        `;
        container.appendChild(chip);
    });

    // Open modal
    document.getElementById('edit-show-modal').classList.add('active');
}

async function submitEditShow(e) {
    e.preventDefault();

    const showId = parseInt(document.getElementById('edit-show-id').value);
    const showDate = document.getElementById('edit-show-date').value;
    const venueName = document.getElementById('edit-show-venue').value.trim();
    const event = document.getElementById('edit-show-event').value.trim();

    if (!showDate || !venueName) {
        showToast('Please fill in date and venue', 'error');
        return;
    }

    const data = {
        date: showDate,
        venue_name: venueName,
        event_name: event || null,
        bands: editBandsAdded.map(b => ({ band_name: b.name, order: b.order }))
    };

    const result = await fetchAPI(`/api/shows/${showId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (result) {
        showToast('Show updated successfully!');
        document.getElementById('edit-show-modal').classList.remove('active');
        loadShows(true);
    }
}

async function deleteShow() {
    if (!confirm('Are you sure you want to delete this show? This cannot be undone.')) {
        return;
    }

    const showId = parseInt(document.getElementById('edit-show-id').value);

    const result = await fetchAPI(`/api/shows/${showId}`, {
        method: 'DELETE'
    });

    if (result) {
        showToast('Show deleted successfully!');
        document.getElementById('edit-show-modal').classList.remove('active');
        loadShows(true);
    }
}

async function submitShow(e) {
    e.preventDefault();

    const showDate = document.getElementById('show-date').value;
    const venueName = document.getElementById('show-venue').value.trim();
    const venueLocation = document.getElementById('venue-location').value.trim();
    const event = document.getElementById('show-event').value.trim();

    if (!showDate || !venueName) {
        showToast('Please fill in date and venue', 'error');
        return;
    }

    // Check if venue is new (needs location)
    const existingVenue = await fetchAPI(`/api/autocomplete/venues?q=${encodeURIComponent(venueName)}&limit=5`);
    const isNewVenue = !existingVenue || !existingVenue.find(v => v.name.toLowerCase() === venueName.toLowerCase());

    // If it's a new venue and location was provided, create venue with location
    if (isNewVenue && venueLocation) {
        // The backend will create the venue when creating the show
        // We just need to pass the location info
        // For now, we'll need to update the backend to accept venue_location
    }

    const data = {
        date: showDate,
        venue_name: venueName,
        venue_location: venueLocation || null,
        event_name: event || null,
        bands: bandsAdded.map(b => ({ band_name: b.name, order: b.order }))
    };

    const result = await fetchAPI('/api/shows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (result) {
        showToast('Show added successfully!');

        // Reset form
        document.getElementById('add-show-form').reset();
        bandsAdded = [];
        document.getElementById('bands-added').innerHTML = '';
        document.getElementById('venue-location-group').style.display = 'none';
        document.getElementById('venue-location').value = '';

        // Switch to shows view
        switchView('shows');
    }
}

// Populate year filter
function populateYearFilter() {
    const select = document.getElementById('year-filter');
    const currentYear = new Date().getFullYear();
    const startYear = 2006; // Based on your first show

    for (let year = currentYear; year >= startYear; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        select.appendChild(option);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            switchView(btn.dataset.view);
        });
    });

    // Modal close
    document.querySelector('.modal-close').addEventListener('click', () => {
        document.getElementById('band-modal').classList.remove('active');
    });

    document.querySelector('.venue-modal-close').addEventListener('click', () => {
        document.getElementById('venue-modal').classList.remove('active');
    });

    document.querySelector('.year-modal-close').addEventListener('click', () => {
        document.getElementById('year-modal').classList.remove('active');
    });

    document.querySelector('.edit-show-close').addEventListener('click', () => {
        document.getElementById('edit-show-modal').classList.remove('active');
    });

    document.querySelector('.event-modal-close').addEventListener('click', () => {
        document.getElementById('event-modal').classList.remove('active');
    });

    // Click outside modal to close
    document.getElementById('band-modal').addEventListener('click', (e) => {
        if (e.target.id === 'band-modal') {
            e.target.classList.remove('active');
        }
    });

    document.getElementById('venue-modal').addEventListener('click', (e) => {
        if (e.target.id === 'venue-modal') {
            e.target.classList.remove('active');
        }
    });

    document.getElementById('year-modal').addEventListener('click', (e) => {
        if (e.target.id === 'year-modal') {
            e.target.classList.remove('active');
        }
    });

    document.getElementById('edit-show-modal').addEventListener('click', (e) => {
        if (e.target.id === 'edit-show-modal') {
            e.target.classList.remove('active');
        }
    });

    document.getElementById('event-modal').addEventListener('click', (e) => {
        if (e.target.id === 'event-modal') {
            e.target.classList.remove('active');
        }
    });

    // Show filters
    document.getElementById('show-search').addEventListener('input', debounce(() => {
        currentFilters.showSearch = document.getElementById('show-search').value;
        loadShows(true);
    }, 500));

    document.getElementById('year-filter').addEventListener('change', () => {
        currentFilters.year = document.getElementById('year-filter').value;
        loadShows(true);
    });

    document.getElementById('load-more-shows').addEventListener('click', () => {
        loadShows(false);
    });

    // Band filters
    document.getElementById('band-search').addEventListener('input', debounce(() => {
        currentFilters.bandSearch = document.getElementById('band-search').value;
        loadBands();
    }, 500));

    document.getElementById('min-shows-filter').addEventListener('change', () => {
        currentFilters.minShows = parseInt(document.getElementById('min-shows-filter').value);
        loadBands();
    });

    // Venue filters
    document.getElementById('venue-search').addEventListener('input', debounce(() => {
        currentFilters.venueSearch = document.getElementById('venue-search').value;
        loadVenues();
    }, 500));

    document.getElementById('min-venue-shows-filter').addEventListener('change', () => {
        currentFilters.minVenueShows = parseInt(document.getElementById('min-venue-shows-filter').value);
        loadVenues();
    });

    // Add show form
    document.getElementById('add-show-form').addEventListener('submit', submitShow);

    // Venue autocomplete with location handling
    setupAutocomplete('show-venue', 'venues', 'venue-suggestions', (venue) => {
        document.getElementById('show-venue').value = venue.name;
        // Hide location field if selecting existing venue
        document.getElementById('venue-location-group').style.display = 'none';
        document.getElementById('venue-location').value = '';
    });

    // Show location field when typing a new venue name
    document.getElementById('show-venue').addEventListener('input', debounce(async () => {
        const venueName = document.getElementById('show-venue').value.trim();
        if (venueName.length < 2) {
            document.getElementById('venue-location-group').style.display = 'none';
            return;
        }

        const results = await fetchAPI(`/api/autocomplete/venues?q=${encodeURIComponent(venueName)}&limit=5`);
        const exactMatch = results && results.find(v => v.name.toLowerCase() === venueName.toLowerCase());

        // Show location field if it's a new venue (no exact match)
        if (!exactMatch) {
            document.getElementById('venue-location-group').style.display = 'block';
        } else {
            document.getElementById('venue-location-group').style.display = 'none';
        }
    }, 500));

    // Event autocomplete
    setupEventAutocomplete('show-event', 'event-suggestions');

    // Band autocomplete
    setupAutocomplete('band-input', 'bands', 'band-suggestions', (band) => {
        addBandChip(band.name);
    });

    // Band input - also allow pressing Enter
    document.getElementById('band-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const bandName = e.target.value.trim();
            if (bandName) {
                addBandChip(bandName);
            }
        }
    });

    // Edit show form
    document.getElementById('edit-show-form').addEventListener('submit', submitEditShow);
    document.getElementById('delete-show-btn').addEventListener('click', deleteShow);

    // Edit venue autocomplete
    setupAutocomplete('edit-show-venue', 'venues', 'edit-venue-suggestions', (venue) => {
        document.getElementById('edit-show-venue').value = venue.name;
    });

    // Edit band autocomplete
    setupAutocomplete('edit-band-input', 'bands', 'edit-band-suggestions', (band) => {
        const editBandInput = document.getElementById('edit-band-input');
        if (editBandsAdded.some(b => b.name === band.name)) {
            showToast('Band already added', 'error');
            editBandInput.value = '';
            return;
        }

        const order = editBandsAdded.length + 1;
        editBandsAdded.push({ name: band.name, order });

        const container = document.getElementById('edit-bands-added');
        const chip = document.createElement('div');
        chip.className = 'band-chip';
        chip.innerHTML = `
            <span class="band-chip-order">${order}</span>
            <span>${band.name}</span>
            <button type="button" class="band-chip-remove" onclick="removeEditBandChip('${band.name}')">&times;</button>
        `;
        container.appendChild(chip);
        editBandInput.value = '';
    });

    // Edit band input - also allow pressing Enter
    document.getElementById('edit-band-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const bandName = e.target.value.trim();
            if (bandName) {
                if (editBandsAdded.some(b => b.name === bandName)) {
                    showToast('Band already added', 'error');
                    e.target.value = '';
                    return;
                }

                const order = editBandsAdded.length + 1;
                editBandsAdded.push({ name: bandName, order });

                const container = document.getElementById('edit-bands-added');
                const chip = document.createElement('div');
                chip.className = 'band-chip';
                chip.innerHTML = `
                    <span class="band-chip-order">${order}</span>
                    <span>${bandName}</span>
                    <button type="button" class="band-chip-remove" onclick="removeEditBandChip('${bandName}')">&times;</button>
                `;
                container.appendChild(chip);
                e.target.value = '';
            }
        }
    });

    // Populate filters
    populateYearFilter();

    // Load initial view
    loadShows(true);
});
