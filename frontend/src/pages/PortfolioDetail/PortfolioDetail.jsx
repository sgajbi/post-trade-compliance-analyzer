// frontend/src/pages/PortfolioDetail/PortfolioDetail.jsx
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Tabs,
  Tab,
  Snackbar,
  Paper
} from '@mui/material';
import MuiAlert from '@mui/material/Alert';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import TabContext from '@mui/lab/TabContext';
import TabList from '@mui/lab/TabList';
import TabPanel from '@mui/lab/TabPanel';

const SnackbarAlert = React.forwardRef(function SnackbarAlert(props, ref) {
  return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

const API_BASE_URL = 'http://127.0.0.1:8000'; // Ensure this matches your FastAPI backend URL

function PortfolioDetail() {
  const { clientId, portfolioId } = useParams();
  const navigate = useNavigate();
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTab, setCurrentTab] = useState('summary');

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

  useEffect(() => {
    const fetchPortfolioDetails = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`${API_BASE_URL}/portfolio/${clientId}/${portfolioId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setPortfolio(data);
      } catch (e) {
        console.error("Failed to fetch portfolio details:", e);
        setError("Failed to load portfolio details. Please ensure the backend is running and the portfolio exists.");
        showSnackbar(e.message || "Failed to load details.", "error");
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioDetails();
  }, [clientId, portfolioId]);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  // Helper function to render data in a table, adapting to different structures
  const renderData = (data, type) => {
    if (!data || (Array.isArray(data) && data.length === 0)) {
      return <Typography sx={{ mt: 2 }}>No {type} found for this portfolio.</Typography>;
    }

    // Special handling for the 'summary' type to format specific fields
    if (type === 'summary') {
        const summaryKeys = Object.keys(data).filter(key => key !== 'id' && key !== '_id'); // Exclude the internal 'id' from summary view
        return (
            <TableContainer component={Paper} sx={{ mt: 2 }}>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell><Typography variant="subtitle2" fontWeight="bold">Detail</Typography></TableCell>
                            <TableCell><Typography variant="subtitle2" fontWeight="bold">Value</Typography></TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {summaryKeys.map((key) => (
                            <TableRow key={key}>
                                <TableCell>
                                    <Typography>{key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</Typography>
                                </TableCell>
                                <TableCell>
                                    {/* Handle specific keys for better display in summary */}
                                    {key === 'positions' && Array.isArray(data[key]) ? (
                                        <Typography>{data[key].length} Positions</Typography>
                                    ) : key === 'trades' && Array.isArray(data[key]) ? (
                                        <Typography>{data[key].length} Trades</Typography>
                                    ) : (key === 'analysis' || key === 'compliance_report') ? (
                                        // Format analysis and compliance report as pre-formatted JSON strings or lists
                                        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0, padding: 0 }}>
                                            {typeof data[key] === 'object' && data[key] !== null
                                                ? JSON.stringify(data[key], null, 2)
                                                : String(data[key])}
                                        </pre>
                                    ) : (
                                        // Default rendering for other primitive types or simple strings
                                        <Typography>{String(data[key])}</Typography>
                                    )}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        );
    }

    // NEW: Special handling for 'compliance_report' type to display the string directly
    if (type === 'compliance_report_display') {
        return (
            <Box sx={{ mt: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: '4px', backgroundColor: '#f9f9f9' }}>
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0, padding: 0 }}>
                    {String(data)}
                </pre>
            </Box>
        );
    }


    // Generic rendering for arrays of objects (used for 'positions', 'trades')
    const getColumns = () => {
        const keys = Object.keys(data[0]).filter(key => key !== 'id' && key !== '_id'); // Filter out internal IDs
        return keys.map(key => ({ key, label: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) }));
    };

    const columns = getColumns();

    return (
      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col.key}>
                  <Typography variant="subtitle2" fontWeight="bold">{col.label}</Typography>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((item, index) => (
                <TableRow key={item.id || index}> {/* Use item.id if available, else index */}
                    {columns.map((col) => (
                        <TableCell key={`${item.id || index}-${col.key}`}>
                            <Typography>{typeof item[col.key] === 'object' && item[col.key] !== null
                                ? JSON.stringify(item[col.key]) // Stringify objects within table cells if they occur
                                : String(item[col.key])}
                            </Typography>
                        </TableCell>
                    ))}
                </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading portfolio details...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!portfolio) {
    return (
      <Alert severity="warning" sx={{ mt: 2 }}>
        Portfolio details not found.
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Button
        variant="outlined"
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/')}
        sx={{ mb: 3 }}
      >
        Back to Dashboard
      </Button>

      <Typography variant="h4" component="h1" gutterBottom>
        Portfolio Details: {portfolio.client_id}/{portfolio.portfolio_id}
      </Typography>
      <Typography variant="subtitle1" gutterBottom>
        Date: {new Date(portfolio.date).toLocaleDateString()} | Uploaded At: {new Date(portfolio.uploaded_at).toLocaleString()}
      </Typography>

      <Box sx={{ width: '100%', typography: 'body1', mt: 3 }}>
        <TabContext value={currentTab}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <TabList onChange={handleTabChange} aria-label="portfolio details tabs">
              <Tab label="Summary" value="summary" />
              <Tab label="Positions" value="positions" />
              <Tab label="Trades" value="trades" />
              <Tab label="Compliance Report" value="compliance_report_tab" /> {/* Renamed for clarity */}
            </TabList>
          </Box>

          <TabPanel value="summary">
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Portfolio Summary</Typography>
            {renderData(portfolio, 'summary')}
          </TabPanel>

          <TabPanel value="positions">
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Positions</Typography>
            {renderData(portfolio.positions, 'positions')}
          </TabPanel>

          <TabPanel value="trades">
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Trades</Typography>
            {renderData(portfolio.trades, 'trades')}
          </TabPanel>

          {/* Updated TabPanel to display compliance_report */}
          <TabPanel value="compliance_report_tab">
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Compliance Report</Typography>
            {renderData(portfolio.compliance_report, 'compliance_report_display')}
          </TabPanel>
        </TabContext>
      </Box>

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

export default PortfolioDetail;