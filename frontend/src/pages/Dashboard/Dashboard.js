// frontend/src/pages/Dashboard/Dashboard.js
import React, { useEffect, useState } from "react";
import {
  Box,
  Heading,
  Text,
  Spinner,
  Alert,
  AlertIcon,
  AlertDescription,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Link,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

const API_BASE_URL = "http://127.0.0.1:8000"; // Make sure this matches your FastAPI backend URL

function Dashboard() {
  const [portfolios, setPortfolios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
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
        setError(
          "Failed to load portfolios. Please ensure the backend server is running and accessible."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolios();
  }, []);

  if (loading) {
    return (
      <Box p={5} textAlign="center">
        <Spinner size="xl" />
        <Text mt={4}>Loading portfolios...</Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={5}>
        <Alert status="error">
          <AlertIcon />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={5}>
      <Heading as="h2" size="xl" mb={6}>
        All Portfolios
      </Heading>

      {portfolios.length === 0 ? (
        <Text>No portfolios found. Upload some data to get started!</Text>
      ) : (
        <TableContainer>
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Client ID</Th>
                <Th>Portfolio ID</Th>
                <Th>Last Reanalyzed At</Th>
                <Th>Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {portfolios.map((portfolio) => (
                <Tr
                  key={
                    portfolio.id ||
                    `${portfolio.client_id}-${portfolio.portfolio_id}`
                  }
                >
                  <Td>{portfolio.client_id}</Td>
                  <Td>{portfolio.portfolio_id}</Td>
                  <Td>
                    {portfolio.last_reanalyzed_at
                      ? new Date(portfolio.last_reanalyzed_at).toLocaleString()
                      : "N/A"}
                  </Td>
                  <Td>
                    {/* Link to a detailed view of the portfolio */}
                    <Link
                      as={RouterLink}
                      to={`/portfolio/${portfolio.client_id}/${portfolio.portfolio_id}`}
                      color="teal.500"
                    >
                      View Details
                    </Link>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

export default Dashboard;
