# Validation Rules & Error Handling

Pre-flight checks, validation procedures, and error handling for strategy creation.

## Table of Contents

1. [Pre-Creation Validation](#pre-creation-validation)
2. [Post-Creation Verification](#post-creation-verification)
3. [Error Handling](#error-handling)
4. [Common Issues & Solutions](#common-issues--solutions)

---

## Pre-Creation Validation

### 1. Strategy Name Validation

**Check:** Class name is valid PascalCase and doesn't conflict with existing strategies

```python
def validate_class_name(class_name: str, strategy_type: str) -> tuple[bool, str]:
    """
    Validate strategy class name.

    Returns:
        (is_valid, error_message)
    """
    # Check PascalCase format
    if not class_name[0].isupper():
        return False, "Class name must start with uppercase letter"

    if not class_name.replace('Strategy', '').replace('_', '').isalnum():
        return False, "Class name must contain only letters and numbers"

    # Check for 'Strategy' suffix
    if not class_name.endswith('Strategy'):
        return False, "Class name must end with 'Strategy' (e.g., 'MyStrategy')"

    # Check for conflicts with existing strategies
    import_path = f"ai_trader.backtesting.strategies.{strategy_type}"
    try:
        module = __import__(import_path, fromlist=['__all__'])
        if class_name in module.__all__:
            return False, f"Strategy '{class_name}' already exists"
    except (ImportError, AttributeError):
        pass

    return True, ""
```

**Valid Examples:**
- `MACDBBandsStrategy` ✓
- `DoubleTopStrategy` ✓
- `TripleEMARotationStrategy` ✓
- `BBandsStrategy` ✓

**Invalid Examples:**
- `MacdbbandStrategy` ✗ (not PascalCase)
- `MACDBBands` ✗ (missing 'Strategy' suffix)
- `macd_bbands_strategy` ✗ (snake_case, not PascalCase)
- `MACD_BBANDS` ✗ (all caps)

### 2. Filename Validation

**Check:** Derived snake_case filename doesn't already exist

```python
def validate_filename(class_name: str, strategy_type: str) -> tuple[bool, str]:
    """
    Validate that the derived filename is available.

    Returns:
        (is_valid, error_message)
    """
    # Convert class name to snake_case filename
    snake_case = class_name_to_snake_case(class_name)
    filepath = f"ai_trader/backtesting/strategies/{strategy_type}/{snake_case}.py"

    import os
    if os.path.exists(filepath):
        return False, f"File already exists: {filepath}"

    return True, ""


def class_name_to_snake_case(class_name: str) -> str:
    """Convert PascalCase to snake_case."""
    # Remove 'Strategy' suffix
    name = class_name.replace('Strategy', '')

    # Insert underscores before capitals (except first)
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append('_')
        result.append(char.lower())

    return ''.join(result)


# Examples:
assert class_name_to_snake_case('MACDBBandsStrategy') == 'macd_bbands'
assert class_name_to_snake_case('DoubleTopStrategy') == 'double_top'
assert class_name_to_snake_case('BBandsStrategy') == 'bbands'
```

### 3. Strategy Type Validation

**Check:** Type is either "classic" or "portfolio"

```python
def validate_strategy_type(strategy_type: str) -> tuple[bool, str]:
    """
    Validate strategy type is valid.

    Returns:
        (is_valid, error_message)
    """
    valid_types = ['classic', 'portfolio']
    if strategy_type not in valid_types:
        return False, f"Strategy type must be '{valid_types[0]}' or '{valid_types[1]}'"

    import os
    base_path = f"ai_trader/backtesting/strategies/{strategy_type}"
    if not os.path.isdir(base_path):
        return False, f"Strategy directory does not exist: {base_path}"

    return True, ""
```

### 4. Parameter Validation

**Check:** All parameters have defaults and use valid Python identifiers

```python
def validate_parameters(params_str: str) -> tuple[bool, list[tuple[str, str]], str]:
    """
    Parse and validate parameter string.

    Args:
        params_str: Comma-separated "name=value" pairs (e.g., "fast=12, slow=26")

    Returns:
        (is_valid, parsed_params, error_message)

    Example:
        >>> validate_parameters("fast=12, slow=26, period=20")
        (True, [('fast', '12'), ('slow', '26'), ('period', '20')], "")
    """
    import keyword

    if not params_str or params_str.strip() == '':
        return True, [], ""

    params = []
    pairs = params_str.split(',')

    for pair in pairs:
        pair = pair.strip()
        if '=' not in pair:
            return False, [], f"Invalid parameter format: '{pair}' (use name=value)"

        name, value = pair.split('=', 1)
        name = name.strip()
        value = value.strip()

        # Check valid identifier
        if not name.isidentifier():
            return False, [], f"Invalid parameter name: '{name}' (must be valid Python identifier)"

        # Check not a keyword
        if keyword.iskeyword(name):
            return False, [], f"Parameter name cannot be Python keyword: '{name}'"

        # Check default value is present
        if not value:
            return False, [], f"Parameter '{name}' must have a default value"

        # Validate value format (simple check)
        try:
            # Try to eval the value - should be a literal
            eval(value, {"__builtins__": {}})
        except:
            return False, [], f"Invalid parameter default value: {name}={value}"

        params.append((name, value))

    return True, params, ""
```

**Valid Examples:**
- `period=20` ✓
- `fast=12, slow=26, signal=9` ✓
- `bb_period=20, bb_dev=2.0` ✓
- `use_filter=True, top_k=5` ✓

**Invalid Examples:**
- `period` ✗ (no default value)
- `fast=, slow=26` ✗ (missing value)
- `12fast=12` ✗ (parameter name not valid identifier)
- `class=20` ✗ (Python keyword)

### 5. Custom Indicator Validation

**Check:** Referenced custom indicators exist in `indicators.py`

```python
def validate_custom_indicators(indicators_list: list[str]) -> tuple[bool, str]:
    """
    Validate that custom indicators exist in indicators.py.

    Args:
        indicators_list: List of indicator class names (e.g., ['DoubleTop', 'RSRS'])

    Returns:
        (is_valid, error_message)
    """
    from ai_trader.backtesting.strategies import indicators

    available_indicators = [name for name in dir(indicators) if not name.startswith('_')]

    for indicator in indicators_list:
        if indicator not in available_indicators:
            return False, f"Indicator '{indicator}' not found in indicators.py"

    return True, ""
```

**Valid Examples:**
- `['DoubleTop']` ✓
- `['RSRS', 'NormRSRS']` ✓
- `[]` (no custom indicators) ✓

**Invalid Examples:**
- `['CustomIndicator']` ✗ (doesn't exist)
- `['doubleto']` ✗ (wrong case)

---

## Post-Creation Verification

### 1. File Creation Verification

**Check:** Strategy file was created successfully

```python
def verify_file_created(filepath: str) -> tuple[bool, str]:
    """
    Verify that the strategy file was created.

    Returns:
        (is_valid, error_message)
    """
    import os

    if not os.path.isfile(filepath):
        return False, f"File not created: {filepath}"

    # Check file has content
    size = os.path.getsize(filepath)
    if size == 0:
        return False, f"File is empty: {filepath}"

    return True, ""
```

### 2. Registration Verification

**Check:** Import and __all__ were updated correctly in `__init__.py`

```python
def verify_registration(class_name: str, strategy_type: str, filename: str) -> tuple[bool, str]:
    """
    Verify that the strategy was registered in __init__.py.

    Args:
        class_name: Full class name (e.g., 'MACDBBandsStrategy')
        strategy_type: 'classic' or 'portfolio'
        filename: Snake-case filename without .py (e.g., 'macd_bbands')

    Returns:
        (is_valid, error_message)
    """
    init_path = f"ai_trader/backtesting/strategies/{strategy_type}/__init__.py"

    with open(init_path, 'r') as f:
        content = f.read()

    # Check import statement exists
    expected_import = f"from ai_trader.backtesting.strategies.{strategy_type}.{filename} import {class_name}"
    if expected_import not in content:
        return False, f"Import not found in __init__.py: {expected_import}"

    # Check __all__ entry exists
    if f'"{class_name}"' not in content and f"'{class_name}'" not in content:
        return False, f"Class name not found in __all__: {class_name}"

    return True, ""
```

### 3. Import Verification

**Check:** Strategy file is syntactically valid and can be imported

```python
def verify_import(class_name: str, strategy_type: str) -> tuple[bool, str]:
    """
    Verify that the strategy can be imported without errors.

    Args:
        class_name: Full class name (e.g., 'MACDBBandsStrategy')
        strategy_type: 'classic' or 'portfolio'

    Returns:
        (is_valid, error_message)
    """
    try:
        # Import the strategy module
        module_path = f"ai_trader.backtesting.strategies.{strategy_type}"
        module = __import__(module_path, fromlist=[class_name])

        # Check the class exists
        if not hasattr(module, class_name):
            return False, f"Class '{class_name}' not found in module"

        # Try to instantiate (minimal check)
        strategy_class = getattr(module, class_name)
        if not issubclass(strategy_class, BaseStrategy):
            return False, f"Class '{class_name}' does not inherit from BaseStrategy"

        return True, ""

    except ImportError as e:
        return False, f"Import error: {str(e)}"
    except SyntaxError as e:
        return False, f"Syntax error in generated file: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
```

### 4. Git Status Verification

**Check:** New files appear in git status

```python
def verify_git_status(filepath: str, init_filepath: str) -> tuple[bool, str]:
    """
    Verify that git recognizes the new/modified files.

    Args:
        filepath: Path to strategy file
        init_filepath: Path to __init__.py

    Returns:
        (is_valid, error_message)
    """
    import subprocess

    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd='ai_trader/backtesting/strategies',
            capture_output=True,
            text=True
        )

        status_output = result.stdout
        # Check that at least one file appears in status
        if filepath.split('/')[-1] not in status_output:
            return False, "Strategy file not recognized by git"

        return True, ""

    except Exception as e:
        return False, f"Could not check git status: {str(e)}"
```

---

## Error Handling

### Validation Workflow

```python
def validate_strategy_creation(
    class_name: str,
    strategy_type: str,
    params_str: str,
    custom_indicators: list[str] = None
) -> tuple[bool, dict]:
    """
    Run all validation checks.

    Returns:
        (all_valid, validation_results)
        validation_results = {
            'class_name': (is_valid, error_msg),
            'filename': (is_valid, error_msg),
            'type': (is_valid, error_msg),
            'parameters': (is_valid, error_msg),
            'indicators': (is_valid, error_msg),
        }
    """
    results = {}

    # 1. Validate type first (needed for other checks)
    results['type'] = validate_strategy_type(strategy_type)
    if not results['type'][0]:
        return False, results

    # 2. Validate class name
    results['class_name'] = validate_class_name(class_name, strategy_type)
    if not results['class_name'][0]:
        return False, results

    # 3. Validate filename
    results['filename'] = validate_filename(class_name, strategy_type)
    if not results['filename'][0]:
        return False, results

    # 4. Validate parameters
    param_valid, params_list, param_error = validate_parameters(params_str)
    results['parameters'] = (param_valid, param_error)
    if not param_valid:
        return False, results

    # 5. Validate custom indicators
    indicators = custom_indicators or []
    results['indicators'] = validate_custom_indicators(indicators)
    if not results['indicators'][0]:
        return False, results

    return True, results
```

---

## Common Issues & Solutions

### Issue 1: File Already Exists

**Error Message:**
```
File already exists: ai_trader/backtesting/strategies/classic/macd_bbands.py
```

**Cause:** A strategy file with that name already exists

**Solution:**
1. Check if `MACDBBandsStrategy` already exists: `ai-trader list | grep MACD`
2. Choose a different name: `MACDBBandsOptimizedStrategy`
3. If rewriting, delete the old file first: `rm ai_trader/backtesting/strategies/classic/macd_bbands.py`

---

### Issue 2: Class Name Already in __all__

**Error Message:**
```
Strategy 'CrossSMAStrategy' already exists
```

**Cause:** The class name is already registered in the strategy module

**Solution:**
1. Use a different name: `CrossSMA5050Strategy`
2. Or modify the existing strategy if you want to improve it

---

### Issue 3: Invalid Parameter Name

**Error Message:**
```
Invalid parameter name: '2fast' (must be valid Python identifier)
Invalid parameter name: 'class' (cannot be Python keyword)
```

**Cause:** Parameter name violates Python naming rules

**Solution:**
1. Start with a letter: `fast` ✓, not `2fast` ✗
2. Use letters, numbers, underscores: `fast_period=12` ✓, not `fast-period=12` ✗
3. Avoid Python keywords: `period=20` ✓, not `class=20` ✗

---

### Issue 4: Missing Parameter Default Value

**Error Message:**
```
Invalid parameter format: 'fast=' (use name=value)
Parameter 'slow' must have a default value
```

**Cause:** Parameter doesn't have a default value

**Solution:**
Provide defaults for all parameters:
- Good: `fast=12, slow=26, signal=9`
- Bad: `fast=12, slow=, signal=9`

---

### Issue 5: Custom Indicator Not Found

**Error Message:**
```
Indicator 'CustomMACD' not found in indicators.py
```

**Cause:** The custom indicator doesn't exist in the indicators module

**Solution:**
1. Check available indicators: Open `indicators.py` and see what's available
2. Use existing custom indicators: `DoubleTop`, `RSRS`, `NormRSRS`, `RecentHigh`, `TripleRSI`
3. Use standard backtrader indicators: `bt.indicators.SMA()`, `bt.indicators.MACD()`, etc.
4. If you need a custom indicator, add it to `indicators.py` first

---

### Issue 6: Import Failed

**Error Message:**
```
Syntax error in generated file: unexpected indent on line 42
Import error: No module named 'ai_trader.backtesting.strategies.classic.my_strategy'
```

**Cause:** The generated strategy file has a syntax error

**Solution:**
1. Check the generated file for syntax errors
2. Ensure all indentation is correct (4 spaces, no tabs)
3. Verify class docstring is properly closed with `"""`
4. Check that all method definitions are indented correctly

---

### Issue 7: Git Not Tracking Files

**Error Message:**
```
Strategy file not recognized by git
```

**Cause:** The file was created but git isn't tracking it

**Solution:**
1. Check git status: `git status`
2. The files should appear as "untracked" (new) or "modified" (__init__.py)
3. If not appearing, try: `git add ai_trader/backtesting/strategies/classic/your_file.py`

---

### Issue 8: Class Doesn't Inherit from BaseStrategy

**Error Message:**
```
Class 'MyStrategy' does not inherit from BaseStrategy
```

**Cause:** The generated class template was modified and doesn't inherit properly

**Solution:**
1. Verify the class definition: `class YourStrategyStrategy(BaseStrategy):`
2. Ensure the import: `from ai_trader.backtesting.strategies.base import BaseStrategy`
3. Call super().__init__() in __init__

---

## Pre-Flight Checklist

Before confirming strategy creation, verify:

- [ ] Class name is PascalCase with 'Strategy' suffix
- [ ] Strategy type is 'classic' or 'portfolio'
- [ ] No class name conflicts with existing strategies
- [ ] All parameters have default values
- [ ] Parameter names are valid Python identifiers
- [ ] Custom indicators (if any) exist in indicators.py
- [ ] Target filename doesn't already exist
- [ ] Description and entry/exit conditions provided

## Post-Creation Checklist

After creation, verify:

- [ ] Strategy file created at correct path
- [ ] File has valid Python syntax (can be imported)
- [ ] Import added to __init__.py
- [ ] Class name added to __all__ in alphabetical order
- [ ] Git recognizes new/modified files
- [ ] Can run standalone backtest: `python path/to/strategy.py`

---

Generated with Claude Code