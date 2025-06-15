// frontend/src/index.js
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
// This is the correct import for Chakra UI 2.5.5, it's directly from @chakra-ui/react
import { ChakraProvider, extendTheme } from "@chakra-ui/react";
import "./index.css";

// You can extend the default Chakra UI theme here if you want custom colors, fonts, etc.
const theme = extendTheme({});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <ChakraProvider theme={theme}>
      <App />
    </ChakraProvider>
  </React.StrictMode>
);
