<script lang="ts">
  let idea = '';
  let result: string | null = null;
  let mapHtml: string | null = null;
  let loading = false;
  let error: string | null = null;
  let notifications: any[] = [];
  let pollInterval: any = null;
  let interactiveCities: any[] = []; // For storing cities from enriched_data

  async function handleCityClick(city: any) {
    const iframe = document.getElementById('map-iframe') as HTMLIFrameElement;
    if (!iframe) {
      console.error('Map iframe not found.');
      return;
    }
    const iframeDoc = iframe.contentDocument;
    if (!iframeDoc) {
      console.error('Map iframe document not accessible.');
      return;
    }

    // Based on previous subtask, popup text is "Citie: CityName"
    const expectedAltText = `Citie: ${city.name}`;
    // Attempt to find the marker icon by its alt attribute (assuming Folium sets it)
    // Leaflet default markers are <img> tags with class leaflet-marker-icon
    const markerIcon = iframeDoc.querySelector(`img.leaflet-marker-icon[alt="${expectedAltText}"]`) as HTMLElement;

    if (markerIcon) {
      markerIcon.click(); // Simulate a click to open popup and potentially center
    } else {
      console.warn(`Marker for city "${city.name}" with alt text "${expectedAltText}" not found. Brute-force searching popups.`);
      // Fallback: If alt attribute isn't set as expected, try to find by iterating all markers and their popups
      // This is more complex and less reliable as it requires popups to be accessible or opened.
      // For now, we'll just log a warning if the primary method fails.
      // A more robust solution might involve Leaflet.js direct API interaction if possible.
    }
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    loading = true;
    result = null;
    mapHtml = null;
    error = null;
    notifications = [];
    try {
      // Step 1: Start orchestration
      const res = await fetch('http://localhost:8005/plan-trip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_input: idea,
          user_id: 'frontend_demo'
        })
      });
      if (!res.ok) {
        // Attempt to parse the error detail from the response
        let detail = 'Failed to start trip planning.';
        try {
          const errorData = await res.json();
          detail = errorData.detail || detail;
        } catch (jsonError) {
          // If response is not JSON or other error, use the status text
          detail = res.statusText || detail;
        }
        throw new Error(detail);
      }
      const data = await res.json();
      let requestId = data.request_id;
      notifications = data.notifications || [];
      result = "⏳ Planning your trip, please wait...";
      mapHtml = null;
      // Step 2: Poll status endpoint
      pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`http://localhost:8005/status/${requestId}`);
          if (!statusRes.ok) {
            clearInterval(pollInterval);
            error = `Failed to get status update: ${statusRes.statusText || 'Server error'}`;
            loading = false;
            return;
          }
          const statusData = await statusRes.json();
          // Optionally display notifications if present
          if (statusData.notifications) {
            notifications = statusData.notifications;
          }
          if (statusData.status === "completed") {
            clearInterval(pollInterval);
            // Extract both travel plan and map HTML if available
            if (statusData.result && statusData.result.travel_plan) {
              result = statusData.result.travel_plan;
              mapHtml = statusData.result.map_html || null;
              // Populate interactiveCities
              interactiveCities = statusData.result?.enriched_data?.cities || [];
            } else if (statusData.result) {
              result = JSON.stringify(statusData.result, null, 2);
              mapHtml = null;
              interactiveCities = []; // Clear if no proper result structure
            } else {
              result = "No plan generated.";
              mapHtml = null;
              interactiveCities = [];
            }
            loading = false;
          } else if (statusData.status === "error") {
            clearInterval(pollInterval);
            interactiveCities = []; // Clear on error
            // Use the detailed error from backend, with a fallback
            error = statusData.error || "An error occurred during trip planning.";
            loading = false;
          }
          // else: still processing, keep polling
        } catch (err: any) { // Catch for polling fetch/json parsing
          clearInterval(pollInterval);
          error = `Error fetching status update: ${err.message || 'Unknown error'}`;
          loading = false;
        }
      }, 2000);
    } catch (err: any) { // Catch for initial plan-trip fetch
      error = err.message || "An API error occurred.";
      loading = false;
    }
  }
</script>

