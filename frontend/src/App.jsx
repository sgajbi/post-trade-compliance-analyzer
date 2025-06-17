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
      main: '#1a73e8', // A slightly deeper blue (Google Blue-like)
      light: '#4285f4', // Lighter shade for hover/active states
      dark: '#0f488c',  // Darker shade for contrast
      contrastText: '#ffffff', // Ensure good readability on primary background
    },
    // Secondary color: A neutral grey for accents and backgrounds
    secondary: {
      main: '#f0f2f5', // A very light grey for subtle backgrounds/separators
      light: '#ffffff', // Pure white
      dark: '#bdbdbd',  // A darker grey for borders/dividers
      contrastText: '#212121',
    },
    // Common colors for feedback and status
    error: { main: '#d32f2f' },
    warning: { main: '#ed6c02' },
    info: { main: '#0288d1' },
    success: { main: '#2e7d32' },
    // Text colors
    text: {
      primary: '#212121', // Dark grey for main text
      secondary: '#757575', // Lighter grey for secondary text
    },
    background: {
      default: '#f8f9fa', // A very light, almost white background
      paper: '#ffffff', // White for cards and elevated components
    },
  },
  typography: {
    // Setting a clean, professional font family
    fontFamily: 'Roboto, "Helvetica Neue", Arial, sans-serif',
    h4: {
      fontWeight: 600, // Make main headings bolder for emphasis
      fontSize: '2rem',
      '@media (max-width:600px)': { // Responsive font size for extra-small screens
        fontSize: '1.5rem',
      },
    },
    h5: {
      fontWeight: 500, // Medium weight for sub-headings
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
      lineHeight: 1.6, // Improve readability of paragraphs
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    button: {
      textTransform: 'none', // Keep button text as is (e.g., "View Details" instead of "VIEW DETAILS")
      fontWeight: 500, // Medium weight for button text
    },
  },
  components: {
    // Global overrides for Material-UI components to ensure consistency
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.05)', // Subtle shadow for app bar
          backgroundColor: '#ffffff', // White app bar for a clean look
          color: '#212121', // Dark text on white app bar
        },
      },
    },
    MuiToolbar: {
      styleOverrides: {
        root: {
          minHeight: '64px', // Standard height for toolbars
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px', // Slightly rounded corners for buttons
          padding: '8px 16px', // Consistent padding
        },
        containedPrimary: {
          '&:hover': {
            backgroundColor: '#0f488c', // Darker blue on hover
          },
        },
        outlinedPrimary: {
          borderColor: '#1a73e8',
          color: '#1a73e8',
          '&:hover': {
            backgroundColor: 'rgba(26, 115, 232, 0.04)', // Light hover effect
            borderColor: '#0f488c',
          },
        },
      },
    },
    MuiPaper: { // Applies to Cards, Dialogs, Menus, Tables (if used as Paper)
      styleOverrides: {
        root: {
          boxShadow: '0px 2px 10px rgba(0, 0, 0, 0.05)', // Subtle shadow for depth on cards/panels
          borderRadius: '8px', // Consistent border radius
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none', // Prevent uppercase tabs
          fontWeight: 500, // Slightly bolder tab labels
          fontSize: '1rem',
          minWidth: 'unset', // Allow tabs to take only necessary width
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
        indicator: {
          height: 3, // Thicker indicator for selected tab
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          padding: '12px 16px', // More comfortable padding for table cells
          fontSize: '0.9rem',
          '@media (max-width:600px)': {
            padding: '8px 12px',
            fontSize: '0.8rem',
          },
        },
        head: {
          fontWeight: 600, // Bolder table headers
          backgroundColor: '#f8f9fa', // Light background for table headers
          color: '#212121', // Dark text for table headers
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
            borderRadius: '8px', // Consistent border radius for text fields
          },
        },
      },
    },
    MuiContainer: {
      styleOverrides: {
        root: {
          // Adjust max-width on smaller screens if needed, though 'xl' is generally fine.
          // You might use spacing here for overall page padding.
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