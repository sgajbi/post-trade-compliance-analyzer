// frontend/src/pages/PortfolioDetail/PortfolioDetail.jsx
import React, { useState, useEffect } from 'react'; // useEffect is needed for side effects, e.g., pre-filling price
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
  AccordionDetails,
  TextField,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  RadioGroup,
  FormControlLabel,
  Radio,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import MuiAlert from '@mui/material/Alert';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SendIcon from '@mui/icons-material/Send';
import TabContext from '@mui/lab/TabContext';
import TabList from '@mui/lab/TabList';
import TabPanel from '@mui/lab/TabPanel';
import { API_BASE_URL } from '../../utils/constants';
import useFetch from '../../hooks/useFetch';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

// For DatePicker
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';


const SnackbarAlert = React.forwardRef(function SnackbarAlert(props, ref) {
  return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

// Component for Historical Compliance Chart
const HistoricalComplianceChart = ({ historicalReports }) => {
  if (!historicalReports || historicalReports.length === 0) {
    return <Typography>No historical data to display charts.</Typography>;
  }

  const chartData = historicalReports
    .filter(report =>
      report.compliance_report &&
      report.compliance_report.raw_risk_drifts &&
      Array.isArray(report.compliance_report.raw_risk_drifts) &&
      report.compliance_report.raw_risk_drifts.length > 0
    )
    .map(report => {
      const totalDrift = parseFloat(report.compliance_report.total_risk_drift || 0); // Use total_risk_drift if available, else sum
      return {
        date: new Date(report.uploaded_at || report.date).toLocaleDateString(),
        totalRiskDrift: isNaN(totalDrift) ? 0 : totalDrift,
      };
    })
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  if (chartData.length === 0) {
    return <Typography>No measurable risk drift data for charting.</Typography>;
  }

  return (
    <Box sx={{ width: '100%', height: 300, mt: 3 }}>
      <Typography variant="h6" component="h3" gutterBottom>
        Historical Risk Drift Trends
      </Typography>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="totalRiskDrift"
            stroke="#8884d8"
            activeDot={{ r: 8 }}
            name="Total Risk Drift"
          />
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
};

// Component for Asset Allocation Chart (by Sector)
const AssetAllocationChart = ({ positions }) => {
  if (!positions || positions.length === 0) {
    return <Typography>No position data to display asset allocation.</Typography>;
  }

  // Aggregate market value by sector
  const aggregatedData = positions.reduce((acc, position) => {
    const sector = position.sector || 'Unknown';
    const marketValue = parseFloat(position.market_value);

    if (!isNaN(marketValue)) {
      acc[sector] = (acc[sector] || 0) + marketValue;
    }
    return acc;
  }, {});

  const chartData = Object.keys(aggregatedData).map(sector => ({
    name: sector,
    value: aggregatedData[sector],
  }));

  if (chartData.length === 0) {
    return <Typography>No valid sector allocation data for charting.</Typography>;
  }

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#AF19FF', '#FF194F', '#82ca9d', '#ffc658'];

  return (
    <Box sx={{ width: '100%', height: 300, mt: 3 }}>
      <Typography variant="h6" component="h3" gutterBottom>
        Asset Allocation by Sector
      </Typography>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </Box>
  );
};


function PortfolioDetail() {
  const { clientId, portfolioId } = useParams();
  const navigate = useNavigate();

  const [currentTab, setCurrentTab] = useState('summary');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('info');

  const [chatHistory, setChatHistory] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // State for Add Trade Form
  const [tradeForm, setTradeForm] = useState({
    selectedProduct: '', // Stores the selected product object from productShelf
    quantity: '',
    price: '',
    trade_date: dayjs(), // Initialize with current date using dayjs
    type: 'BUY',
  });
  const [addingTrade, setAddingTrade] = useState(false);

  // Fetch Hooks
  const {
    data: portfolio,
    loading: portfolioLoading,
    error: portfolioError,
    refetch: refetchPortfolio // Get refetch function
  } = useFetch(`${API_BASE_URL}/portfolio/${clientId}/${portfolioId}/detail`);

  const {
    data: historicalReports,
    loading: historicalReportsLoading,
    error: historicalReportsError
  } = useFetch(`${API_BASE_URL}/portfolio/${clientId}/${portfolioId}/history`);

  const {
    data: productShelf,
    loading: productShelfLoading,
    error: productShelfError
  } = useFetch(`${API_BASE_URL}/product-shelf`);

  // Effect to update trade form when a product is selected
  useEffect(() => {
    if (tradeForm.selectedProduct) {
      const selected = productShelf?.find(p => p.symbol === tradeForm.selectedProduct);
      if (selected) {
        setTradeForm(prev => ({
          ...prev,
          price: selected.market_price || '', // Pre-fill price from product shelf
        }));
      }
    }
  }, [tradeForm.selectedProduct, productShelf]);


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

  const handleChangeTab = (event, newValue) => {
    setCurrentTab(newValue);
  };

  // Chat functionality - kept as is
  const handleSendMessage = async () => {
    if (!currentQuestion.trim()) return;

    const newUserMessage = { role: 'user', content: currentQuestion };
    setChatHistory(prevHistory => [...prevHistory, newUserMessage]);
    setCurrentQuestion('');

    setChatLoading(true);
    try {
      const requestUrl = `${API_BASE_URL}/rag/ask/${clientId}/${portfolioId}`;
      const requestBody = {
        question: newUserMessage.content,
        chat_history: chatHistory
      };

      const response = await fetch(requestUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setChatHistory(prevHistory => [...prevHistory, { role: 'assistant', content: data.answer }]);
    } catch (error) {
      console.error("Error sending message to RAG service:", error);
      showSnackbar(`Error: ${error.message}`, 'error');
      setChatHistory(prevHistory => [...prevHistory.slice(0, prevHistory.length - 1), { role: 'assistant', content: `Error: Could not get a response. ${error.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Add Trade functionality
  const handleTradeFormChange = (e) => {
    const { name, value } = e.target;
    setTradeForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleProductSelectChange = (e) => {
    const symbol = e.target.value;
    setTradeForm(prev => ({
      ...prev,
      selectedProduct: symbol // Store the symbol
    }));
  };

  const handleDateChange = (date) => {
    setTradeForm(prev => ({
      ...prev,
      trade_date: date
    }));
  };

  const handleAddTradeSubmit = async (e) => {
    e.preventDefault();
    setAddingTrade(true);

    const selectedProductDetails = productShelf?.find(p => p.symbol === tradeForm.selectedProduct);

    if (!selectedProductDetails) {
      showSnackbar('Please select a valid product.', 'error');
      setAddingTrade(false);
      return;
    }
    if (!tradeForm.quantity || parseFloat(tradeForm.quantity) <= 0) {
      showSnackbar('Quantity must be a positive number.', 'error');
      setAddingTrade(false);
      return;
    }
    if (!tradeForm.price || parseFloat(tradeForm.price) <= 0) {
      showSnackbar('Price must be a positive number.', 'error');
      setAddingTrade(false);
      return;
    }
    if (!tradeForm.trade_date) {
      showSnackbar('Please select a trade date.', 'error');
      setAddingTrade(false);
      return;
    }

    try {
      const tradeData = {
        symbol: selectedProductDetails.symbol,
        quantity: parseFloat(tradeForm.quantity),
        price: parseFloat(tradeForm.price),
        trade_date: tradeForm.trade_date.format('YYYY-MM-DD'), // Format date for API
        type: tradeForm.type,
        isin: selectedProductDetails.isin,
        sector: selectedProductDetails.sector,
      };

      const response = await fetch(`${API_BASE_URL}/portfolio/${clientId}/${portfolioId}/add-trade`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tradeData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      showSnackbar('Trade added successfully!', 'success');
      // Clear form
      setTradeForm({
        selectedProduct: '',
        quantity: '',
        price: '',
        trade_date: dayjs(),
        type: 'BUY',
      });
      // Refetch portfolio data to update positions and trades tabs
      refetchPortfolio();

    } catch (error) {
      console.error("Error adding trade:", error);
      showSnackbar(`Failed to add trade: ${error.message}`, 'error');
    } finally {
      setAddingTrade(false);
    }
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
                  <ListItem key={idx}>
                    <Typography variant="body2">{violation}</Typography>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
          <Divider sx={{ my: 2 }} />

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
                  <ListItem key={idx}>
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

  const overallLoading = portfolioLoading || historicalReportsLoading || productShelfLoading;
  const overallError = portfolioError || historicalReportsError || productShelfError;

  if (overallLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading portfolio details...</Typography>
      </Box>
    );
  }

  if (overallError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Error: {overallError.message}. Please try again or check if the portfolio exists.
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
              <Tab label="Add Trade" value="add_trade" />
              <Tab label="Chat with AI" value="chat_rag" />
            </TabList>
          </Box>

          <TabPanel value="summary">
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Portfolio Summary</Typography>
            {renderData(portfolio, 'summary')}
          </TabPanel>

          <TabPanel value="positions">
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Positions</Typography>
            {portfolio.positions && portfolio.positions.length > 0 ? (
              <>
                <AssetAllocationChart positions={portfolio.positions} />
                <Box mt={4}>
                  <Typography variant="h6" component="h3" gutterBottom>Raw Position Data</Typography>
                  {renderData(portfolio.positions, 'positions')}
                </Box>
              </>
            ) : (
              <Typography>No positions data available for charting or table display.</Typography>
            )}
          </TabPanel>

          <TabPanel value="trades">
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Trades</Typography>
            {renderData(portfolio.trades, 'trades')}
          </TabPanel>

          <TabPanel value="compliance_report_tab">
            {renderData(portfolio.compliance_report, 'compliance_report_display')}
          </TabPanel>

          <TabPanel value="historical_reports">
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Historical Compliance Reports</Typography>
            {historicalReportsLoading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <CircularProgress size={20} />
                <Typography sx={{ ml: 1 }}>Loading historical reports...</Typography>
              </Box>
            )}
            {historicalReportsError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                Error fetching historical reports: {historicalReportsError.message}
              </Alert>
            )}
            {!historicalReportsLoading && !historicalReportsError && (!historicalReports || historicalReports.length === 0) && (
              <Typography>No historical reports available for this portfolio.</Typography>
            )}
            {!historicalReportsLoading && !historicalReportsError && historicalReports && historicalReports.length > 0 && (
              <>
                <HistoricalComplianceChart historicalReports={historicalReports} />
                <Box mt={4}>
                  <Typography variant="h6" component="h3" gutterBottom>Raw Historical Data</Typography>
                  {historicalReports.map((report, index) => (
                    <Paper key={index} sx={{ p: 2, mb: 2, border: '1px solid #e0e0e0', borderRadius: '8px' }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Report Date: {new Date(report.uploaded_at || report.date).toLocaleString()}
                      </Typography>
                      {report.compliance_report ? (
                        <Box sx={{ ml: 2, mt: 1 }}>
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
                              </AccordionSummary>
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
                              </AccordionSummary>
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
              </>
            )}
          </TabPanel>

          {/* New Tab for Add Trade Functionality */}
          <TabPanel value="add_trade">
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Add New Trade</Typography>
            <form onSubmit={handleAddTradeSubmit}>
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 3, maxWidth: 600 }}>
                <FormControl fullWidth variant="outlined" sx={{ gridColumn: 'span 2' }}>
                  <InputLabel id="product-select-label">Select Product</InputLabel>
                  <Select
                    labelId="product-select-label"
                    id="product-select"
                    name="selectedProduct"
                    value={tradeForm.selectedProduct}
                    onChange={handleProductSelectChange}
                    label="Select Product"
                    disabled={productShelfLoading || productShelfError}
                  >
                    {productShelfLoading && <MenuItem disabled>Loading products...</MenuItem>}
                    {productShelfError && <MenuItem disabled>Error loading products</MenuItem>}
                    {productShelf && productShelf.map((product) => (
                      <MenuItem key={product.symbol} value={product.symbol}>
                        {product.symbol} - {product.name} ({product.isin})
                      </MenuItem>
                    ))}
                  </Select>
                  {(productShelfLoading || productShelfError) && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                      {productShelfLoading ? 'Loading available products...' : `Error: ${productShelfError.message}`}
                    </Typography>
                  )}
                </FormControl>

                <TextField
                  label="Quantity"
                  name="quantity"
                  type="number"
                  value={tradeForm.quantity}
                  onChange={handleTradeFormChange}
                  fullWidth
                  required
                  inputProps={{ min: 1 }}
                />

                <TextField
                  label="Price"
                  name="price"
                  type="number"
                  value={tradeForm.price}
                  onChange={handleTradeFormChange}
                  fullWidth
                  required
                  inputProps={{ step: "0.01", min: 0 }}
                />

                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <DatePicker
                    label="Trade Date"
                    value={tradeForm.trade_date}
                    onChange={handleDateChange}
                    slotProps={{ textField: { fullWidth: true, required: true } }}
                  />
                </LocalizationProvider>

                <FormControl component="fieldset" fullWidth sx={{ gridColumn: 'span 2', mt:1 }}>
                  <Typography variant="subtitle1" component="legend">Trade Type</Typography>
                  <RadioGroup
                    row
                    name="type"
                    value={tradeForm.type}
                    onChange={handleTradeFormChange}
                  >
                    <FormControlLabel value="BUY" control={<Radio />} label="BUY" />
                    <FormControlLabel value="SELL" control={<Radio />} label="SELL" />
                  </RadioGroup>
                </FormControl>

                <Button
                  type="submit"
                  variant="contained"
                  endIcon={<SendIcon />}
                  disabled={addingTrade || !tradeForm.selectedProduct || !tradeForm.quantity || !tradeForm.price || !tradeForm.trade_date}
                  sx={{ mt: 2, gridColumn: 'span 2' }}
                >
                  {addingTrade ? <CircularProgress size={24} color="inherit" /> : 'Add Trade'}
                </Button>
              </Box>
            </form>
          </TabPanel>


          <TabPanel value="chat_rag">
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Chat with AI Assistant about this Portfolio</Typography>
            <Box
              sx={{
                height: '50vh',
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                p: 2,
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: 1,
                mb: 2,
              }}
            >
              {chatHistory.length === 0 ? (
                <Typography color="text.secondary">Start a conversation by asking a question!</Typography>
              ) : (
                chatHistory.map((msg, index) => (
                  <Box
                    key={index}
                    sx={{
                      display: 'flex',
                      justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    }}
                  >
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 1.5,
                        maxWidth: '70%',
                        borderRadius: '15px',
                        backgroundColor: msg.role === 'user' ? 'primary.light' : 'grey.200',
                        color: msg.role === 'user' ? 'white' : 'text.primary',
                      }}
                    >
                      <Typography variant="body2">{msg.content}</Typography>
                    </Paper>
                  </Box>
                ))
              )}
              {chatLoading && (
                 <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                   <CircularProgress size={20} />
                   <Typography variant="body2" sx={{ ml: 1, fontStyle: 'italic', color: 'text.secondary' }}>AI is typing...</Typography>
                 </Box>
              )}
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Ask a question about this portfolio..."
                value={currentQuestion}
                onChange={(e) => setCurrentQuestion(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !chatLoading) {
                    handleSendMessage();
                  }
                }}
                disabled={chatLoading}
                sx={{ mr: 1 }}
              />
              <IconButton color="primary" onClick={handleSendMessage} disabled={chatLoading}>
                <SendIcon />
              </IconButton>
            </Box>
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