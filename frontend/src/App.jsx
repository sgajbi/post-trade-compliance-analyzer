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

// Define a refined Material-UI theme for a more professional look
const theme = createTheme({
  palette: {
    // Primary color: A professional shade of blue
    primary: {
      main: '#1976d2', // Standard, strong Material-UI blue
      light: '#42a5f5',
      dark: '#1565c0',
      contrastText: '#ffffff', // White text for primary background
    },
    // Secondary color: A subtle, cool grey for accents and backgrounds
    secondary: {
      main: '#607d8b', // Muted blue-grey
      light: '#90a4ae',
      dark: '#455a64',
      contrastText: '#ffffff',
    },
    // Neutral background colors to provide visual separation and depth
    background: {
      default: '#eef2f6', // Light, subtle bluish-grey for main page background
      paper: '#ffffff', // Pure white for cards, panels
    },
    // Text colors for better contrast
    text: {
      primary: '#212121', // Dark grey for main text
      secondary: '#616161', // Medium grey for secondary text
      disabled: '#bdbdbd',
    },
    // Action states (hover, selected, etc.)
    action: {
      hover: 'rgba(0, 0, 0, 0.04)',
      selected: 'rgba(0, 0, 0, 0.08)',
    },
    // Common colors for feedback and status
    error: { main: '#d32f2f' },
    warning: { main: '#ed6c02' },
    info: { main: '#0288d1' },
    success: { main: '#2e7d32' },
  },
  typography: {
    fontFamily: 'Roboto, "Helvetica Neue", Arial, sans-serif',
    h4: {
      fontWeight: 600,
      fontSize: '2rem',
      '@media (max-width:600px)': {
        fontSize: '1.5rem',
      },
    },
    h5: {
      fontWeight: 500,
      fontSize: '1.5rem',
      '@media (max-width:600px)': {
        fontSize: '1.25rem',
      },
    },
    h6: {
      fontWeight: 500,
      fontSize: '1.25rem',
      '@media (max-width:600px)': {
        fontSize: '1rem',
      },
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: ({ theme }) => ({ // Use function to access theme
          boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)', // Slightly more pronounced shadow
          backgroundColor: theme.palette.primary.main, // Set AppBar background to primary color
          color: theme.palette.primary.contrastText, // Ensure text color contrasts with primary background
        }),
      },
    },
    MuiToolbar: {
      styleOverrides: {
        root: {
          minHeight: '64px',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          padding: '8px 16px',
        },
        containedPrimary: {
          backgroundColor: '#1976d2',
          '&:hover': {
            backgroundColor: '#1565c0',
          },
        },
        outlinedPrimary: {
          borderColor: '#1976d2',
          color: '#1976d2',
          '&:hover': {
            backgroundColor: 'rgba(25, 118, 210, 0.04)',
            borderColor: '#1565c0',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0px 2px 10px rgba(0, 0, 0, 0.05)',
          borderRadius: '8px',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          fontSize: '1rem',
          minWidth: 'unset',
          padding: '12px 16px',
          '@media (max-width:600px)': {
            fontSize: '0.875rem',
            padding: '8px 12px',
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: ({ theme }) => ({
          height: 3,
          backgroundColor: theme.palette.primary.main,
        }),
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          padding: '12px 16px',
          fontSize: '0.9rem',
          '@media (max-width:600px)': {
            padding: '8px 12px',
            fontSize: '0.8rem',
          },
        },
        head: {
          fontWeight: 600,
          backgroundColor: '#f0f4f7',
          color: ({ theme }) => theme.palette.text.primary,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '8px',
          },
        },
      },
    },
    MuiContainer: {
      styleOverrides: {
        root: {
          // No changes needed here.
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: 'inherit' }}>
              Post-Trade Compliance Analyzer
            </Typography>
          </Toolbar>
        </AppBar>
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/portfolio/:clientId/:portfolioId" element={<PortfolioDetail />} />
          </Routes>
        </Container>
      </Router>
    </ThemeProvider>
  );
}

export default App;