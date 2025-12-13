#!/usr/bin/env python3
"""
Script to update strategy files to use new utilities instead of AITrader.
"""
import re
from pathlib import Path


def update_strategy_file(file_path):
    """Update a single strategy file."""
    print(f"Updating {file_path.name}...")

    with open(file_path, "r") as f:
        content = f.read()

    # Skip if already updated
    if "from ai_trader.trader import AITrader" not in content:
        print(f"  Skipped: Already updated")
        return

    # Remove AITrader import
    content = re.sub(
        r"from ai_trader\.trader import AITrader\n",
        "",
        content,
    )

    # Extract strategy class name from the file
    # Look for the last class definition before __main__
    class_matches = re.findall(r"class (\w+Strategy)\(", content)
    if not class_matches:
        print(f"  Warning: No strategy class found")
        return

    strategy_name = class_matches[-1]  # Use the last one (usually the main one)

    # Find the __main__ block and replace it
    old_main_pattern = r'if __name__ == "__main__":\s+trader = AITrader\(\).*?trader\.plot\(\)'

    new_main = f'''if __main__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with {strategy_name}
    results = run_backtest(
        strategy={strategy_name},
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("\\nBacktest completed! Use cerebro.plot() to visualize results.")'''

    content = re.sub(old_main_pattern, new_main, content, flags=re.DOTALL)

    # Write back
    with open(file_path, "w") as f:
        f.write(content)

    print(f"  ✓ Updated")


def main():
    """Update all strategy files."""
    base_dir = Path(__file__).parent.parent / "ai_trader" / "backtesting" / "strategies"

    # Get all classic strategy files
    classic_dir = base_dir / "classic"
    classic_files = list(classic_dir.glob("*.py"))
    classic_files = [f for f in classic_files if f.name != "__init__.py"]

    # Get all portfolio strategy files
    portfolio_dir = base_dir / "portfolio"
    portfolio_files = list(portfolio_dir.glob("*.py"))
    portfolio_files = [f for f in portfolio_files if f.name != "__init__.py"]

    all_files = classic_files + portfolio_files

    print(f"\nFound {len(all_files)} strategy files to update\n")

    for file_path in all_files:
        update_strategy_file(file_path)

    print(f"\n✓ All strategy files updated!")


if __name__ == "__main__":
    main()
