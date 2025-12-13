"""Agent delegation tools for the Root Coordinator Agent."""

import logging
from typing import Any, Dict

from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

logger = logging.getLogger(__name__)


async def call_strategy_analysis_agent(
    request: str,
    market_symbol: str = None,
    time_period: str = "1y",
    tool_context: ToolContext = None,
) -> str:
    """Call the Strategy Analysis Agent to analyze market conditions and recommend strategies.
    
    Args:
        request: Natural language request for strategy analysis
        market_symbol: Stock symbol to analyze (optional)
        time_period: Time period for analysis ('1y', '2y', '5y')
        tool_context: Tool context for state management
        
    Returns:
        Strategy analysis and recommendations
    """
    logger.info(f"Calling Strategy Analysis Agent: {request}")
    
    try:
        # Import the strategy analysis agent (will be implemented in Phase 2)
        from ..sub_agents.strategy_analysis import strategy_analysis_agent
        
        # Prepare the request with context
        enhanced_request = f"""
        Analysis Request: {request}
        
        Context:
        - Market Symbol: {market_symbol or 'Not specified'}
        - Time Period: {time_period}
        - Available Market Data: {list(tool_context.state.keys()) if tool_context else 'None'}
        
        Please provide:
        1. Market condition analysis
        2. Recommended trading strategies
        3. Rationale for recommendations
        4. Key parameters to consider
        """
        
        # Create agent tool and call
        agent_tool = AgentTool(agent=strategy_analysis_agent)
        
        result = await agent_tool.run_async(
            args={"request": enhanced_request},
            tool_context=tool_context
        )
        
        # Store result in context
        if tool_context:
            tool_context.state["strategy_analysis_output"] = result
        
        logger.info("Strategy Analysis Agent completed successfully")
        return result
        
    except ImportError:
        # Placeholder response for Phase 1
        placeholder_response = f"""
        Strategy Analysis Agent (Placeholder - Phase 2):
        
        Request: {request}
        Market Symbol: {market_symbol}
        Time Period: {time_period}
        
        This agent will analyze market conditions and recommend optimal strategies.
        Implementation coming in Phase 2.
        """
        
        if tool_context:
            tool_context.state["strategy_analysis_output"] = placeholder_response
        
        return placeholder_response
        
    except Exception as e:
        logger.error(f"Error calling Strategy Analysis Agent: {e}")
        return f"Error in Strategy Analysis Agent: {str(e)}"


async def call_backtesting_execution_agent(
    request: str,
    strategy_name: str = None,
    parameters: Dict[str, Any] = None,
    tool_context: ToolContext = None,
) -> str:
    """Call the Backtesting Execution Agent to run backtests.
    
    Args:
        request: Natural language request for backtesting
        strategy_name: Name of strategy to backtest (optional)
        parameters: Strategy parameters (optional)
        tool_context: Tool context for state management
        
    Returns:
        Backtesting execution results
    """
    logger.info(f"Calling Backtesting Execution Agent: {request}")
    
    try:
        # Import the backtesting execution agent (will be implemented in Phase 3)
        from ..sub_agents.backtesting_execution import backtesting_execution_agent
        
        # Prepare the request with context
        enhanced_request = f"""
        Backtesting Request: {request}
        
        Context:
        - Strategy Name: {strategy_name or 'Not specified'}
        - Parameters: {parameters or 'Default parameters'}
        - Available Strategies: {tool_context.state.get('available_strategies', {}).keys() if tool_context else 'None'}
        - Market Data: {[k for k in tool_context.state.keys() if k.startswith('market_data_')] if tool_context else 'None'}
        
        Please:
        1. Execute the requested backtests
        2. Return performance metrics
        3. Provide execution summary
        """
        
        # Create agent tool and call
        agent_tool = AgentTool(agent=backtesting_execution_agent)
        
        result = await agent_tool.run_async(
            args={"request": enhanced_request},
            tool_context=tool_context
        )
        
        # Store result in context
        if tool_context:
            tool_context.state["backtesting_execution_output"] = result
        
        logger.info("Backtesting Execution Agent completed successfully")
        return result
        
    except ImportError:
        # Placeholder response for Phase 1
        placeholder_response = f"""
        Backtesting Execution Agent (Placeholder - Phase 3):
        
        Request: {request}
        Strategy: {strategy_name}
        Parameters: {parameters}
        
        This agent will execute backtests using the ai_trader framework.
        Implementation coming in Phase 3.
        """
        
        if tool_context:
            tool_context.state["backtesting_execution_output"] = placeholder_response
        
        return placeholder_response
        
    except Exception as e:
        logger.error(f"Error calling Backtesting Execution Agent: {e}")
        return f"Error in Backtesting Execution Agent: {str(e)}"


