# ai-trader
[中文版說明 (Chinese Subpage)](README_zh.md)

This repository demonstrates how to implement 20+ algorithmic trading strategies using Backtrader framework with a focus on AI. It includes examples for both the US and Taiwanese stock markets.

Some of the codes are still in development and not fully clean or functional at the moment, but I am actively working on updates and improvements.

## Strategy overview 
### Single stock trading 
- SMA (Niave SMA & Cross SMA)
- Bollinger Band
- Momentum 
- RSI
- Resistance Support Relative Strength (RSRS)
- ROC
- Double Top
- Risk Averse
- Turtle
- Volatility Contraction Pattern (VCP)

### Portfolio trading
- ROC rotation
- RSRS rotation
- Triple RSI rotation
- Multi Bollinger Bands rotation

### Machine learning based (dev)
- Logistic regression
- Feature engineering
- Gradient boosting
- DNN
- RNN
- LSTM
- Reinforcemnt learning
- (More to come!)

## How to Start

1. Clone the repository:
    ```
    git https://github.com/whchien/ai-trader.git
    cd ai-trader
    ```

2. Install the required dependencies:
    ```
    pip install -r requirements.txt
    ```

3. (Optional) Download the data (you can also prepare your own).
    ```
    python ai_trader/loader.py
    ```
4. Test the first strategy.
    ```
    python ai_trader/strategy/classic/bbands.py 
    ```
 
# Tutorials
In the future, I will share some tutorial notebooks to share my learning with the community. If you find it helpful, please give the repo a star ⭐️. Your support would mean a lot to me. 