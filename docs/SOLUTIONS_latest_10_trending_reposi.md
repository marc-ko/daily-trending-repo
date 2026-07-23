class ExecutionHarnessEngine:
    def __init__(self):
        # Assuming other initialization logic here...

        # This is the suspected location where memory_store is initialized, 
        # which calls _initialize_context_manager()
        self._memory_store: "AgentContext" = self._initialize_context_manager()

    def _initialize_context_manager(self) -> "AgentContext":
        """Initializes and returns the agent context manager."""
        # FIX applied here: Replaced the problematic emoji (\U0001f916) 
        # with plain text to prevent UnicodeEncodeError on non-UTF8 systems.
        print("Initializing Context Manager...")
        return "AgentContext_Instance"

# Example usage to ensure context management runs (assuming this is near line 96 in the original script)
if __name__ == "__main__":
    try:
        harness = ExecutionHarnessEngine()
        print("Execution Harness successfully initialized.")
    except Exception as e:
        print(f"An error occurred during setup: {e}")

# Note: The code assumes the necessary supporting definitions (AgentContext, etc.) 
# exist elsewhere in the original script and were not included for brevity.