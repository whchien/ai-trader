# Strategy overview
### Single Stock Trading Strategies

| Strategy                  | Description                                                                                             |
| :------------------------ | :------------------------------------------------------------------------------------------------------ |
| **Buy & Hold**            | Buys on the first day and holds to the end. A baseline for performance comparison.                        |
| **SMA (Naive)**           | Buys when price is above a moving average, sells when below.                                            |
| **SMA (Crossover)**       | Buys on a "golden cross" (fast MA over slow MA), sells on a "death cross".                              |
| **MACD**                  | Buys on a MACD "golden cross" and sells on a "death cross".                                             |
| **Bollinger Bands**       | A mean-reversion strategy that buys at the lower band and sells at the upper band.                      |
| **Momentum**              | Buys when momentum turns positive, sells when price falls below a trend-filtering MA.                   |
| **RSI**                   | Combines RSI and Bollinger Bands. Buys when RSI is oversold and price is below the lower band.          |
| **RSRS**                  | Uses linear regression of high/low prices to buy on signals of strengthening support.                     |
| **ROC**                   | A simple momentum strategy that buys on a high Rate of Change and sells on a low one.                   |
| **Double Top**            | Buys on a breakout after a double top pattern, with trend and volume confirmation.                      |
| **Risk Averse**           | Buys low-volatility stocks making new highs on high volume.                                             |
| **Turtle Trading**        | A classic trend-following strategy that buys on breakouts and sells on breakdowns, using ATR for position sizing. |
| **Volatility Contraction Pattern (VCP)** | Buys on breakouts after price and volume volatility have contracted.                    |
| **AlphaRSI Pro**          | Advanced RSI with adaptive overbought/oversold levels based on volatility and trend bias filtering. Reduces false signals in choppy markets. |
| **Adaptive RSI (ARSI)**   | RSI with dynamic period (8-28) that adapts to market volatility and cycles. More responsive in high volatility, more stable in low volatility. |
| **Hybrid AlphaRSI**       | Most sophisticated RSI variant combining adaptive period, adaptive levels, and trend confirmation for highest quality signals. |

### Portfolio Trading Strategies

| Strategy                    | Description                                                                                         |
| :-------------------------- | :-------------------------------------------------------------------------------------------------- |
| **ROC Rotation**            | Periodically rotates into the top K stocks with the highest Rate of Change (momentum).              |
| **RSRS Rotation**           | Periodically rotates into stocks with high RSRS indicator values (strong support).                  |
| **Triple RSI Rotation**     | Rotates stocks based on a combination of long, medium, and short-term RSI signals.                  |
| **Multi Bollinger Bands Rotation** | A breakout rotation strategy that buys stocks crossing above their upper Bollinger Band.     |

### AI Component (Active Development)
I am currently developing an Agentic AI system designed to interact with and reason over backtesting strategies. In parallel, an MCP server is being implemented to support orchestration and integration.

### Classic Machine Learning (Deprecated / Experimental)
This component is no longer part of the active development roadmap due to bandwidth and prioritization constraints. Deprecated components include feature engineering and model training approaches such as Logistic Regression, Gradient Boosting, Recurrent Neural Networks (RNN), and Long Short-Term Memory (LSTM).

