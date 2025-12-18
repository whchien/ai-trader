# ai-trader

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[English Version (英文版)](README.md)

一個基於 Backtrader 的綜合回測框架，用於演算法交易策略。跨越美股、台股、加密貨幣和外匯市場測試和優化交易策略。現在支持 **MCP 伺服器**，可與 LLM 無縫整合。

**版本 0.3.0** 引入了全新架構，包含工具函式、CLI 工具、設定驅動工作流程和 MCP 伺服器，適用於專業回測和 AI 整合。

![Demo GIF](data/demo_bt.gif)

## ✨ v0.3.0 的新功能

- **MCP 伺服器** - Model Context Protocol 伺服器，支持與 Claude Desktop 的 LLM 整合
- **新 CLI 工具** - 從 YAML 設定檔執行回測
- **工具函式** - 常見任務的簡單輔助函式
- **設定驅動** - 版本控制、可重現回測
- **20+ 策略** - 包含新 AlphaRSI 變種的即用型交易策略
- **多市場支持** - 美股、台股、加密貨幣和外匯支持
- **豐富範例** - 5 個範例腳本和 4 個設定樣板

### 最新新增
- **FastMCP 伺服器** - 作為獨立 MCP 伺服器運行，支持 AI/LLM 整合
- **AlphaRSI Pro** - 先進的 RSI，具有自適應波動率級別和趨勢過濾
- **自適應 RSI** - 動態 RSI 週期，根據市場條件自動調整
- **混合 AlphaRSI** - 結合所有自適應功能以獲得優越的信號質量

## 快速開始

### 安裝

1. **複製程式庫：**
    ```bash
    git clone https://github.com/whchien/ai-trader.git
    cd ai-trader
    ```

2. **安裝套件：**

    **選項 A：使用 Poetry（推薦）**
    ```bash
    poetry install
    ```

    **選項 B：使用 pip**
    ```bash
    pip install -r requirements.txt
    ```

3. **安裝套件**（選擇性，用於 CLI 存取）：
    ```bash
    pip install -e .
    ```

### 運行第一次回測

**選項 1：使用 Python（快速）**
```python
from ai_trader import run_backtest
from ai_trader.backtesting.strategies.classic.sma import CrossSMAStrategy

# 使用範例資料執行回測
results = run_backtest(
    strategy=CrossSMAStrategy,
    data_source=None,  # 使用內建範例資料
    cash=1000000,
    commission=0.001425,
    strategy_params={"fast": 10, "slow": 30}
)
```

**選項 2：使用 CLI（推薦用於正式環境）**
```bash
# 從設定檔執行回測
ai-trader run config/backtest/classic/sma_example.yaml

# 快速回測，無需設定
ai-trader quick CrossSMAStrategy data/us_stock/tsm.csv --cash 100000

# 列出可用策略
ai-trader list-strategies
```

**選項 3：逐步控制**
```python
from ai_trader.utils.backtest import (
    create_cerebro, add_stock_data, add_sizer,
    add_default_analyzers, print_results
)
from ai_trader.backtesting.strategies.classic.bbands import BBandsStrategy

# 1. 建立 cerebro
cerebro = create_cerebro(cash=500000, commission=0.001)

# 2. 新增資料
add_stock_data(cerebro, source="data/AAPL.csv")

# 3. 新增策略
cerebro.addstrategy(BBandsStrategy, period=20, devfactor=2.0)

# 4. 設定
add_sizer(cerebro, "percent", percents=90)
add_default_analyzers(cerebro)

# 5. 執行
initial_value = cerebro.broker.getvalue()
results = cerebro.run()
final_value = cerebro.broker.getvalue()

# 6. 查看結果
print_results(results, initial_value, final_value)
```

### 下載市場資料

```bash
# 美股
ai-trader fetch AAPL --market us_stock --start-date 2020-01-01

# 台股
ai-trader fetch 2330 --market tw_stock --start-date 2020-01-01

# 加密貨幣
ai-trader fetch BTC-USD --market crypto --start-date 2020-01-01

# 外匯
ai-trader fetch EURUSD=X --market forex --start-date 2020-01-01
```

