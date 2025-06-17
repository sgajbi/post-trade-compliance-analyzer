// frontend/src/hooks/useFetch.js
import { useState, useEffect, useCallback, useRef } from "react"; // Use useRef

const useFetch = (url, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Use a ref to store the options. This ref will persist across renders.
  // We initialize it with the current options.
  const optionsRef = useRef(options);

  // Update the ref's current value if the 'options' object (passed to the hook)
  // itself changes reference. This ensures the hook uses the latest options
  // if they are truly dynamic and change from the caller.
  useEffect(() => {
    optionsRef.current = options;
  }, [options]); // This useEffect runs only when the 'options' prop changes reference.

  // fetchData is now independent of 'options' reference changes,
  // as it accesses the options via optionsRef.current.
  // It will only be re-created if the URL changes.
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Use optionsRef.current to get the latest stable options object
      const response = await fetch(url, optionsRef.current);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
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
  }, [url]); // Only 'url' is a dependency for fetchData

  // This useEffect triggers the fetch operation. It depends on 'url' and 'fetchData'.
  // Since 'fetchData' is now stable (only changes if 'url' changes),
  // this useEffect will also be stable.
  useEffect(() => {
    if (url) {
      // Only fetch if URL is provided
      fetchData();
    }
  }, [url, fetchData]);

  // Expose a refetch function for manual re-triggering
  return { data, loading, error, refetch: fetchData };
};

export default useFetch;
