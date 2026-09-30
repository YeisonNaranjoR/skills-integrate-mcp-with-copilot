# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities as a teacher
- View participant rosters without signing in
- Manage registrations through teacher-only controls

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Configure the teacher account and session signing key in the environment. Keep these values out of version control:

   ```
   export TEACHER_USERNAME="teacher"
   export TEACHER_PASSWORD="replace-with-a-strong-password"
   export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   export COOKIE_SECURE=false
   ```

   Use `COOKIE_SECURE=true` when serving the application over HTTPS. Keep the same `SESSION_SECRET` across server restarts.

3. From the `src` directory, run the application:

   ```
   uvicorn app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| GET    | `/auth/session`                                                   | Check whether the current browser is signed in as a teacher         |
| POST   | `/auth/login`                                                     | Sign in using the configured teacher credentials                   |
| POST   | `/auth/logout`                                                    | Sign out the current browser                                        |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | (Teacher only) Sign up a student                                    |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | (Teacher only) Remove a student from an activity                   |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
