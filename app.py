import streamlit as st
import ollama
import re

# Page setup
st.set_page_config(page_title="Municipal Grievance Assistant", layout="centered")
st.title("Municipal Grievance Assistant")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "name": None,
        "gender": None,
        "pin": None,
        "disability": None,
        "grievance": None
    }
if "data_stage" not in st.session_state:
    st.session_state.data_stage = "name"
if "confirmed" not in st.session_state:
    st.session_state.confirmed = False
if "editing_field" not in st.session_state:
    st.session_state.editing_field = None

# Sidebar
with st.sidebar:
    st.markdown("## Municipal Grievance Assistant")
    name = st.session_state.user_data["name"]
    st.markdown(f"Welcome, {name if name else 'USER'} 👋")
    st.markdown("Let us know about Your Grievance.")
    st.markdown("---")
    st.markdown("🛠 Features")
    st.markdown("- Smart validation via model")
    st.markdown("- Chat-driven onboarding")
    st.markdown("- Grievance classification")
    st.markdown("---")
    st.markdown("Made using Streamlit + Ollama")

# Reset button
if st.button(" Reset Chat"):
    st.session_state.messages = []
    st.session_state.user_data = {
        "name": None,
        "gender": None,
        "pin": None,
        "disability": None,
        "grievance": None
    }
    st.session_state.data_stage = "name"
    st.session_state.confirmed = False
    st.session_state.editing_field = None
    st.rerun()

# Initial assistant message
if not st.session_state.messages and not st.session_state.confirmed:
    greeting = "Hello there! Greetings from The Municipal Grievance Assistant — How can I help you today?\nBefore that, what should I call you?"
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.session_state.data_stage = "name"

# Display chat history
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Type your response...📟")
if user_input:
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant", avatar="🤖"):
        placeholder = st.empty()

        # Edit flow
        if user_input.lower().strip() == "edit":
            st.session_state.editing_field = "awaiting_field"
            prompt = " Which field would you like to update? (name, gender, pin, disability, grievance)"
            st.session_state.messages.append({"role": "assistant", "content": prompt})
            placeholder.markdown(prompt)
            st.stop()

        if st.session_state.editing_field == "awaiting_field":
            field = user_input.lower().strip()
            if field in st.session_state.user_data:
                st.session_state.editing_field = field
                prompt = f" What should I update **{field}** to?"
                st.session_state.messages.append({"role": "assistant", "content": prompt})
                placeholder.markdown(prompt)
            else:
                valid_fields = ", ".join([f"`{f}`" for f in st.session_state.user_data])
                error = f" I couldn't find that field. Try one of: {valid_fields}"
                st.session_state.messages.append({"role": "assistant", "content": error})
                placeholder.markdown(error)
            st.stop()

        if st.session_state.editing_field and st.session_state.editing_field != "awaiting_field":
            field = st.session_state.editing_field
            st.session_state.user_data[field] = user_input
            st.session_state.editing_field = None
            summary = "\n".join([f"- **{k.capitalize()}**: {v}" for k, v in st.session_state.user_data.items()])
            response = f"Updated **{field}** to: {user_input}\n\nHere's your info:\n\n{summary}\n\nType `edit` to change another field, or `confirm` to continue."
            st.session_state.messages.append({"role": "assistant", "content": response})
            placeholder.markdown(response)
            st.stop()

        # Validation fallback
        stage = st.session_state.data_stage
        def quick_validate(stage, value):
            if stage == "gender":
                return value.lower().strip() in ["male", "female"]
            if stage == "pin":
                return re.match(r"^\d{6}$", value.replace(" ", ""))
            return True

        if not st.session_state.confirmed and stage in ["gender", "pin"]:
            if not quick_validate(stage, user_input):
                error = f" That doesn't look like a valid {stage}. Please check and try again."
                st.session_state.messages.append({"role": "assistant", "content": error})
                placeholder.markdown(error)
                st.stop()

        # Onboarding flow
        if not st.session_state.confirmed:
            if stage != "done":
                st.session_state.user_data[stage] = user_input
                next_fields = {
                    "name": "gender",
                    "gender": "pin",
                    "pin": "disability",
                    "disability": "grievance",
                    "grievance": "done"
                }
                st.session_state.data_stage = next_fields[stage]
                if st.session_state.data_stage != "done":
                    question = {
                        "name": " Hi! What should I call you?",
                        "gender": " What's your gender?",
                        "pin": " What's your postal PIN code?",
                        "disability": " Do you have any disability? (Yes/No)",
                        "grievance": " Any grievance you'd like to share?"
                    }[st.session_state.data_stage]
                    st.session_state.messages.append({"role": "assistant", "content": question})
                    placeholder.markdown(question)
                else:
                    summary = "\n".join([f"- **{k.capitalize()}**: {v}" for k, v in st.session_state.user_data.items()])
                    response = f" Here's your info:\n\n{summary}\n\n Type `edit` to change anything, or `confirm` to continue."
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    placeholder.markdown(response)
                st.stop()

        # Confirmation + classification
        if user_input.lower().strip() == "confirm":
            st.session_state.confirmed = True

            grievance_prompt = f"""
You are a grievance classifier. Based on the user's message, assign it to one of these departments:
- Allotment
- Engineering
- Land
- Legal
- Finance
- Enforcement
- Establishment
- Planning
- Horticulture

User's grievance: "{st.session_state.user_data['grievance']}"
Respond with only the department name.
"""
            classification_response = ollama.chat(
                model="phi3:mini",
                messages=[{"role": "system", "content": grievance_prompt}]
            )
            department = classification_response["message"]["content"].strip()

            routing_map = {
                "Allotment": "Plot/Flat Allotment Dept",
                "Engineering": "Planning Dept",
                "Land": "Land Plotting Dept",
                "Legal": "Legal Affairs Cell",
                "Finance": "Refund & Finance Dept",
                "Enforcement": "Construction Enforcement Wing",
                "Establishment": "Letter & Dairy Section",
                "Planning": "Plan Approval Authority",
                "Horticulture": "Greenery & Parks Division"
            }
            routed_to = routing_map.get(department, "General Grievance Cell")

            response = f"""
                            You've confirmed your information. Thank You!

                             Grievance classified under: **{department}**  
                             Routed to: **{routed_to}**
                            
                        You can now:
                            - Type `edit` to update any info
                            - Type a new grievance to log another issue
                            """
            st.session_state.messages.append({"role": "assistant", "content": response})
            placeholder.markdown(response)
            st.stop()
