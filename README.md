# 🧠 Quiz app

A Streamlit quiz app that loads questions from a JSON file, lets users enter their name, pick chapters, choose how many questions to answer, and complete a randomized quiz with optional skipping and answer explanations.

### How to run it on your own machine

Prerequisite: install `uv` if you don't already have it.

```
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. Sync the dependencies

   ```
   $ uv sync
   ```

2. Run the app

   ```
   $ uv run streamlit run streamlit_app.py
   ```

The app reads questions from [questions.json](questions.json) and chapter metadata from [chapters.json](chapters.json).

### Publish it publicly

This app is ready to publish on Streamlit Community Cloud:

1. Push the repository to GitHub.
2. Open Streamlit Community Cloud and click New app.
3. Choose this repository and set the main file to [streamlit_app.py](streamlit_app.py).
4. Deploy.

If you want, I can also help you set up a GitHub repository and the exact deployment steps for your account.