**使用 Python API：**
```python
from ai_trader.data.fetchers import ForexDataFetcher

# 取得歐元/美元資料
fetcher = ForexDataFetcher(
    symbol="EURUSD=X",
    start_date="2020-01-01",
    end_date="2024-12-31"
)
df = fetcher.fetch()
print(df.head())

# 常見外匯交易對
# 歐元/美元：'EURUSD=X'
# 英鎊/美元：'GBPUSD=X'
# 美元/日圓：'JPY=X'
# 美元/瑞郎：'CHF=X'
# 美元/加幣：'CAD=X'
# 澳幣/美元：'AUDUSD=X'
```

**注意：** 外匯資料的成交量為零，因為外匯市場是分散的，沒有集中交易所提供成交量資料。

## CLI 參考

### 可用命令

```bash
# 從設定檔執行回測
ai-trader run <config.yaml> [--strategy <name>] [--cash <amount>] [--commission <rate>]

# 快速回測，無需設定
ai-trader quick <StrategyName> <data_file> [options]

# 列出可用策略
ai-trader list-strategies [--type classic|portfolio|all]

# 取得市場資料
ai-trader fetch <symbol> --market <us_stock|tw_stock|crypto|forex|vix> [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]

# 顯示說明
ai-trader --help
```

### 設定檔案結構

建立 YAML 設定檔案（例如 `my_strategy.yaml`）：

```yaml
broker:
  cash: 1000000
  commission: 0.001425

data:
  file: "data/AAPL.csv"  # 單支股票
  # 或
  # directory: "./data/tw_stock/"  # 投資組合
  start_date: "2020-01-01"
  end_date: "2023-12-31"

strategy:
  class: "SMAStrategy"
  params:
    fast_period: 10
    slow_period: 30

sizer:
  type: "percent"  # 或 "fixed"
  params:
    percents: 95

analyzers:
  - sharpe
  - drawdown
  - returns
  - trades
```

**查看 `config/backtest/` 以取得完整範例。**

## 建立自訂策略

### 方法 1：簡單策略檔案

在 `ai_trader/backtesting/strategies/classic/` 中建立新的 Python 檔案：

```python
import backtrader as bt
from ai_trader.backtesting.strategies.base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    """我的自訂交易策略。"""

    params = dict(
        period=20,
        threshold=0.02,
    )

    def __init__(self):
        # 初始化指標
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.period)

    def next(self):
        # 交易邏輯
        if not self.position:
            # 進場條件
            if self.data.close[0] > self.sma[0] * (1 + self.params.threshold):
                self.buy()
        else:
            # 出場條件
            if self.data.close[0] < self.sma[0]:
                self.close()

# 選擇性：測試策略
if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    results = run_backtest(
        strategy=MyCustomStrategy,
        data_source=None,  # 使用範例資料
        strategy_params={"period": 20, "threshold": 0.02}
    )
```

### 方法 2：內聯策略（快速測試）

```python
import backtrader as bt
from ai_trader.utils.backtest import create_cerebro, add_stock_data, print_results

class QuickTestStrategy(bt.Strategy):
    def next(self):
        if not self.position and self.data.close[0] > self.data.close[-1]:
            self.buy()
        elif self.position and self.data.close[0] < self.data.close[-1]:
            self.sell()

cerebro = create_cerebro(cash=100000)
add_stock_data(cerebro, source="data/AAPL.csv")
cerebro.addstrategy(QuickTestStrategy)

initial = cerebro.broker.getvalue()
results = cerebro.run()
final = cerebro.broker.getvalue()
print_results(results, initial, final)
```

### 策略開發提示

1. **繼承 `BaseStrategy`** 以取得常見功能
2. **定義參數** 使用 `params = dict(...)`
3. **在 `__init__()` 中初始化指標**
4. **在 `next()` 方法中實現邏輯**
5. **用不同市場條件進行充分測試**
6. **使用日誌** 而不是 print 陳述式
7. **新增文件字串** 以解釋策略邏輯

## 專案結構

