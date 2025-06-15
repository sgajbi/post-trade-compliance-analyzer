// frontend/src/App.js

import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link as RouterLink,
} from "react-router-dom";
import {
  ChakraProvider,
  extendTheme,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerContent,
  DrawerOverlay, // Corrected from DrawerBackdrop
  DrawerCloseButton, // Corrected from DrawerCloseTrigger
  useDisclosure,
  Button,
  Box,
  Flex,
  Link,
  VStack,
  Text,
} from "@chakra-ui/react";
import { HamburgerIcon } from "@chakra-ui/icons";

// Assuming you have a Dashboard.js file in src/pages/Dashboard/
// If not, you'll need to create it or adjust this import.
import Dashboard from "./pages/Dashboard/Dashboard";

// You can extend the default Chakra UI theme here for custom colors, fonts, etc.
// This ensures `extendTheme` is imported and used correctly for Chakra UI 2.5.5
const theme = extendTheme({});

function App() {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const btnRef = React.useRef();

  return (
    <ChakraProvider theme={theme}>
      <Router>
        <Flex
          as="nav"
          p={4}
          bg="gray.100"
          align="center"
          justify="space-between"
        >
          <Button
            ref={btnRef}
            colorScheme="teal"
            onClick={onOpen}
            leftIcon={<HamburgerIcon />}
          >
            Menu
          </Button>
          <Text fontSize="xl" fontWeight="bold">
            Post-Trade Compliance Analyzer
          </Text>
          <Box>{/* Placeholder for other nav items or user info */}</Box>
        </Flex>

        <Drawer
          isOpen={isOpen}
          placement="left"
          onClose={onClose}
          finalFocusRef={btnRef}
        >
          <DrawerOverlay /> {/* Corrected component name */}
          <DrawerContent>
            <DrawerCloseButton /> {/* Corrected component name */}
            <DrawerHeader borderBottomWidth="1px">Navigation</DrawerHeader>
            <DrawerBody>
              <VStack align="stretch" spacing={4}>
                <Link
                  as={RouterLink}
                  to="/"
                  onClick={onClose}
                  p={2}
                  _hover={{ bg: "gray.100" }}
                >
                  Dashboard
                </Link>
                {/* Add more navigation links here as your application grows */}
                {/* <Link as={RouterLink} to="/upload" onClick={onClose} p={2} _hover={{ bg: "gray.100" }}>
                  Upload Portfolio
                </Link>
                <Link as={RouterLink} to="/ask" onClick={onClose} p={2} _hover={{ bg: "gray.100" }}>
                  Ask a Question
                </Link> */}
              </VStack>
            </DrawerBody>
          </DrawerContent>
        </Drawer>

        <Box p={4}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            {/* Placeholder for the Portfolio Detail page - we'll create this next */}
            <Route
              path="/portfolio/:clientId/:portfolioId"
              element={<Text>Portfolio Detail Page Coming Soon!</Text>}
            />
            {/* Add more routes here as your application grows */}
          </Routes>
        </Box>
      </Router>
    </ChakraProvider>
  );
}

export default App;
