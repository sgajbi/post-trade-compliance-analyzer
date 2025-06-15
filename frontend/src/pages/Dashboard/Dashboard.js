// frontend/src/pages/Dashboard/Dashboard.js
import React from "react";
import { Box, Heading, Text, VStack } from "@chakra-ui/react";

function Dashboard() {
  return (
    <Box p={5}>
      <Heading mb={4}>Dashboard</Heading>
      <Text fontSize="lg">Welcome to the Post-Trade Compliance Analyzer!</Text>
      <VStack mt={8} spacing={3} align="flex-start">
        <Text>
          Here you will see a list of all portfolios and their compliance
          summaries.
        </Text>
        <Text>Use the navigation above to explore features.</Text>
      </VStack>
    </Box>
  );
}

export default Dashboard;