<main class="container">
  <header class="header">
    <svg class="map-icon" width="52" height="52" viewBox="0 0 24 24" fill="none">
      <path d="M2 6l7-3 7 3 6-3v17l-7 3-7-3-6 3V6z" stroke="#3B82F6" stroke-width="2" fill="#EFF6FF"/>
    </svg>
    <div>
      <h1>Travel Planner Assistant</h1>
      <p class="subtitle">Describe your dream trip and get instant inspiration.</p>
    </div>
  </header>
  <form class="input-form" on:submit={handleSubmit}>
    <textarea
      class="input-text"
      placeholder="E.g. 7-day food and culture trip in Spain: Madrid, Barcelona, Seville"
      bind:value={idea}
      required
      disabled={loading}
    ></textarea>
    <button class="submit-btn" type="submit" disabled={loading || !idea.trim()}>
      {loading ? 'Planning...' : 'Plan my trip'}
    </button>
  </form>

  {#if notifications.length}
    <div class="notifications">
      {#each notifications as note}
        <div
          class="notification notification-{note.type || 'info'}"
          role="alert"
        >
          <span class="icon">
            {#if note.type === 'error'}❌
            {:else if note.type === 'success'}✅
            {:else if note.type === 'warning'}⚠️
            {:else}ℹ️{/if}
          </span>
          {note.message}
        </div>
      {/each}
    </div>
  {/if}

  {#if error}
    <div class="error">{error}</div>
  {/if}

  {#if result}
    <div class="result-box">
      <h2>Your AI-Generated Travel Plan</h2>
      <pre class="result-text">{result}</pre>
    </div>
  {/if}

  {#if mapHtml}
    <div class="map-container" style="margin: 2rem 0;">
      {#if mapHtml} {#!--Re-check to ensure mapHtml is not null/empty before creating iframe--}
        <iframe id="map-iframe" title="Travel Map" srcdoc={mapHtml} style="width: 100%; height: 400px; border: none;"></iframe>
      {/if}
    </div>
  {/if}

  {#if interactiveCities.length > 0}
    <div class="interactive-cities">
      <h3>Key Cities:</h3>
      <p class="interactive-cities-hint">Click a city name to highlight it on the map.</p>
      <div class="city-buttons-container">
        {#each interactiveCities as city (city.name)}
          <button class="city-button" on:click={() => handleCityClick(city)}>
            {city.name}
          </button>
        {/each}
      </div>
    </div>
  {/if}

  <footer class="footer">
    <small>&copy; 2025 Travel Planner App</small>
  </footer>
</main>

<style>
  body {
    background: #f3f4f6;
    margin: 0;
    font-family: 'Segoe UI', Arial, sans-serif;
  }
  .container {
    background: #fff;
    max-width: 1200px;
    margin: 40px auto 0 auto;
    border-radius: 18px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.08);
    padding: 32px 28px 24px 28px;
    min-height: 480px;
    display: flex;
    flex-direction: column;
  }
  .header {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }
  .map-icon {
    flex-shrink: 0;
  }
  h1 {
    margin: 0 0 4px 0;
    font-size: 1.7rem;
    font-weight: bold;
    color: #234e82;
  }
  .subtitle {
    color: #475569;
    font-size: 1rem;
    margin: 0;
  }
  .input-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 2rem;
  }
  .input-text {
    font-size: 1.1rem;
    padding: 0.8rem;
    border-radius: 8px;
    border: 1px solid #cbd5e1;
    background: #f9fafb;
    min-height: 80px;
    resize: vertical;
  }
  .submit-btn {
    align-self: flex-end;
    padding: 0.5rem 2rem;
    background: #3B82F6;
    color: #fff;
    font-size: 1rem;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    transition: background 0.2s;
    font-weight: 600;
  }
  .submit-btn:disabled {
    background: #b3cdf6;
    cursor: not-allowed;
  }
  .error {
    color: #a00;
    margin: 1rem 0;
    font-weight: bold;
  }
  .notifications {
    margin: 0 0 1rem 0;
  }
  .notification {
    display: flex; /* For icon alignment */
    align-items: center; /* For icon alignment */
    padding: 0.75rem 1rem; /* Adjusted padding */
    border-radius: 8px; /* Slightly larger radius */
    margin-bottom: 0.5rem; /* Adjusted margin */
    font-size: 0.95rem; /* Slightly adjusted font size */
    border: 1px solid transparent; /* Base for border */
  }
  .notification .icon {
    margin-right: 0.75rem; /* Space between icon and text */
    font-size: 1.2em; /* Larger icon */
  }

  /* Info (default) */
  .notification-info {
    background-color: #e0eafc; /* Light blue */
    color: #1e40af; /* Dark blue */
    border-color: #b3c5ef; /* Blue border */
  }

  /* Error */
  .notification-error {
    background-color: #fde8e8; /* Light red */
    color: #c53030; /* Dark red */
    border-color: #f7c5c5; /* Red border */
  }

  /* Success */
  .notification-success {
    background-color: #e6fffa; /* Light green */
    color: #2f855a; /* Dark green */
    border-color: #b2f0e0; /* Green border */
  }

  /* Warning */
  .notification-warning {
    background-color: #fffbea; /* Light yellow/orange */
    color: #b45309; /* Dark yellow/orange */
    border-color: #ffe58f; /* Yellow/orange border */
  }

  .result-box {
    background: #f6f8fa;
    border-radius: 12px;
    padding: 1rem;
    margin-top: 2rem;
  }
  .result-text {
    background: #fff;
    padding: 1rem;
    border-radius: 8px;
    font-size: 1rem;
    margin-bottom: 1rem;
    white-space: pre-wrap;
    font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
  }
  .map-container {
    min-height: 400px; /* Adjusted to match iframe height */
    margin: 2rem 0;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(55,93,176,0.07);
    border: 1px solid #dbeafe;
    background: #f8fafc; /* Fallback if iframe content is transparent */
  }

  .interactive-cities {
    margin-top: 1.5rem;
    padding: 1rem;
    background-color: #f9fafb;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
  }
  .interactive-cities h3 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    color: #234e82;
    font-size: 1.2rem;
  }
  .interactive-cities-hint {
    font-size: 0.9rem;
    color: #6b7280;
    margin-bottom: 1rem;
  }
  .city-buttons-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }
  .city-button {
    padding: 0.5rem 1rem;
    font-size: 0.95rem;
    color: #3B82F6;
    background-color: #fff;
    border: 1px solid #3B82F6;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
  }
  .city-button:hover {
    background-color: #eff6ff;
    color: #2563eb;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  }

  .footer {
    margin-top: 2rem;
    text-align: center;
    color: #777;
  }
</style>