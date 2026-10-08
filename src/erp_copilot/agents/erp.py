from erp_copilot.agents.base import Agent

# Placeholder answering agent; the orchestrator will later route to specialists instead.
erp_agent = Agent(
    name="erp",
    system_prompt=(
        "You are ERP Copilot, an assistant for sales orders, purchase orders and work orders. "
        "Answer concisely and only about those topics."
    ),
)



