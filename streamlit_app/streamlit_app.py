"""
Streamlit app for viewing Learning Machine quizzes.
"""
import sys
from pathlib import Path
# Add parent directory to Python path to import constants
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import constants
import json
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import pandas as pd


def load_quiz_metadata(quiz_file: Path) -> Dict[str, Any]:
    """Extract metadata from quiz HTML file."""
    with open(quiz_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Extract title from the header
    header = soup.find('div', class_='header')
    title = "Unknown Quiz"
    source_file = "Unknown"
    
    if header:
        h1 = header.find('h1')
        if h1:
            title = h1.get_text().replace('Quiz: ', '')
        
        em = header.find('em')
        if em:
            source_file = em.get_text().replace('Generated from: ', '')
    
    # Count questions
    questions = soup.find_all('div', class_='question')
    num_questions = len(questions)
    
    # Extract question types and difficulties
    answer_items = soup.find_all('div', class_='answer-item')
    question_types = []
    difficulties = []
    
    for item in answer_items:
        h3 = item.find('h3')
        if h3:
            question_text = item.find('p', string=re.compile(r'Question:'))
            if question_text:
                # Try to determine question type from the question text
                q_text = question_text.get_text().replace('Question: ', '')
                if 'True or False' in q_text or 'True/False' in q_text:
                    question_types.append('True/False')
                elif 'Options:' in str(item):
                    question_types.append('Multiple Choice')
                else:
                    question_types.append('Short Answer')
        
        # Extract difficulty
        difficulty_p = item.find('p', string=re.compile(r'Difficulty:'))
        if difficulty_p:
            difficulty = difficulty_p.get_text().replace('Difficulty: ', '')
            difficulties.append(difficulty)
    
    return {
        'title': title,
        'source_file': source_file,
        'num_questions': num_questions,
        'question_types': question_types,
        'difficulties': difficulties,
        'file_path': quiz_file
    }


def load_quiz_content(quiz_file: Path) -> str:
    """Load the full HTML content of a quiz."""
    with open(quiz_file, 'r', encoding='utf-8') as f:
        return f.read()


def get_available_quizzes() -> List[Dict[str, Any]]:
    """Get list of available quizzes with metadata."""
    quiz_dir = constants.QUIZ_OUTPUT_DIR
    if not quiz_dir.exists():
        return []
    
    quizzes = []
    for quiz_file in quiz_dir.glob("*.html"):
        try:
            metadata = load_quiz_metadata(quiz_file)
            quizzes.append(metadata)
        except Exception as e:
            st.error(f"Error loading quiz {quiz_file.name}: {e}")
    
    return sorted(quizzes, key=lambda x: x['title'])


def display_quiz_summary(quiz_metadata: Dict[str, Any]):
    """Display a summary card for a quiz."""
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.subheader(quiz_metadata['title'])
        st.caption(f"Source: {quiz_metadata['source_file']}")
    
    with col2:
        st.metric("Questions", quiz_metadata['num_questions'])
    
    with col3:
        if quiz_metadata['difficulties']:
            difficulty_counts = pd.Series(quiz_metadata['difficulties']).value_counts()
            most_common = difficulty_counts.index[0] if len(difficulty_counts) > 0 else "Unknown"
            st.metric("Difficulty", most_common)
        else:
            st.metric("Difficulty", "Unknown")


def main():
    st.set_page_config(
        page_title="Learning Machine Quiz Viewer",
        page_icon="🧠",
        layout="wide"
    )
    
    st.title("🧠 Learning Machine Quiz Viewer")
    st.markdown("View and explore your generated quizzes")
    
    # Load available quizzes
    quizzes = get_available_quizzes()
    
    if not quizzes:
        st.warning("No quizzes found. Generate some quizzes first!")
        return
    
    st.sidebar.header("Quiz Navigation")
    
    # Quiz selection
    quiz_titles = [quiz['title'] for quiz in quizzes]
    selected_title = st.sidebar.selectbox(
        "Select a quiz to view:",
        quiz_titles,
        index=0
    )
    
    # Find selected quiz
    selected_quiz = next(quiz for quiz in quizzes if quiz['title'] == selected_title)
    
    # Display quiz summary
    st.header("Quiz Overview")
    display_quiz_summary(selected_quiz)
    
    # Display quiz content
    st.header("Quiz Content")
    
    # Load and display the quiz HTML
    quiz_content = load_quiz_content(selected_quiz['file_path'])
    
    # Use st.components.v1.html to render the HTML
    st.components.v1.html(quiz_content, height=800, scrolling=True)
    
    # Additional information
    st.header("Quiz Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Questions", selected_quiz['num_questions'])
    
    with col2:
        if selected_quiz['question_types']:
            type_counts = pd.Series(selected_quiz['question_types']).value_counts()
            st.write("**Question Types:**")
            for q_type, count in type_counts.items():
                st.write(f"• {q_type}: {count}")
        else:
            st.write("**Question Types:** Not available")
    
    with col3:
        if selected_quiz['difficulties']:
            difficulty_counts = pd.Series(selected_quiz['difficulties']).value_counts()
            st.write("**Difficulty Distribution:**")
            for difficulty, count in difficulty_counts.items():
                st.write(f"• {difficulty}: {count}")
        else:
            st.write("**Difficulty Distribution:** Not available")
    
    # Download option
    st.header("Download")
    with open(selected_quiz['file_path'], 'r', encoding='utf-8') as f:
        quiz_html = f.read()
    
    st.download_button(
        label="Download Quiz HTML",
        data=quiz_html,
        file_name=f"{selected_quiz['title']}.html",
        mime="text/html"
    )


if __name__ == "__main__":
    main()
