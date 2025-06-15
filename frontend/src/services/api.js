import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

const api = {
  uploadPortfolio: async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await axios.post(`${API_BASE_URL}/upload`, formData);
    return response.data;
  },

  fetchAllPortfolios: async () => {
    const response = await axios.get(`${API_BASE_URL}/portfolios`);
    return response.data;
  },

  fetchPortfolioDetails: async (id) => {
    const response = await axios.get(`${API_BASE_URL}/portfolio/${id}`);
    return response.data;
  },

  fetchProductShelf: async () => {
    const response = await axios.get(`${API_BASE_URL}/product-shelf`);
    return response.data;
  },

  // Re-adding fetchClients function
  fetchClients: async () => {
    const response = await axios.get(`${API_BASE_URL}/clients`);
    return response.data;
  },

  askComplianceQuestion: async (portfolioId, question) => {
    const response = await axios.post(
      `${API_BASE_URL}/ask/${portfolioId}`,
      null,
      {
        params: {
          question: question,
        },
      }
    );
    return response.data;
  },
};

export default api;
