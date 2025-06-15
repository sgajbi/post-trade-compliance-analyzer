import React from 'react'; // Removed useState, useEffect as state is lifted

const ClientSection = ({ clients, loadingClients, fetchClients, setAppErrorMessage }) => {
  // Removed local state and fetch logic

  return (
    <div className="client-section">
      <h3>👥 Our Clients</h3>
      <button onClick={fetchClients} disabled={loadingClients}>
        {loadingClients ? 'Loading...' : 'Fetch Clients'}
      </button>

      {loadingClients && <p>Loading clients...</p>}
      {/* Moved error message display to App.jsx global error or handle locally if needed */}

      {clients && clients.length > 0 && (
        <div className="client-list">
          {clients.map((client) => (
            <div key={client.client_id} className="client-card">
              <h4>{client.name} (ID: {client.client_id})</h4>
              {client.portfolios && client.portfolios.length > 0 ? (
                <p>Portfolios:</p>
              ) : (
                <p>No portfolios listed.</p>
              )}
              {client.portfolios && client.portfolios.length > 0 && (
                <ul>
                  {client.portfolios.map((portfolio) => (
                    <li key={portfolio.portfolio_id}>
                      {portfolio.name} (ID: {portfolio.portfolio_id}) - Risk: {portfolio.risk_profile}, Currency: {portfolio.currency}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}

      {clients && clients.length === 0 && !loadingClients && (
        <p>No clients found.</p>
      )}
    </div>
  );
};

export default ClientSection;