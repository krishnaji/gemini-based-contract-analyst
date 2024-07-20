![](frontend/contract-analyst.jpg)  
# Contract Analyst
![](agent-response.jpg)
## Configuration 
```bash
 pip install -r frontend/requirements.txt
 pip install -r backend/requirements.txt
 export BUCKET_NAME=<yourbucketname>
 export PROJECT_ID=<yourprojectname>
```

## Run Frontend Gradio Application
```bash
cd frontent
gradio app.py
```
## Run Backend Application
Change model name of your choice in backend/gemini.py
```python 
MODEL_ID = "gemini-1.5-pro" 
```
Run the backend application
```bash
cd backend
python app.py
```