```
ai-trader/
├── ai_trader/                      # 主套件
│   ├── backtesting/               # 回測元件
│   │   ├── feeds/                 # 資料饋送處理器
│   │   └── strategies/            # 交易策略
│   │       ├── base.py            # 基礎策略類
│   │       ├── indicators.py      # 自訂指標
│   │       ├── classic/           # 單支股票策略 (15)
│   │       │   ├── sma.py
│   │       │   ├── bbands.py
│   │       │   ├── rsi.py
│   │       │   ├── macd.py
│   │       │   ├── momentum.py
│   │       │   ├── buyhold.py
│   │       │   ├── turtle.py
│   │       │   ├── vcp.py
│   │       │   ├── roc.py
│   │       │   ├── double_top.py
│   │       │   ├── rsrs.py
│   │       │   ├── risk_averse.py
│   │       │   ├── adaptive_rsi.py
│   │       │   ├── alpharsi_pro.py
│   │       │   └── hybrid_alpharsi.py
│   │       └── portfolio/         # 多支股票策略 (4)
│   │           ├── roc_rotation.py
│   │           ├── rsrs_rotation.py
│   │           ├── multi_bbands.py
│   │           └── triple_rsi.py
│   ├── core/                      # 核心工具
│   │   ├── config.py              # 設定管理
│   │   ├── exceptions.py          # 自訂例外
│   │   ├── logging.py             # 日誌設置
│   │   └── utils.py               # 輔助函式
│   ├── data/                      # 資料層
│   │   ├── fetchers/              # 資料取得器
│   │   │   ├── base.py            # 基礎取得器
│   │   │   ├── us_stock.py        # 美股資料
│   │   │   ├── tw_stock.py        # 台股資料
│   │   │   ├── crypto.py          # 加密貨幣資料
│   │   │   ├── forex.py           # 外匯資料
│   │   │   └── vix.py             # VIX 資料
│   │   └── storage/               # 資料儲存
│   │       └── base.py            # 儲存處理器
│   ├── mcp/                       # Model Context Protocol 伺服器
│   │   ├── server.py              # MCP 伺服器實現
│   │   ├── models.py              # MCP 資料模型
│   │   ├── __main__.py            # MCP 進入點
│   │   └── tools/                 # MCP 工具
│   │       ├── backtest.py        # 回測工具
│   │       ├── data.py            # 資料工具
│   │       └── strategies.py      # 策略工具
│   ├── utils/                     # 實用函式
│   │   ├── backtest.py            # 回測輔助
│   │   └── __init__.py
│   ├── __init__.py                # 套件初始化
│   └── cli.py                     # CLI 工具
├── config/                        # 設定檔案
│   └── backtest/                  # 回測設定
│       ├── classic/               # 經典策略設定
│       │   └── *.yaml
│       └── portfolio/             # 投資組合策略設定
│           └── *.yaml
├── scripts/                       # 輔助腳本
│   └── examples/                  # 範例腳本
│       ├── 01_simple_backtest.py
│       ├── 02_step_by_step.py
│       ├── 03_portfolio_backtest.py
│       ├── 04_pure_backtrader.py
│       └── 05_compare_strategies.py
├── tests/                         # 測試套件
│   ├── unit/                      # 單元測試
│   │   ├── backtesting/
│   │   ├── cli/
│   │   ├── core/
│   │   ├── data/
│   │   ├── mcp/
│   │   ├── utils/
│   │   └── conftest.py
│   ├── integration/               # 整合測試
│   │   ├── test_backtest_workflow.py
│   │   └── test_data_pipeline.py
│   └── conftest.py
├── docs/                          # 文件
│   ├── MIGRATION_GUIDE.md         # 從 v0.1.x 遷移
│   └── REFACTORING_SUMMARY.md     # v0.2.0 變更
├── agentic_ai_trader/             # 代理型交易模組
│   ├── data-science/
│   ├── financial-advisor/
│   └── trading-backtester/
├── data/                          # 資料目錄
│   ├── us_stock/                  # 美股資料
│   ├── tw_stock/                  # 台股資料
│   ├── crypto/                    # 加密貨幣資料
│   └── forex/                     # 外匯資料
├── pyproject.toml                 # Poetry 設定
├── requirements.txt               # Pip 需求
└── README_zh.md                   # 本檔案
```

## 文件和資源

- **[策略概述](ai_trader/backtesting/strategies/README.md)** - 從 v0.1.x 升級到 v0.2.0
- **[範例腳本](scripts/examples/)** - 5 個完整的工作範例
- **[設定範例](config/backtest/)** - YAML 設定樣板

### 範例腳本

1. **01_simple_backtest.py** - 使用 `run_backtest()` 快速開始
2. **02_step_by_step.py** - 詳細的逐步範例
3. **03_portfolio_backtest.py** - 多支股票投資組合策略
4. **04_pure_backtrader.py** - 純 Backtrader，不使用工具
5. **05_compare_strategies.py** - 比較多個策略

執行任何範例：
```bash
python scripts/examples/01_simple_backtest.py
```

## 🌐 MCP 伺服器整合

### 作為 MCP 伺服器運行

