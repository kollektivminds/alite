// This gets the base URL of your backend from an environment variable.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * A helper function to handle API requests and responses.
 * @param {string} endpoint - The API endpoint to call (e.g., '/lookup').
 * @param {object} options - The options for the fetch call (method, body, etc.).
 * @returns {Promise<object>} The JSON response from the API.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    // 'Authorization': `Bearer ${getAuthToken()}`,
  };

  const config = {
    ...options,
    headers: { ...headers, ...options.headers },
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    // Handle HTTP errors (like 404, 500)
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
  }
  
  return response.json();
}

// --- API functions ---

export const apiClient = {
  lookupWord: (word, lang) => {
    return request('/api/lookup', {
      method: 'POST',
      body: JSON.stringify({ word, lang }),
    });
  },
  
  getPartsOfSpeechMenu: () => {
    return request('/api/menu/parts-of-speech'); // GET is the default method
  },
  
  authenticateUser: (userData) => {
    return request('/api/authenticate', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },
  // ... add a function for every endpoint you have
};