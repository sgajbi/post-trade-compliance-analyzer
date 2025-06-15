// frontend/src/pages/PortfolioDetail/PortfolioDetail.js
import React, { useEffect, useState } from "react";
import { useParams, Link as RouterLink } from "react-router-dom";
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
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  VStack, // ADDED BACK HERE
  Flex,
  Spacer,
  Button,
} from "@chakra-ui/react";
import { ArrowBackIcon } from "@chakra-ui/icons";

const API_BASE_URL = "http://127.0.0.1:8000"; // Ensure this matches your FastAPI backend URL

function PortfolioDetail() {
  const { clientId, portfolioId } = useParams();
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPortfolioDetail = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(
          `${API_BASE_URL}/portfolio/${clientId}/${portfolioId}`
        );
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setPortfolio(data);
      } catch (e) {
        console.error("Failed to fetch portfolio details:", e);
        setError(
          "Failed to load portfolio details. Please check Client ID and Portfolio ID, and ensure the backend is running."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioDetail();
  }, [clientId, portfolioId]); // Re-fetch if client or portfolio ID changes

  if (loading) {
    return (
      <Box p={5} textAlign="center">
        <Spinner size="xl" />
        <Text mt={4}>
          Loading portfolio details for {clientId}/{portfolioId}...
        </Text>
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
        <Button as={RouterLink} to="/" mt={4} leftIcon={<ArrowBackIcon />}>
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  if (!portfolio) {
    return (
      <Box p={5}>
        <Text>Portfolio not found.</Text>
        <Button as={RouterLink} to="/" mt={4} leftIcon={<ArrowBackIcon />}>
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  // Helper function to render data in a table or as text (now recursive)
  const renderData = (data) => {
    // If data is null or undefined, return "No data available."
    if (data === null || data === undefined) {
      return <Text>N/A</Text>;
    }

    // If it's a primitive type (string, number, boolean), just display it
    if (typeof data !== "object") {
      return <Text>{data.toString()}</Text>;
    }

    // If it's an empty object or an empty array, display "No data available."
    if (Object.keys(data).length === 0 && !Array.isArray(data)) {
      return <Text>No data available.</Text>;
    }
    if (Array.isArray(data) && data.length === 0) {
      return <Text>No items to display.</Text>;
    }

    // Handle array types
    if (Array.isArray(data)) {
      // Check if the array contains only primitive types (strings, numbers, etc.)
      const allPrimitives = data.every(
        (item) => typeof item !== "object" || item === null
      );

      if (allPrimitives) {
        // If all items are primitives, display them as a simple list (VStack)
        return (
          <VStack align="flex-start" spacing={1}>
            {data.map((item, idx) => (
              <Text key={idx}>{item?.toString()}</Text>
            ))}
          </VStack>
        );
      } else {
        // If it's an array of objects, render as a nested table
        // Get keys from the first object, assuming uniform structure
        const keys = Object.keys(data[0] || {});
        if (keys.length === 0)
          return <Text>No items to display (array of empty objects).</Text>;

        return (
          <TableContainer>
            <Table variant="simple" size="sm">
              {" "}
              {/* Changed to 'simple' for nested tables */}
              <Thead>
                <Tr>
                  {keys.map((key) => (
                    <Th key={key}>{key.replace(/_/g, " ").toUpperCase()}</Th>
                  ))}
                </Tr>
              </Thead>
              <Tbody>
                {data.map((item, index) => (
                  <Tr key={index}>
                    {keys.map((key) => (
                      <Td key={key}>
                        {/* Recursive call for nested data */}
                        {renderData(item[key])}
                      </Td>
                    ))}
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        );
      }
    }

    // Handle object types (main object or nested objects)
    return (
      <TableContainer>
        <Table variant="striped" size="sm">
          <Tbody>
            {Object.entries(data).map(([key, value]) => (
              <Tr key={key}>
                <Th>{key.replace(/_/g, " ").toUpperCase()}</Th>
                <Td>
                  {/* Recursive call for nested data */}
                  {renderData(value)}
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <Box p={5}>
      <Flex mb={4} align="center">
        <Button as={RouterLink} to="/" leftIcon={<ArrowBackIcon />}>
          Back to Dashboard
        </Button>
        <Spacer />
        <Heading as="h2" size="xl">
          Portfolio: {portfolio.client_id}/{portfolio.portfolio_id}
        </Heading>
        <Spacer />
        <Box width="auto" /> {/* Spacer to balance the back button */}
      </Flex>

      <Text mb={4}>
        Last Reanalyzed:{" "}
        {portfolio.last_reanalyzed_at
          ? new Date(portfolio.last_reanalyzed_at).toLocaleString()
          : "N/A"}
      </Text>

      <Tabs isFitted variant="enclosed" mt={6}>
        <TabList mb="1em">
          <Tab>Positions</Tab>
          <Tab>Transactions (Trades)</Tab>
          <Tab>Analysis</Tab>
          <Tab>Compliance Report</Tab>
        </TabList>
        <TabPanels>
          <TabPanel>
            <Heading as="h3" size="md" mb={4}>
              Positions
            </Heading>
            {renderData(portfolio.positions)}
          </TabPanel>
          <TabPanel>
            <Heading as="h3" size="md" mb={4}>
              Transactions
            </Heading>
            {renderData(portfolio.trades)}{" "}
            {/* Assuming 'trades' key for transactions */}
          </TabPanel>
          <TabPanel>
            <Heading as="h3" size="md" mb={4}>
              Analysis
            </Heading>
            {renderData(portfolio.analysis)}
          </TabPanel>
          <TabPanel>
            <Heading as="h3" size="md" mb={4}>
              Compliance Report
            </Heading>
            {renderData(portfolio.compliance_report)}
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
}

export default PortfolioDetail;
