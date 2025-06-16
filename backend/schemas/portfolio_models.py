# schemas/portfolio_models.py
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field

class TradeIn(BaseModel):
    symbol: str
    quantity: float = Field(..., gt=0, description="Quantity of the instrument to trade, must be positive.")
    price: float = Field(..., gt=0, description="Execution price per unit of the instrument, must be positive.")
    trade_date: Optional[date] = None
    type: str = Field("BUY", pattern="^(BUY|SELL)$", description="Type of trade (BUY or SELL).")
    isin: str  
    sector: str 


class Position(BaseModel):
    symbol: str
    quantity: float
    isin: str
    avg_price: float = 0.0  # Make optional with a default value
    market_price: float = 0.0 # Make optional with a default value
    sector: str
    
class Trade(BaseModel):
    trade_id: str
    symbol: str
    quantity: float
    price: float
    trade_date: str
    type: str

class PortfolioUpdate(BaseModel):
    client_id: str
    portfolio_id: str
    date: str
    positions: List[Position]
    trades: List[Trade]
    uploaded_at: datetime
    analysis: Optional[dict] = None