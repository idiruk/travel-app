<script lang="ts">
  let idea = '';
  let result: string | null = null;
  let mapHtml: string | null = null;
  let loading = false;
  let error: string | null = null;
  let notifications: any[] = [];
  let pollInterval: any = null;

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
      if (!res.ok) throw new Error((await res.json()).detail || 'API error');
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
            error = "Failed to get status update.";
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
            } else if (statusData.result) {
              result = JSON.stringify(statusData.result, null, 2);
              mapHtml = null;
            } else {
              result = "No plan generated.";
              mapHtml = null;
            }
            loading = false;
          } else if (statusData.status === "error") {
            clearInterval(pollInterval);
            error = statusData.error ?? "Error during planning.";
            loading = false;
          }
          // else: still processing, keep polling
        } catch (err) {
          clearInterval(pollInterval);
          error = "Error polling for status.";
          loading = false;
        }
      }, 2000);
    } catch (err: any) {
      error = err?.message || 'API error.';
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
        <div class="notification">{note.message}</div>
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
      {@html mapHtml}
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
    background: #e5eafc;
    color: #1e40af;
    padding: 0.5rem 0.8rem;
    border-radius: 7px;
    margin-bottom: 0.4rem;
    font-size: 0.98rem;
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
    min-height: 340px;
    margin: 2rem 0;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(55,93,176,0.07);
    border: 1px solid #dbeafe;
    background: #f8fafc;
  }
  .footer {
    margin-top: 2rem;
    text-align: center;
    color: #777;
  }
</style>