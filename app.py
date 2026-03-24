import os
import re
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()

# Support alternate env names sometimes used in starter templates.
if not os.getenv("GEMINI_API_KEY") and os.getenv("GOOGLE_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
if not os.getenv("OPENAI_API_KEY") and os.getenv("API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["API_KEY"]

SYSTEM_PROMPT = (
    "You are ShopSmart Assistant, a friendly customer service and sales chatbot for an online electronics store. "
    "Help customers with order status, refund questions, and product suggestions. "
    "Use conversation history so the customer does not need to repeat themselves. "
    "Be concise, accurate, and practical."
)

ORDER_DB = {
    "1001": {
        "status": "Shipped",
        "eta": "Arriving in 2 business days",
        "item": "Noise-Canceling Headphones",
    },
    "1002": {
        "status": "Processing",
        "eta": "Expected to ship tomorrow",
        "item": "Smart Fitness Watch",
    },
    "1003": {
        "status": "Delivered",
        "eta": "Delivered yesterday",
        "item": "4K Action Camera",
    },
}

REFUND_POLICY = {
    "window": "30 days from delivery",
    "condition": "Items must be in good condition and include the original packaging",
    "exceptions": "Final-sale items and gift cards are non-refundable",
    "process": "Start a return request, receive a return label after approval, and refunds are processed within 5-7 business days after inspection",
}

PRODUCT_CATALOG = [
    {
        "name": "Student Laptop 14",
        "category": "laptop",
        "price": 649,
        "best_for": ["school", "college", "laptop", "battery", "study", "productivity"],
        "battery": "up to 12 hours",
        "summary": "Lightweight laptop for schoolwork, web browsing, and documents.",
    },
    {
        "name": "Noise-Canceling Headphones",
        "category": "audio",
        "price": 199,
        "best_for": ["travel", "study", "focus", "music", "calls", "battery"],
        "battery": "up to 30 hours",
        "summary": "Excellent for travel and studying with strong noise cancellation.",
    },
    {
        "name": "Portable Bluetooth Speaker",
        "category": "audio",
        "price": 89,
        "best_for": ["travel", "budget", "music", "battery"],
        "battery": "up to 15 hours",
        "summary": "Budget-friendly speaker with solid battery life.",
    },
    {
        "name": "Smart Fitness Watch",
        "category": "wearables",
        "price": 149,
        "best_for": ["fitness", "running", "health", "budget"],
        "battery": "up to 7 days",
        "summary": "Tracks workouts, heart rate, and sleep.",
    },
    {
        "name": "4K Action Camera",
        "category": "camera",
        "price": 249,
        "best_for": ["travel", "sports", "vlogging", "outdoors"],
        "battery": "up to 2 hours",
        "summary": "Compact camera for trips and outdoor adventures.",
    },
]


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    inquiry_type: str


class MockLLM:
    def invoke(self, messages: list[BaseMessage]):
        return AIMessage(content="I can help with order tracking, refunds, or product suggestions.")


def build_llm():
    provider = os.getenv("MODEL_PROVIDER", "google").strip().lower()

    if provider == "google":
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
                return ChatGoogleGenerativeAI(model=model_name, temperature=0.2)
            except Exception:
                pass
        return MockLLM()

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from langchain_openai import ChatOpenAI

            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            return ChatOpenAI(model=model_name, temperature=0.2)
        except Exception:
            pass
    return MockLLM()


llm = build_llm()


def detect_inquiry_type(text: str) -> Literal["order_status", "refund_policy", "product_suggestion", "general"]:
    lower = text.lower()
    if any(word in lower for word in ["order", "track", "shipping", "shipment", "delivered", "eta"]):
        return "order_status"
    if any(word in lower for word in ["refund", "return", "exchange", "money back", "policy"]):
        return "refund_policy"
    if any(
        phrase in lower
        for phrase in [
            "recommend",
            "suggest",
            "looking for",
            "which product",
            "best for",
            "need a",
            "need an",
            "budget",
            "battery life",
        ]
    ):
        return "product_suggestion"
    return "general"


# ----------------------------
# Helpers for deterministic logic
# ----------------------------

def extract_order_id(text: str) -> str | None:
    match = re.search(r"\b(\d{4,})\b", text)
    if match:
        return match.group(1)
    return None


def parse_budget(text: str) -> int | None:
    match = re.search(r"(?:under|below|less than)\s*\$?(\d+)", text.lower())
    if match:
        return int(match.group(1))
    match = re.search(r"\$\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return None


def collect_preferences(messages: list[BaseMessage]) -> dict:
    joined_user_text = " ".join(
        msg.content.lower()
        for msg in messages
        if isinstance(msg, HumanMessage) and isinstance(msg.content, str)
    )

    budget = None
    for msg in messages:
        if isinstance(msg, HumanMessage) and isinstance(msg.content, str):
            maybe_budget = parse_budget(msg.content)
            if maybe_budget is not None:
                budget = maybe_budget

    keywords = []
    for word in [
        "school",
        "college",
        "travel",
        "music",
        "study",
        "fitness",
        "running",
        "battery",
        "battery life",
        "laptop",
        "camera",
        "budget",
    ]:
        if word in joined_user_text:
            keywords.append(word)

    wants_good_battery = "battery life" in joined_user_text or "good battery" in joined_user_text or "battery" in joined_user_text
    wants_laptop = "laptop" in joined_user_text

    return {
        "budget": budget,
        "keywords": keywords,
        "wants_good_battery": wants_good_battery,
        "wants_laptop": wants_laptop,
    }


def score_product(product: dict, prefs: dict) -> int:
    score = 0
    budget = prefs["budget"]
    keywords = prefs["keywords"]

    if budget is not None:
        if product["price"] <= budget:
            score += 3
        else:
            score -= 5

    for kw in keywords:
        if kw in product["best_for"]:
            score += 2

    if prefs["wants_laptop"] and product["category"] == "laptop":
        score += 5
    if prefs["wants_good_battery"] and "battery" in product["best_for"]:
        score += 2

    return score


def build_order_response(order_id: str | None) -> str:
    if not order_id:
        return "Please share your order number, and I can check the status for you."
    if order_id not in ORDER_DB:
        return f"I could not find order {order_id} in the sample store data. Please verify the order number."

    order = ORDER_DB[order_id]
    return (
        f"Order {order_id} is for **{order['item']}**. "
        f"Current status: **{order['status']}**. "
        f"Latest update: **{order['eta']}**."
    )


def build_refund_response() -> str:
    return (
        "Our refund policy is:\n"
        f"- **Refund window:** {REFUND_POLICY['window']}\n"
        f"- **Condition:** {REFUND_POLICY['condition']}\n"
        f"- **Exceptions:** {REFUND_POLICY['exceptions']}\n"
        f"- **Process:** {REFUND_POLICY['process']}"
    )


def build_product_response(messages: list[BaseMessage]) -> str:
    prefs = collect_preferences(messages)
    ranked = sorted(PRODUCT_CATALOG, key=lambda item: score_product(item, prefs), reverse=True)

    budget = prefs["budget"]
    filtered = [item for item in ranked if budget is None or item["price"] <= budget]
    choices = filtered[:2] if filtered else ranked[:2]

    intro_bits = []
    if "school" in prefs["keywords"] or "college" in prefs["keywords"]:
        intro_bits.append("school use")
    if "travel" in prefs["keywords"]:
        intro_bits.append("travel")
    if budget is not None:
        intro_bits.append(f"a budget under ${budget}")
    if prefs["wants_good_battery"]:
        intro_bits.append("good battery life")

    intro = "Based on your needs"
    if intro_bits:
        intro += " for " + ", ".join(intro_bits)
    intro += ", I recommend:\n"

    lines = [intro]
    for item in choices:
        lines.append(
            f"- **{item['name']} (${item['price']})**: {item['summary']} Battery life: **{item['battery']}**."
        )

    if budget is not None and all(item["price"] > budget for item in PRODUCT_CATALOG):
        lines.append(f"I do not have any products under ${budget} in the sample catalog.")

    lines.append("If you want, I can also recommend the single best option instead of two choices.")
    return "\n".join(lines)


def maybe_general_llm_reply(state: ChatState) -> str:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(
            content=(
                "You are the General Support Agent. Keep the reply short. "
                "If the customer needs order tracking, refunds, or recommendations, guide them to ask that directly."
            )
        ),
        *state["messages"],
    ]
    try:
        response = llm.invoke(messages)
        if hasattr(response, "content") and isinstance(response.content, str) and response.content.strip():
            return response.content.strip()
    except Exception:
        pass
    return "Hi. I can help with order status, refund policy, or product recommendations."


# ----------------------------
# LangGraph nodes
# ----------------------------

def router_node(state: ChatState) -> dict:
    user_text = state["messages"][-1].content
    return {"inquiry_type": detect_inquiry_type(user_text)}


def order_status_agent(state: ChatState) -> dict:
    order_id = extract_order_id(state["messages"][-1].content)
    return {"messages": [AIMessage(content=build_order_response(order_id))]}


def refund_policy_agent(state: ChatState) -> dict:
    return {"messages": [AIMessage(content=build_refund_response())]}


def product_suggestion_agent(state: ChatState) -> dict:
    return {"messages": [AIMessage(content=build_product_response(state["messages"]))]}


def general_agent(state: ChatState) -> dict:
    return {"messages": [AIMessage(content=maybe_general_llm_reply(state))]}


def pick_next_node(state: ChatState) -> str:
    route = state.get("inquiry_type", "general")
    if route == "order_status":
        return "order_status_agent"
    if route == "refund_policy":
        return "refund_policy_agent"
    if route == "product_suggestion":
        return "product_suggestion_agent"
    return "general_agent"


builder = StateGraph(ChatState)
builder.add_node("router", router_node)
builder.add_node("order_status_agent", order_status_agent)
builder.add_node("refund_policy_agent", refund_policy_agent)
builder.add_node("product_suggestion_agent", product_suggestion_agent)
builder.add_node("general_agent", general_agent)

builder.add_edge(START, "router")
builder.add_conditional_edges(
    "router",
    pick_next_node,
    {
        "order_status_agent": "order_status_agent",
        "refund_policy_agent": "refund_policy_agent",
        "product_suggestion_agent": "product_suggestion_agent",
        "general_agent": "general_agent",
    },
)
builder.add_edge("order_status_agent", END)
builder.add_edge("refund_policy_agent", END)
builder.add_edge("product_suggestion_agent", END)
builder.add_edge("general_agent", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


def chat() -> None:
    print("ShopSmart Assistant")
    print("Type 'quit' to exit.\n")

    config = {"configurable": {"thread_id": "demo-thread-1"}}

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            print("Assistant: Thanks for visiting ShopSmart. Goodbye!")
            break

        result = graph.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
        print(f"Assistant: {result['messages'][-1].content}\n")


if __name__ == "__main__":
    chat()
