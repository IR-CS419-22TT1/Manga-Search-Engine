import streamlit as st
import os

# Check for API key
if "gemini_api_key" in st.session_state and st.session_state.gemini_api_key:
    st.sidebar.success("✅ API Key is entered!")
else:
    st.sidebar.error("⚠️ No API key detected! Please set it on the main page.")

# Page content
col1, col2 = st.columns([1, 3])  # Adjust column width ratios as needed
# Add the image in the first column
with col1:
    st.image('./assets/app_logo.png', width=200)
# Divide col2 into three rows
with col2:
    row1, row2, row3 = st.columns(1), st.columns(1), st.columns(1)
    with row1[0]:
        st.empty()  # Leave the first row empty
    with row2[0]:
        st.empty()  # Leave the third row empty
    with row3[0]:
        st.title("💬 Dialogue Search")  # Add the title to the second row

st.info("Type a **dialogue** you want to search or pick one of these suggestions:")

# Suggestions for quick search
suggestions = [
    "He's going to punch right through the island!!!",
    "I was just curious about my old house. That's all.",
    "We won't let something like that happen again!",
]

# Layout: Suggestion boxes
cols = st.columns(len(suggestions))  # Creates dynamic columns for each suggestion
st.session_state.chosen_suggestion = ""

# Handle clicks on suggestions
for idx, suggestion in enumerate(suggestions):
    with cols[idx]:
        if st.button(suggestion):
            st.session_state.chosen_suggestion = suggestion

# Search bar
query = st.text_input(
    label="Dialogue:", value=st.session_state.chosen_suggestion
)

if st.button("Search") or st.session_state.chosen_suggestion:
    if query:
        ocr_results = st.session_state.search_engine.search(query, top_k=10)
        print('Streamlit get: ',ocr_results)
        st.subheader("Top 10 OCR Search Results")
        columns_per_row = 3
        for row_start in range(0, len(ocr_results), columns_per_row):
            cols = st.columns(columns_per_row)
            for col, ocr_result in zip(cols, ocr_results[row_start:row_start + columns_per_row]):
                ocr_id = ocr_result['postId']
                # Convert OCR ID to image path
                image_path = ocr_id.replace("ocr_result", "dataset")
                image_path = image_path + ".png"
                image_path = "./" + image_path
                with col:
                    st.image(image_path, caption=f"{os.path.basename(image_path)}")
    else:
        st.warning("Please enter a query to search.")