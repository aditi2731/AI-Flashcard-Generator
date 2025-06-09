import streamlit as st
import openai
import json
import os
import random

# Set page configuration
st.set_page_config(page_title="Flashcard Generator", page_icon="🧠")

# App title
st.title("AI Flashcard Generator 🧠")

# API Key input in sidebar
with st.sidebar:
    st.header("API Configuration")
    api_key = st.text_input("Enter your OpenAI API Key:", type="password", 
                           help="Your API key will not be stored permanently")
    
    if not api_key:
        st.warning("⚠️ Please enter an OpenAI API key to continue")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This app generates flashcards based on any topic you provide.")
    st.markdown("### How to use")
    st.markdown("1. Enter a topic or subject area")
    st.markdown("2. Specify how many flashcards you want")
    st.markdown("3. View, study, and save your flashcards")

# Initialize session state variables
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "current_card" not in st.session_state:
    st.session_state.current_card = 0
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

# Function to generate flashcards
def generate_flashcards(topic, num_cards):
    if not api_key:
        return "Please enter an OpenAI API key in the sidebar to continue."
    
    try:
        client = openai.OpenAI(api_key=api_key)
        prompt = f"""Create {num_cards} flashcards on the topic of "{topic}".
        Each flashcard should have a question and an answer.
        Return the data as a JSON array of objects, each with 'question' and 'answer' fields.
        Keep questions concise but clear, and answers detailed but not too long.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Extract and parse JSON from response
        content = response.choices[0].message.content
        flashcards_data = json.loads(content)
        
        # Make sure we have a list of flashcards
        if "flashcards" in flashcards_data:
            return flashcards_data["flashcards"]
        else:
            # If the model didn't return in expected format, try to find any array
            for key, value in flashcards_data.items():
                if isinstance(value, list) and len(value) > 0:
                    return value
            # Fallback if we can't find a good array
            return []
            
    except Exception as e:
        st.error(f"Error generating flashcards: {str(e)}")
        return []

# Function to handle card navigation
def next_card():
    if st.session_state.flashcards:
        st.session_state.current_card = (st.session_state.current_card + 1) % len(st.session_state.flashcards)
        st.session_state.show_answer = False

def prev_card():
    if st.session_state.flashcards:
        st.session_state.current_card = (st.session_state.current_card - 1) % len(st.session_state.flashcards)
        st.session_state.show_answer = False

def toggle_answer():
    st.session_state.show_answer = not st.session_state.show_answer

def shuffle_cards():
    if st.session_state.flashcards:
        random.shuffle(st.session_state.flashcards)
        st.session_state.current_card = 0
        st.session_state.show_answer = False

# Input form for flashcard generation
with st.form("flashcard_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Enter a topic for your flashcards:", placeholder="e.g., Python Programming Basics")
    with col2:
        num_cards = st.number_input("Number of cards:", min_value=1, max_value=20, value=5)
    
    submit_button = st.form_submit_button("Generate Flashcards")
    
    if submit_button and topic:
        with st.spinner("Generating flashcards..."):
            st.session_state.flashcards = generate_flashcards(topic, num_cards)
            st.session_state.current_card = 0
            st.session_state.show_answer = False

# Display flashcards
if st.session_state.flashcards:
    st.subheader(f"Flashcards on: {topic}")
    
    # Create a card-like container
    card = st.container()
    with card:
        current_flashcard = st.session_state.flashcards[st.session_state.current_card]
        
        # Display card number
        st.markdown(f"**Card {st.session_state.current_card + 1} of {len(st.session_state.flashcards)}**")
        
        # Question section with styling
        st.markdown("### Question:")
        st.markdown(f"**{current_flashcard['question']}**")
        
        # Answer section with reveal button
        st.markdown("### Answer:")
        if st.session_state.show_answer:
            st.markdown(current_flashcard['answer'])
        else:
            st.button("Reveal Answer", on_click=toggle_answer)
    
    # Navigation controls
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.button("Previous", on_click=prev_card)
    with col2:
        st.button("Shuffle", on_click=shuffle_cards)
    with col3:
        st.button("Next", on_click=next_card)
    
    # Export options
    st.markdown("---")
    export_format = st.selectbox("Export format:", ["JSON", "Text"])
    
    if export_format == "JSON":
        export_data = json.dumps(st.session_state.flashcards, indent=2)
        file_ext = "json"
    else:
        # Text format with one card per line
        export_lines = []
        for i, card in enumerate(st.session_state.flashcards):
            export_lines.append(f"Card {i+1}:")
            export_lines.append(f"Q: {card['question']}")
            export_lines.append(f"A: {card['answer']}")
            export_lines.append("")
        export_data = "\n".join(export_lines)
        file_ext = "txt"
    
    st.download_button(
        label="Download Flashcards",
        data=export_data,
        file_name=f"flashcards_{topic.replace(' ', '_')}.{file_ext}",
        mime="application/json" if export_format == "JSON" else "text/plain"
    )
