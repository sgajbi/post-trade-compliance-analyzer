// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';

import Home from './pages/Home/Home';
import PortfolioDetail from './pages/PortfolioDetail/PortfolioDetail';

// Define a basic Material-UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Example primary color
    },
    secondary: {
      main: '#dc004e', // Example secondary color
    },
  },
  components: {
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none', // Prevent uppercase tabs
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline /> {/* Provides a consistent baseline to build on. */}
      <Router>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Post-Trade Compliance Analyzer
            </Typography>
          </Toolbar>
        </AppBar>
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/portfolio/:clientId/:portfolioId" element={<PortfolioDetail />} />
            {/* Add more routes here if needed */}
          </Routes>
        </Container>
      </Router>
    </ThemeProvider>
  );
}

export default App;