async def call_performance_evaluation_agent(
    request: str,
    tool_context: ToolContext = None,
) -> str:
    """Call the Performance Evaluation Agent to analyze backtest results.
    
    Args:
        request: Natural language request for performance evaluation
        tool_context: Tool context for state management
        
    Returns:
        Performance evaluation and insights
    """
    logger.info(f"Calling Performance Evaluation Agent: {request}")
    
    try:
        # Import the performance evaluation agent (will be implemented in Phase 4)
        from ..sub_agents.performance_evaluation import performance_evaluation_agent
        
        # Prepare the request with context
        enhanced_request = f"""
        Performance Evaluation Request: {request}
        
        Available Results:
        - Backtesting Results: {'Available' if tool_context and 'backtesting_execution_output' in tool_context.state else 'Not available'}
        - Strategy Analysis: {'Available' if tool_context and 'strategy_analysis_output' in tool_context.state else 'Not available'}
        
        Please provide:
        1. Comprehensive performance analysis
        2. Key insights and patterns
        3. Comparative analysis if multiple strategies
        4. Visualization recommendations
        """
        
        # Create agent tool and call
        agent_tool = AgentTool(agent=performance_evaluation_agent)
        
        result = await agent_tool.run_async(
            args={"request": enhanced_request},
            tool_context=tool_context
        )
        
        # Store result in context
        if tool_context:
            tool_context.state["performance_evaluation_output"] = result
        
        logger.info("Performance Evaluation Agent completed successfully")
        return result
        
    except ImportError:
        # Placeholder response for Phase 1
        placeholder_response = f"""
        Performance Evaluation Agent (Placeholder - Phase 4):
        
        Request: {request}
        
        This agent will provide comprehensive performance analysis and insights.
        Implementation coming in Phase 4.
        """
        
        if tool_context:
            tool_context.state["performance_evaluation_output"] = placeholder_response
        
        return placeholder_response
        
    except Exception as e:
        logger.error(f"Error calling Performance Evaluation Agent: {e}")
        return f"Error in Performance Evaluation Agent: {str(e)}"


async def call_risk_assessment_agent(
    request: str,
    tool_context: ToolContext = None,
) -> str:
    """Call the Risk Assessment Agent to analyze risk metrics.
    
    Args:
        request: Natural language request for risk assessment
        tool_context: Tool context for state management
        
    Returns:
        Risk assessment and recommendations
    """
    logger.info(f"Calling Risk Assessment Agent: {request}")
    
    try:
        # Import the risk assessment agent (will be implemented in Phase 4)
        from ..sub_agents.risk_assessment import risk_assessment_agent
        
        # Prepare the request with context
        enhanced_request = f"""
        Risk Assessment Request: {request}
        
        Available Data:
        - Backtesting Results: {'Available' if tool_context and 'backtesting_execution_output' in tool_context.state else 'Not available'}
        - Performance Analysis: {'Available' if tool_context and 'performance_evaluation_output' in tool_context.state else 'Not available'}
        
        Please provide:
        1. Comprehensive risk analysis
        2. Risk metrics calculation
        3. Risk warnings and recommendations
        4. Stress testing insights
        """
        
        # Create agent tool and call
        agent_tool = AgentTool(agent=risk_assessment_agent)
        
        result = await agent_tool.run_async(
            args={"request": enhanced_request},
            tool_context=tool_context
        )
        
        # Store result in context
        if tool_context:
            tool_context.state["risk_assessment_output"] = result
        
        logger.info("Risk Assessment Agent completed successfully")
        return result
        
    except ImportError:
        # Placeholder response for Phase 1
        placeholder_response = f"""
        Risk Assessment Agent (Placeholder - Phase 4):
        
        Request: {request}
        
        This agent will provide comprehensive risk analysis and stress testing.
        Implementation coming in Phase 4.
        """
        
        if tool_context:
            tool_context.state["risk_assessment_output"] = placeholder_response
        
        return placeholder_response
        
    except Exception as e:
        logger.error(f"Error calling Risk Assessment Agent: {e}")
        return f"Error in Risk Assessment Agent: {str(e)}"


async def call_optimization_agent(
    request: str,
    optimization_type: str = "parameters",
    tool_context: ToolContext = None,
) -> str:
    """Call the Optimization Agent for strategy and parameter optimization.
    
    Args:
        request: Natural language request for optimization
        optimization_type: Type of optimization ('parameters', 'ensemble', 'walkforward')
        tool_context: Tool context for state management
        
    Returns:
        Optimization results and recommendations
    """
    logger.info(f"Calling Optimization Agent: {request}")
    
    try:
        # Import the optimization agent (will be implemented in Phase 5)
        from ..sub_agents.optimization import optimization_agent
        
        # Prepare the request with context
        enhanced_request = f"""
        Optimization Request: {request}
        Optimization Type: {optimization_type}
        
        Available Data:
        - Backtesting Results: {'Available' if tool_context and 'backtesting_execution_output' in tool_context.state else 'Not available'}
        - Performance Analysis: {'Available' if tool_context and 'performance_evaluation_output' in tool_context.state else 'Not available'}
        - Risk Assessment: {'Available' if tool_context and 'risk_assessment_output' in tool_context.state else 'Not available'}
        
        Please provide:
        1. Optimization analysis
        2. Optimal parameters or configurations
        3. Validation results
        4. Implementation recommendations
        """
        
        # Create agent tool and call
        agent_tool = AgentTool(agent=optimization_agent)
        
        result = await agent_tool.run_async(
            args={"request": enhanced_request},
            tool_context=tool_context
        )
        
        # Store result in context
        if tool_context:
            tool_context.state["optimization_output"] = result
        
        logger.info("Optimization Agent completed successfully")
        return result
        
    except ImportError:
        # Placeholder response for Phase 1
        placeholder_response = f"""
        Optimization Agent (Placeholder - Phase 5):
        
        Request: {request}
        Optimization Type: {optimization_type}
        
        This agent will provide advanced optimization and parameter tuning.
        Implementation coming in Phase 5.
        """
        
        if tool_context:
            tool_context.state["optimization_output"] = placeholder_response
        
        return placeholder_response
        
    except Exception as e:
        logger.error(f"Error calling Optimization Agent: {e}")
        return f"Error in Optimization Agent: {str(e)}"