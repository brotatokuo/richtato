// API utility functions
class APIClient {
  constructor() {
    this.baseURL = '';
    this.csrfToken = this.getCSRFToken();
  }

  getCSRFToken() {
    const cookieValue = document.cookie
      .match("(^|;)\\s*csrftoken\\s*=\\s*([^;]+)")
      ?.pop();
    return cookieValue || "";
  }

  async getUserID() {
    try {
      const response = await fetch("/get-user-id");
      const data = await response.json();
      return data.userID;
    } catch (error) {
      console.error('Error fetching user ID:', error);
      throw error;
    }
  }

  async makeRequest(url, options = {}) {
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrfToken,
      },
    };

    const mergedOptions = {
      ...defaultOptions,
      ...options,
      headers: { ...defaultOptions.headers, ...options.headers },
    };

    try {
      const response = await fetch(url, mergedOptions);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async get(url) {
    return this.makeRequest(url, { method: 'GET' });
  }

  async post(url, data) {
    return this.makeRequest(url, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put(url, data) {
    return this.makeRequest(url, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete(url) {
    return this.makeRequest(url, { method: 'DELETE' });
  }
}

// Export singleton instance
window.apiClient = new APIClient();
