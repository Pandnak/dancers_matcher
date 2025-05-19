# Dance matcher 

This service provides dancers to search for pair. This service is created on Python language using the FastAPI framework.

For using on your device you can run this command:

```
git clone https://github.com/Pandnak/dancers_matcher.git
cd dancers_matcher
```

After that you should create virtual env by:
```
python3 -m venv .venv
source .venv/bin/activate
```

Install all required libraries:
```
pip install -r requirements.txt
```

Change dirrectory:
```
cd app
```

And run this command:
```
uvicorn main:app --reload
```
