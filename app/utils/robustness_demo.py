"""
Robustness System Demo

This module demonstrates how to use the robustness system to prevent
race conditions and handle timeouts properly.
"""

import asyncio
import time
import streamlit as st
from typing import Dict, Any
from app.utils.robustness_integration import (
    initialize_robustness_system,
    get_system_status,
    create_robust_save_button,
    execute_robust_save,
    force_system_reset
)

def demo_save_operation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Demo save operation that simulates real work"""
    # Simulate some work
    time.sleep(2)
    
    # Simulate potential failure
    if data.get("should_fail", False):
        raise Exception("Simulated save failure")
    
    return {
        "success": True,
        "saved_items": len(data.get("items", [])),
        "timestamp": time.time()
    }

def demo_robust_save_button():
    """Demonstrate robust save button"""
    st.subheader("Robust Save Button Demo")
    
    # Create a robust save button
    create_robust_save_button(
        operation_type="demo_save",
        save_function=demo_save_operation,
        button_text="💾 Demo Save",
        button_key="demo_save_btn",
        timeout=10.0,
        disabled=False
    )
    
    # Show current data
    if "demo_data" not in st.session_state:
        st.session_state.demo_data = {
            "items": ["item1", "item2", "item3"],
            "should_fail": False
        }
    
    # Allow user to modify data
    st.session_state.demo_data["should_fail"] = st.checkbox("Simulate failure", value=st.session_state.demo_data["should_fail"])
    
    st.write("**Current Data:**", st.session_state.demo_data)

def demo_system_status():
    """Demonstrate system status monitoring"""
    st.subheader("System Status")
    
    # Get system status
    status = get_system_status()
    
    # Display status
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Active Operations", status.get("active_operations", 0))
        st.metric("System Health", status.get("system_health", "unknown"))
    
    with col2:
        st.metric("Global Processing", "Yes" if status.get("global_processing", False) else "No")
        st.metric("Initialized", "Yes" if status.get("initialized", False) else "No")
    
    # Show detailed status
    if st.expander("Detailed Status"):
        st.json(status)

def demo_emergency_reset():
    """Demonstrate emergency reset functionality"""
    st.subheader("Emergency Reset")
    
    st.warning("⚠️ Use this only if the system is completely stuck!")
    
    if st.button("🔄 Force System Reset", type="secondary"):
        with st.spinner("Resetting system..."):
            force_system_reset()
            st.success("✅ System reset completed!")
            st.rerun()

def demo_operation_tracking():
    """Demonstrate operation tracking"""
    st.subheader("Operation Tracking")
    
    # Show current operations
    from app.utils.operation_tracker import get_operation_tracker
    tracker = get_operation_tracker()
    
    active_ops = tracker.get_active_operations()
    if active_ops:
        st.write("**Active Operations:**")
        for op in active_ops:
            duration = op.calculate_duration()
            st.write(f"• {op.operation_type}: {duration:.1f}s")
    else:
        st.write("No active operations")
    
    # Show operation history
    history = tracker.get_operation_history(limit=5)
    if history:
        st.write("**Recent Operations:**")
        for op in history:
            st.write(f"• {op['operation_type']}: {op['status']} ({op.get('duration', 0):.1f}s)")

def demo_timeout_handling():
    """Demonstrate timeout handling"""
    st.subheader("Timeout Handling")
    
    # Create a button that will timeout
    if st.button("⏰ Test Timeout (5s)", key="timeout_test"):
        async def timeout_operation():
            # This will timeout after 5 seconds
            await asyncio.sleep(10)  # Sleep longer than timeout
            return {"success": True}
        
        # Execute with short timeout - execute_robust_save is async, so we need to await it
        async def run_timeout_test():
            return await execute_robust_save(
                operation_type="timeout_test",
                save_function=timeout_operation,
                timeout=5.0
            )
        
        # Run the async function
        result = asyncio.run(run_timeout_test())
        
        if result["success"]:
            st.success("✅ Operation completed!")
        else:
            st.error(f"❌ Operation failed: {result.get('error', 'Unknown error')}")

def main():
    """Main demo function"""
    st.title("🛡️ Robustness System Demo")
    
    # Initialize robustness system
    initialize_robustness_system()
    
    # Create tabs for different demos
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Save Button", "System Status", "Operation Tracking", "Timeout Handling", "Emergency Reset"
    ])
    
    with tab1:
        demo_robust_save_button()
    
    with tab2:
        demo_system_status()
    
    with tab3:
        demo_operation_tracking()
    
    with tab4:
        demo_timeout_handling()
    
    with tab5:
        demo_emergency_reset()
    
    # Show system information
    st.sidebar.title("System Information")
    st.sidebar.write("This demo shows the robustness system features:")
    st.sidebar.write("• Race condition prevention")
    st.sidebar.write("• Timeout handling")
    st.sidebar.write("• Operation tracking")
    st.sidebar.write("• Error recovery")
    st.sidebar.write("• Emergency reset")
    
    # Add refresh button
    if st.sidebar.button("🔄 Refresh Status"):
        st.rerun()

if __name__ == "__main__":
    main()
