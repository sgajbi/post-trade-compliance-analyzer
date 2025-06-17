// frontend/src/hooks/useFetch.js
import { useState, useEffect, useCallback } from "react";

const useFetch = (url, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({})); // Try to parse error, but don't fail if not JSON
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }
      const json = await response.json();
      setData(json);
    } catch (e) {
      console.error("Fetch error:", e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [url, options]); // Dependencies for useCallback

  useEffect(() => {
    if (url) {
      // Only fetch if URL is provided
      fetchData();
    }
  }, [url, fetchData]); // Re-fetch when URL changes or fetchData (which has options) changes

  // Expose a refetch function for manual re-triggering
  return { data, loading, error, refetch: fetchData };
};

export default useFetch;
