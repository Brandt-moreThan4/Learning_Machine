@echo off
echo Activating conda environment...
call conda activate vise3_py312

echo Starting Streamlit app...
cd ..
streamlit run streamlit_app/streamlit_app.py

pause
