# Form & Function

A Flask fitness-coach prototype that creates weekly workout plans from a person's goal, experience, schedule, and available equipment.

Live website: https://form-and-function-764.vercel.app/

Repository: https://github.com/y79mgjphy2-afk/form-and-function

## Run locally

Install Python 3.11 or newer and the Microsoft Python / Python Debugger VS Code extensions. In PowerShell, run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open http://127.0.0.1:5000. Demo mode works without an API key.

## Live AI

For personalized plans, configure `OPENAI_API_KEY` as a server environment variable and restart the app. `OPENAI_MODEL` defaults to `gpt-4.1-mini`; change it to a model your account can access. Never put API keys in browser code or commit them. `.env.example` documents variables but is not loaded automatically.

Live mode sends the selected goal, experience level, days per week, equipment, and optional notes to the model provider. Do not enter sensitive personal or medical details. Provider calls require network access and have not been tested with a real API key.

## Safety and limitations

This is a classroom prototype, not a medical device or a substitute for a qualified trainer or health professional. Workout suggestions are general information and may not suit every person. Consult a qualified health professional before starting if you have an injury, medical condition, or concerns about exercise. Stop if you feel sharp pain, dizziness, or unusual shortness of breath.

The app does not save workout plans to a database. You can download a plan as JSON or print it from the browser; workout completion marks are temporary and reset when a new plan is generated or the page is refreshed. Browser sessions use CSRF protection and HTTP-only, SameSite cookies; live requests are sent to the configured model provider. Use demo mode for anonymous public access. Before enabling a paid live endpoint publicly, add authentication and global usage controls.

## Vercel deployment

Import this GitHub repository at https://vercel.com/new . Vercel detects Flask from requirements.txt and app.py. The build command in vercel.json copies CSS and JavaScript into public/static for Vercel's CDN. The page is rendered from templates/index.html. No Node build is required.

Set SESSION_SECRET to a stable random value in Vercel's environment variables before deploying, so signed sessions work across function instances. Keep live mode disabled for the public class demo by leaving OPENAI_API_KEY unset. If enabling live mode later, add authentication and global cost controls first. The model key must remain a server-side environment variable.

## Render deployment (alternative)

`render.yaml` defines a Render Python service using Waitress. Push this folder to your GitHub repository, then create a Render Blueprint from the repository. Configure `SESSION_SECRET` and, optionally, `OPENAI_API_KEY` in the Render dashboard.

## Course report

`report.tex` is the LaTeX project report and `report.pdf` is its compiled version. The GitHub and public Vercel website links are included. The public demo was checked for plan generation and workout progress tracking.

## Tests

Run `python -m unittest discover -s tests -v` with dependencies installed.
