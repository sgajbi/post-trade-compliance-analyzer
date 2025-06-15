// frontend/src/pages/Home/Home.jsx
import React, { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Button,
  TextField,
  FormControl,
  Grid,
  Snackbar
} from '@mui/material';
import MuiAlert from '@mui/material/Alert';

const SnackbarAlert = React.forwardRef(function SnackbarAlert(props, ref) {
  return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

const API_BASE_URL = 'http://127.0.0.1:8000'; // Ensure this matches your FastAPI backend URL

function Home() {
  const [portfolios, setPortfolios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('info');

  const showSnackbar = (message, severity) => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };

  const handleSnackbarClose = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackbarOpen(false);
  };

  const fetchPortfolios = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/portfolios`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setPortfolios(data);
    } catch (e) {
      console.error("Failed to fetch portfolios:", e);
      setError("Failed to load portfolios. Please ensure the backend is running.");
      showSnackbar(e.message || "Failed to load portfolios.", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolios();
  }, []);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleFileUpload = async () => {
    if (!file) {
      showSnackbar("Please choose a portfolio JSON file to upload.", "warning");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      showSnackbar(`Portfolio ${result.client_id}/${result.portfolio_id} uploaded and analyzed.`, "success");
      setFile(null); // Clear selected file
      // Reset file input value (important for re-uploading the same file)
      document.getElementById('file-upload').value = '';
      fetchPortfolios(); // Refresh the list of portfolios
    } catch (e) {
      console.error("Error uploading portfolio:", e);
      showSnackbar(e.message || "Upload failed.", "error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3} alignItems="center" mb={4}>
        <Grid item xs={12} md={6}>
          <Typography variant="h4" component="h1">
            Portfolio Dashboard
          </Typography>
        </Grid>
        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <Typography variant="subtitle1" component="label" htmlFor="file-upload" sx={{ mb: 1, display: 'block' }}>
                Upload Portfolio (JSON):
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <TextField
                    id="file-upload"
                    type="file"
                    accept=".json"
                    onChange={handleFileChange}
                    variant="outlined"
                    size="small"
                    sx={{ mr: 1, flexGrow: 1 }}
                    InputLabelProps={{ shrink: true }}
                />
                <Button
                    variant="contained"
                    onClick={handleFileUpload}
                    disabled={!file || uploading}
                >
                    {uploading ? <CircularProgress size={24} color="inherit" /> : 'Upload'}
                </Button>
            </Box>
          </FormControl>
        </Grid>
      </Grid>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Loading portfolios...</Typography>
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && portfolios.length === 0 && (
        <Typography sx={{ mt: 2 }}>No portfolios found. Upload one to get started!</Typography>
      )}

      {!loading && !error && portfolios.length > 0 && (
        <TableContainer component={Box} sx={{ mt: 4 }}>
          <Table sx={{ minWidth: 650 }} aria-label="portfolio table">
            <TableHead>
              <TableRow>
                <TableCell>Client ID</TableCell>
                <TableCell>Portfolio ID</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Uploaded At</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {portfolios.map((portfolio) => (
                <TableRow
                  key={portfolio.id}
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                >
                  <TableCell component="th" scope="row">
                    {portfolio.client_id}
                  </TableCell>
                  <TableCell>{portfolio.portfolio_id}</TableCell>
                  <TableCell>{new Date(portfolio.date).toLocaleDateString()}</TableCell>
                  <TableCell>{new Date(portfolio.uploaded_at).toLocaleString()}</TableCell>
                  <TableCell>
                    <Button
                      component={RouterLink}
                      to={`/portfolio/${portfolio.client_id}/${portfolio.portfolio_id}`}
                      variant="outlined"
                      size="small"
                    >
                      View Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <SnackbarAlert onClose={handleSnackbarClose} severity={snackbarSeverity}>
          {snackbarMessage}
        </SnackbarAlert>
      </Snackbar>
    </Box>
  );
}

export default Home;