ai-trader 框架可以作為 Model Context Protocol (MCP) 伺服器運行，使像 Claude 這樣的 LLM 能夠通過標準協議與您的回測引擎互動。

#### 啟動伺服器

**選項 1：直接命令**
```bash
python -m ai_trader.mcp
```

**選項 2：使用 FastMCP CLI**
```bash
fastmcp dev ai_trader/mcp/server.py
```

#### Claude Desktop 設定

要將 ai-trader 與 Claude Desktop 整合，請將以下內容添加到 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "ai-trader": {
      "command": "python",
      "args": ["-m", "ai_trader.mcp"],
      "cwd": "/path/to/ai-trader"
    }
  }
}
```

將 `/path/to/ai-trader` 替換為您實際的專案目錄路徑。

#### 可用的 MCP 工具

MCP 伺服器公開 4 個強大的工具：

1. **run_backtest** - 從 YAML 設定檔執行回測
   - 支持策略覆蓋、現金調整和手續費設定
   - 適用於單支股票策略

2. **quick_backtest** - 快速回測，無需設定
   - 簡化的 ad-hoc 測試介面
   - 使用預設位置規模（95%）

3. **fetch_market_data** - 下載並保存市場資料
   - 支持：美股、台股、加密貨幣、外匯、VIX
   - 批次模式支持多個符號

4. **list_strategies** - 列出所有可用的策略
   - 返回經典（單支股票）和投資組合策略
   - 包含策略描述

#### 通過 Claude 使用範例

配置到 Claude Desktop 後，您可以要求 Claude：
- "運行 NaiveSMAStrategy 對 TSM 資料從 2020-2022 的回測"
- "列出所有可用的交易策略及其描述"
- "從 2020 年到 2024 年獲取蘋果股票資料"
- "比較不同策略的表現"

## 🔧 進階用法

### 比較多個策略

```python
from ai_trader import run_backtest
from ai_trader.backtesting.strategies.classic.sma import CrossSMAStrategy
from ai_trader.backtesting.strategies.classic.rsi import RsiBollingerBandsStrategy

strategies = [
    (CrossSMAStrategy, {"fast": 10, "slow": 30}),
    (RsiBollingerBandsStrategy, {"rsi_period": 14, "oversold": 30})
]

for strategy, params in strategies:
    print(f"\n測試 {strategy.__name__}...")
    results = run_backtest(
        strategy=strategy,
        strategy_params=params,
        print_output=True
    )
```

### 自訂資料來源

```python
import pandas as pd
from ai_trader.utils.backtest import create_cerebro, add_stock_data

# 載入自訂資料
df = pd.read_csv("my_data.csv", parse_dates=["Date"], index_col=["Date"])
# 必須包含以下欄位：Open, High, Low, Close, Volume

cerebro = create_cerebro()
add_stock_data(cerebro, source=df, name="CUSTOM")
# ... 繼續策略設置
```

### 投資組合優化

```python
from ai_trader.utils.backtest import create_cerebro, add_portfolio_data
from ai_trader.backtesting.strategies.portfolio.roc_rotation import ROCRotationStrategy

cerebro = create_cerebro(cash=2000000)
add_portfolio_data(cerebro, data_dir="./data/tw_stock/")

# 測試不同參數
for k in [3, 5, 7]:
    for days in [20, 30, 40]:
        cerebro.addstrategy(ROCRotationStrategy, k=k, rebalance_days=days)
        # ... 執行和分析
```

## 貢獻

歡迎貢獻！請隨時：

- 回報錯誤和問題
- 建議新功能或策略
- 提交拉取請求
- 改進文件
- 分享回測結果

## 授權

此專案根據 MIT 授權許可 - 有關詳細資訊，請參閱 LICENSE 檔案。

## 顯示你的支持

如果你發現此專案有幫助，請給它一個星星 ⭐️！你的支持激勵持續開發和改進。

## 聯繫方式

- **作者**: Will Chien
- **GitHub**: [@whchien](https://github.com/whchien)

## 致謝

- 基於優秀的 [Backtrader](https://www.backtrader.com/) 框架
- 受到量化交易社群的啟發
- 感謝所有貢獻者和使用者

---

**v0.1.x 使用者注意：** `AITrader` 類在 v0.2.0 中已棄用。請參閱 [遷移指南](docs/MIGRATION_GUIDE.md) 以取得升級說明。你的現有程式碼將繼續工作，但會發出棄用警告。