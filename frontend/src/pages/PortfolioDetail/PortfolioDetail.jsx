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
  Paper,
  List,
  ListItem,
  Divider,
  Accordion, 
  AccordionSummary, 
  AccordionDetails 
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'; 
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

  const [historicalReports, setHistoricalReports] = useState([]); 

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
        const response = await fetch(`${API_BASE_URL}/portfolio/${clientId}/${portfolioId}/detail`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setPortfolio(data);
      } catch (error) {
        setError(error);
        console.error("Error fetching portfolio details:", error);
        showSnackbar(`Error fetching portfolio details: ${error.message}`, 'error');
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioDetails();
  }, [clientId, portfolioId]);

  useEffect(() => {
    const fetchHistoricalReports = async () => {
      if (!clientId || !portfolioId) return;

      try {
        const response = await fetch(`${API_BASE_URL}/portfolio/${clientId}/${portfolioId}/history`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setHistoricalReports(data);
      } catch (error) {
        console.error("Error fetching historical reports:", error);
        showSnackbar(`Error fetching historical reports: ${error.message}`, 'error');
      }
    };

    fetchHistoricalReports();
  }, [clientId, portfolioId]);


  const handleChangeTab = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const renderData = (data, type) => {
    if (!data) {
      return <Typography>No data available.</Typography>;
    }

    if (type === 'summary') {
      return (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableBody>
              <TableRow>
                <TableCell component="th" scope="row">Client ID:</TableCell>
                <TableCell>{data.client_id}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Portfolio ID:</TableCell>
                <TableCell>{data.portfolio_id}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Date:</TableCell>
                <TableCell>{data.date ? new Date(data.date).toLocaleDateString() : 'N/A'}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Uploaded At:</TableCell>
                <TableCell>{data.uploaded_at ? new Date(data.uploaded_at).toLocaleString() : 'N/A'}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      );
    }

    if (Array.isArray(data)) {
      if (data.length === 0) {
        return <Typography>No {type} available.</Typography>;
      }
      const headers = Object.keys(data[0]).filter(key => key !== 'id' && key !== '_id');
      return (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                {headers.map((header) => (
                  <TableCell key={header} sx={{ textTransform: 'capitalize' }}>
                    {header.replace(/_/g, ' ')}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((row, index) => (
                <TableRow key={index}>
                  {headers.map((header) => (
                    <TableCell key={header}>
                      {header.includes('date') && row[header] ? new Date(row[header]).toLocaleDateString() : row[header]}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      );
    }

    if (type === 'compliance_report_display') {
      if (!data) {
        return <Typography>No compliance report available.</Typography>;
      }
      return (
        <Box>
          <Typography variant="h6" component="h3" gutterBottom sx={{ mt: 2, mb: 1 }}>
            Compliance Report Summary
          </Typography>
          <Divider sx={{ mb: 2 }} />

          {/* Policy Violations */}
          <Typography variant="h6" component="h4" gutterBottom>
            Policy Violations
          </Typography>
          {data.policy_violations_summary ? (
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {data.policy_violations_summary}
            </Typography>
          ) : (
            <Typography variant="body1" color="text.secondary">No policy violations detected.</Typography>
          )}

          {data.raw_policy_violations && data.raw_policy_violations.length > 0 && (
            <Box mt={2}>
              <Typography variant="subtitle2">Details:</Typography>
              <List dense>
                {data.raw_policy_violations.map((violation, idx) => (
                  <ListItem key={idx} sx={{ py: 0.5 }}>
                    <Typography variant="body2">{violation}</Typography>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
          <Divider sx={{ my: 2 }} />

          {/* Risk Drifts - IMPROVED RENDERING */}
          <Typography variant="h6" component="h4" gutterBottom>
            Risk Drifts
          </Typography>
          {data.risk_drifts_summary ? (
            <Box>
              <Typography variant="body1" sx={{ mb: 1 }}>
                Summary:
              </Typography>
              <List dense sx={{ ml: 2 }}>
                {data.risk_drifts_summary.split(';').filter(s => s.trim() !== '').map((driftSummary, idx) => (
                  <ListItem key={idx} sx={{ py: 0.5 }}>
                    <Typography variant="body2">{driftSummary.trim()}</Typography>
                  </ListItem>
                ))}
              </List>
            </Box>
          ) : (
            <Typography variant="body1" color="text.secondary">No significant risk drifts identified.</Typography>
          )}

          {data.raw_risk_drifts && data.raw_risk_drifts.length > 0 && (
            <Box mt={2}>
              <Typography variant="subtitle2">Details:</Typography>
              <TableContainer component={Paper} sx={{ mt: 1, maxHeight: 200, overflowY: 'auto' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Sector</TableCell>
                      <TableCell>Actual</TableCell>
                      <TableCell>Model</TableCell>
                      <TableCell>Drift</TableCell>
                      <TableCell>Threshold</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.raw_risk_drifts.map((drift, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{drift.sector}</TableCell>
                        <TableCell>{drift.actual?.toFixed(4)}</TableCell>
                        <TableCell>{drift.model?.toFixed(4)}</TableCell>
                        <TableCell>{drift.drift?.toFixed(4)}</TableCell>
                        <TableCell>{drift.threshold?.toFixed(4)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </Box>
      );
    }

    return <Typography>Invalid data type for rendering.</Typography>;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Error: {error.message}. Please try again or check if the portfolio exists.
          <Button onClick={() => navigate('/')} sx={{ ml: 2 }}>Go Back Home</Button>
        </Alert>
      </Box>
    );
  }

  if (!portfolio) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">
          No portfolio data found for {clientId}/{portfolioId}.
          <Button onClick={() => navigate('/')} sx={{ ml: 2 }}>Go Back Home</Button>
        </Alert>
      </Box> 
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate(-1)}
        variant="outlined"
        sx={{ mb: 3 }}
      >
        Back to Portfolios
      </Button>

      <Typography variant="h4" component="h1" gutterBottom>
        Portfolio Details: {clientId}/{portfolioId}
      </Typography>

      <Box sx={{ width: '100%', typography: 'body1', mt: 3 }}>
        <TabContext value={currentTab}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <TabList onChange={handleChangeTab} aria-label="portfolio details tabs">
              <Tab label="Summary" value="summary" />
              <Tab label="Positions" value="positions" />
              <Tab label="Trades" value="trades" />
              <Tab label="Compliance Report" value="compliance_report_tab" />
              <Tab label="Historical Reports" value="historical_reports" />
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

          <TabPanel value="compliance_report_tab">
            {renderData(portfolio.compliance_report, 'compliance_report_display')}
          </TabPanel>

          {/* IMPROVED TabPanel for Historical Reports with Collapsible Sections */}
          <TabPanel value="historical_reports">
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Historical Compliance Reports</Typography>
            {historicalReports.length > 0 ? (
              <Box>
                {historicalReports.map((report, index) => (
                  <Paper key={index} sx={{ p: 2, mb: 2, border: '1px solid #e0e0e0', borderRadius: '8px' }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Report Date: {new Date(report.uploaded_at || report.date).toLocaleString()}
                    </Typography>
                    {report.compliance_report ? (
                      <Box sx={{ ml: 2, mt: 1 }}>
                        {/* Policy Violations for Historical */}
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Policy Violations:</Typography>
                        {report.compliance_report.policy_violations_summary ? (
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', ml: 1 }}>
                            {report.compliance_report.policy_violations_summary}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>No policy violations detected.</Typography>
                        )}
                        
                        {report.compliance_report.raw_policy_violations && report.compliance_report.raw_policy_violations.length > 0 && (
                          <Accordion elevation={0} sx={{ mt: 1, '&.MuiAccordion-root:before': { display: 'none' }, border: '1px solid #eee' }}>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls={`panel${index}pvh-content`} id={`panel${index}pvh-header`}>
                              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Show Raw Policy Violations ({report.compliance_report.raw_policy_violations.length})</Typography>
                            </AccordionSummary> {/* MISSING CLOSING TAG ADDED HERE */}
                            <AccordionDetails>
                              <List dense sx={{ ml: 1 }}>
                                {report.compliance_report.raw_policy_violations.map((violation, vIdx) => (
                                  <ListItem key={vIdx} sx={{ py: 0 }}>
                                    <Typography variant="body2" color="text.secondary">- {violation}</Typography>
                                  </ListItem>
                                ))}
                              </List>
                            </AccordionDetails>
                          </Accordion>
                        )}
                        <Divider sx={{ my: 1 }} />

                        {/* Risk Drifts for Historical */}
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mt: 2 }}>Risk Drifts:</Typography>
                        {report.compliance_report.risk_drifts_summary ? (
                          <List dense sx={{ ml: 1 }}>
                            {report.compliance_report.risk_drifts_summary.split(';').filter(s => s.trim() !== '').map((driftSummary, dIdx) => (
                              <ListItem key={dIdx} sx={{ py: 0 }}>
                                <Typography variant="body2" color="text.secondary">- {driftSummary.trim()}</Typography>
                              </ListItem>
                            ))}
                          </List>
                        ) : (
                          <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>No significant risk drifts identified.</Typography>
                        )}
                        
                        {report.compliance_report.raw_risk_drifts && report.compliance_report.raw_risk_drifts.length > 0 && (
                          <Accordion elevation={0} sx={{ mt: 1, '&.MuiAccordion-root:before': { display: 'none' }, border: '1px solid #eee' }}>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls={`panel${index}rdh-content`} id={`panel${index}rdh-header`}>
                              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Show Raw Risk Drifts ({report.compliance_report.raw_risk_drifts.length})</Typography>
                            </AccordionSummary> {/* MISSING CLOSING TAG ADDED HERE */}
                            <AccordionDetails>
                              <TableContainer component={Paper} elevation={0} sx={{ mt: 1, maxHeight: 150, overflowY: 'auto' }}>
                                <Table size="small">
                                  <TableHead>
                                    <TableRow>
                                      <TableCell>Sector</TableCell>
                                      <TableCell>Actual</TableCell>
                                      <TableCell>Model</TableCell>
                                      <TableCell>Drift</TableCell>
                                      <TableCell>Threshold</TableCell>
                                    </TableRow>
                                  </TableHead>
                                  <TableBody>
                                    {report.compliance_report.raw_risk_drifts.map((drift, dIdx) => (
                                      <TableRow key={dIdx}>
                                        <TableCell>{drift.sector}</TableCell>
                                        <TableCell>{drift.actual?.toFixed(4)}</TableCell>
                                        <TableCell>{drift.model?.toFixed(4)}</TableCell>
                                        <TableCell>{drift.drift?.toFixed(4)}</TableCell>
                                        <TableCell>{drift.threshold?.toFixed(4)}</TableCell>
                                      </TableRow>
                                    ))}
                                  </TableBody>
                                </Table>
                              </TableContainer>
                            </AccordionDetails>
                          </Accordion>
                        )}

                      </Box>
                    ) : (
                      <Typography variant="body2" color="error" sx={{ ml: 2 }}>
                        Compliance report data not available for this record.
                      </Typography>
                    )}
                  </Paper>
                ))}
              </Box>
            ) : (
              <Typography>No historical reports available for this portfolio.</Typography>
            )}
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