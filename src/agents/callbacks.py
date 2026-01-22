"""Callback handler for tracking tool execution in LlamaIndex agent."""

import logging
import time
from typing import Any, Dict, List, Optional

from llama_index.core.callbacks import CallbackManager
from llama_index.core.callbacks.base import BaseCallbackHandler
from llama_index.core.callbacks.schema import CBEventType, EventPayload

logger = logging.getLogger(__name__)


class ToolExecutionTracker:
    """Tracks tool calls during agent execution."""

    def __init__(self):
        """Initialize the tracker."""
        self.tool_calls: List[Dict[str, Any]] = []
        self.current_step = 0
        self._tool_start_times: Dict[str, float] = {}
        self._tool_info: Dict[str, Dict[str, Any]] = {}  # Store tool name and args by event_id

    def reset(self) -> None:
        """Reset the tracker for a new execution."""
        self.tool_calls = []
        self.current_step = 0
        self._tool_start_times = {}
        self._tool_info = {}

    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """Get all tracked tool calls."""
        return self.tool_calls.copy()

    def on_event_start(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        """Handle event start."""
        logger.info(f"Tracker: event_start - type={event_type}, event_id={event_id}, payload_keys={list(payload.keys()) if payload else 'None'}")
        if event_type == CBEventType.FUNCTION_CALL:
            # Track tool call start
            # Extract tool information from payload
            tool_name = "unknown"
            tool_args = {}
            
            if payload:
                # Try different ways to extract tool information
                func_call = payload.get(EventPayload.FUNCTION_CALL, {})
                if isinstance(func_call, dict):
                    tool_name = func_call.get("name", func_call.get("function", {}).get("name", "unknown"))
                    # Try to get arguments
                    if "arguments" in func_call:
                        tool_args = func_call["arguments"]
                    elif "args" in func_call:
                        tool_args = func_call["args"]
                    elif "function" in func_call and "arguments" in func_call["function"]:
                        tool_args = func_call["function"]["arguments"]
                
                # Also check if tool info is directly in payload
                if tool_name == "unknown" and "name" in payload:
                    tool_name = payload["name"]
                if not tool_args and "args" in payload:
                    tool_args = payload["args"]
                if not tool_args and "arguments" in payload:
                    tool_args = payload["arguments"]
            
            self.current_step += 1
            start_time = time.time()
            self._tool_start_times[event_id] = start_time
            self._tool_info[event_id] = {"name": tool_name, "args": tool_args}
            
            logger.info(f"Tool call started: {tool_name} with args: {tool_args}")
        
        return event_id

    def on_event_end(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        """Handle event end."""
        if event_type == CBEventType.FUNCTION_CALL:
            # Track tool call end
            # Extract tool information from payload
            tool_name = "unknown"
            tool_args = {}
            tool_result = ""
            
            if payload:
                # Get function output
                tool_result = payload.get(EventPayload.FUNCTION_OUTPUT, "")
                
                # Extract tool name and args from function call
                func_call = payload.get(EventPayload.FUNCTION_CALL, {})
                if isinstance(func_call, dict):
                    tool_name = func_call.get("name", func_call.get("function", {}).get("name", "unknown"))
                    # Try to get arguments
                    if "arguments" in func_call:
                        tool_args = func_call["arguments"]
                    elif "args" in func_call:
                        tool_args = func_call["args"]
                    elif "function" in func_call and "arguments" in func_call["function"]:
                        tool_args = func_call["function"]["arguments"]
                
                # Also check if tool info is directly in payload
                if tool_name == "unknown" and "name" in payload:
                    tool_name = payload["name"]
                if not tool_args and "args" in payload:
                    tool_args = payload["args"]
                if not tool_args and "arguments" in payload:
                    tool_args = payload["arguments"]
            
            # If we don't have tool name from end event, get it from start event
            if event_id in self._tool_info:
                stored_info = self._tool_info.pop(event_id, {})
                if tool_name == "unknown":
                    tool_name = stored_info.get("name", "unknown")
                if not tool_args:
                    tool_args = stored_info.get("args", {})
            
            start_time = self._tool_start_times.pop(event_id, time.time())
            execution_time = time.time() - start_time
            
            # Truncate result if too long
            result_str = str(tool_result)
            if len(result_str) > 1000:
                result_str = result_str[:1000] + "... [truncated]"
            
            tool_call = {
                "step_number": self.current_step,
                "tool_name": tool_name,
                "parameters": tool_args,
                "result": result_str,
                "execution_time": execution_time,
                "timestamp": start_time,
            }
            
            self.tool_calls.append(tool_call)
            logger.info(f"Tool call completed: {tool_name} in {execution_time:.3f}s")
        
        elif event_type == CBEventType.LLM:
            # Check for tool calls in LLM response
            if payload:
                messages = payload.get(EventPayload.MESSAGES, [])
                for msg in messages:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            self.current_step += 1
                            tool_call_data = {
                                "step_number": self.current_step,
                                "tool_name": tool_call.get("function", {}).get("name", "unknown"),
                                "parameters": tool_call.get("function", {}).get("arguments", {}),
                                "result": "",
                                "execution_time": 0.0,
                                "timestamp": time.time(),
                            }
                            self.tool_calls.append(tool_call_data)


class ToolExecutionCallbackHandler(BaseCallbackHandler):
    """Custom callback handler that tracks tool execution."""

    def __init__(self, tracker: ToolExecutionTracker):
        """Initialize with a tracker."""
        super().__init__(event_starts_to_ignore=[], event_ends_to_ignore=[])
        self.tracker = tracker

    def start_trace(self, trace_id: Optional[str] = None) -> None:
        """Start a trace (required by BaseCallbackHandler)."""
        pass

    def end_trace(
        self,
        trace_id: Optional[str] = None,
        trace_map: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """End a trace (required by BaseCallbackHandler)."""
        pass

    def on_event_start(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        """Handle event start."""
        logger.debug(f"Callback: event_start - type={event_type}, event_id={event_id}")
        self.tracker.on_event_start(event_type, payload, event_id, parent_id, **kwargs)
        return event_id

    def on_event_end(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        """Handle event end."""
        logger.debug(f"Callback: event_end - type={event_type}, event_id={event_id}")
        self.tracker.on_event_end(event_type, payload, event_id, **kwargs)


def create_callback_manager(tracker: ToolExecutionTracker) -> CallbackManager:
    """Create a callback manager with tool execution tracking."""
    handler = ToolExecutionCallbackHandler(tracker)
    return CallbackManager([handler])
