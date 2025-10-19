@echo off
echo Activating conda environment...
call conda activate vise3_py312

echo Starting Streamlit app...
streamlit run streamlit_app.py

pause
