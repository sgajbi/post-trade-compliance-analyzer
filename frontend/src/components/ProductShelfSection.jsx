import React from 'react'; // Removed useState, useEffect as state is lifted

const ProductShelfSection = ({ products, loadingProducts, fetchProducts, setAppErrorMessage }) => {
  // Removed local state and fetch logic

  return (
    <div className="product-shelf-section">
      <h3>🛍️ Available Investment Products</h3>
      <button onClick={fetchProducts} disabled={loadingProducts}>
        {loadingProducts ? 'Loading...' : 'Fetch Product Shelf'}
      </button>

      {loadingProducts && <p>Loading products...</p>}
      {/* Moved error message display to App.jsx global error or handle locally if needed */}

      {products && products.length > 0 && (
        <div className="product-list">
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th>Sector</th>
                <th>Market Price</th>
                <th>Currency</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.isin}>
                  <td>{product.symbol}</td>
                  <td>{product.name}</td>
                  <td>{product.sector}</td>
                  <td>{product.market_price.toFixed(2)}</td>
                  <td>{product.currency}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {products && products.length === 0 && !loadingProducts && (
        <p>No products found on the shelf.</p>
      )}
    </div>
  );
};

export default ProductShelfSection;