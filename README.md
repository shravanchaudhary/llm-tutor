For local deployment:

1. Create venv
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Create .env file with below secrets:
```
YOUTUBE_API_KEY=XXXXXXX
OPENAI_API_KEY=XXXXXXX
MONGO_URL=XXXXXXX
```

2. Run development server with command
```
uvicorn main:app --reload
```

Note: Please use gpt-3.5 turbo until you are testing the output of llm.
- To check the quality of output response use gpt-4
- To test your code, please use gpt-3
- Change it via settings.py