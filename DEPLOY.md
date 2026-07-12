# AssetFlow Deployment Guide

This guide provides step-by-step instructions for deploying the **AssetFlow** application using **Vercel** (for the Next.js frontend) and **Render** (for the FastAPI backend).

---

## 1. Database Setup (Recommended for Data Persistence)

Since Render's free tier has an ephemeral filesystem, any SQLite database (`assetflow.db`) will be deleted and reset every time the backend container restarts (which happens on every deployment or after 15 minutes of inactivity).

To ensure your data is persistent, use a **PostgreSQL** database:

1. **Get a Free PostgreSQL Instance:**
   - Sign up for a free PostgreSQL database on [Neon.tech](https://neon.tech/), [Supabase](https://supabase.com/), or create a PostgreSQL database directly on [Render](https://render.com/).
2. **Copy the Connection String:**
   - Copy your database connection URI. It should look like this:
     ```
     postgresql://<username>:<password>@<host>/<database>?sslmode=require
     ```
   - Keep this URL ready. You will set it as the `DATABASE_URL` environment variable on Render.
   - *Note: The backend is preconfigured to automatically create all tables on startup when connecting to the database.*

---

## 2. Backend Deployment (on Render)

1. Go to [Render](https://render.com/) and log in.
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.
4. Configure the Web Service settings:
   - **Name:** `assetflow-backend`
   - **Language/Environment:** `Python`
   - **Root Directory:** *Leave empty* (or set to `backend` if you want, but leaving it empty is safer for mono-repos).
   - **Build Command:** 
     ```bash
     pip install -r backend/requirements.txt
     ```
   - **Start Command:**
     ```bash
     cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
5. **Environment Variables:**
   Click **Advanced** and add the following Environment Variables:
   - `ENV_MODE`: `production` *(This enables secure, cross-site cookies for Vercel)*
   - `CORS_ORIGINS`: `https://your-frontend.vercel.app` *(Replace with your Vercel URL once generated, see below)*
   - `JWT_SECRET`: `your-random-jwt-secret` *(Use a secure random string)*
   - `DATABASE_URL`: `your-postgresql-connection-string` *(Add this for data persistence. If left empty, it will default to an ephemeral SQLite database)*
6. Click **Deploy Web Service**.
7. Once deployed, copy your service URL (e.g. `https://assetflow-backend.onrender.com`).

---

## 3. Frontend Deployment (on Vercel)

1. Go to [Vercel](https://vercel.com/) and log in.
2. Click **Add New...** and select **Project**.
3. Connect your GitHub repository.
4. Set the **Root Directory** to `frontend`.
5. Vercel will automatically detect Next.js and configure the build settings.
6. **Environment Variables:**
   Under **Environment Variables**, add:
   - `NEXT_PUBLIC_API_URL`: `https://assetflow-backend.onrender.com` *(Use the URL of your Render backend. Do NOT include a trailing slash)*
7. Click **Deploy**.
8. Vercel will build your static assets and publish your live app URL!

> [!IMPORTANT]
> **Link the Services (CORS):**
> Once your frontend is successfully deployed on Vercel, copy its URL (e.g. `https://assetflow-frontend.vercel.app`).
> Go back to your Render Dashboard -> **assetflow-backend** -> **Environment Variables**, and set `CORS_ORIGINS` to your frontend's Vercel URL. Redeploy the backend if needed to apply the settings.

---

## 4. Environment Variables Reference Sheet

Here are the environment variables configured in the codebase for production use:

| Variable | Location | Description | Example / Recommended Value |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | **Vercel** | Public URL of the FastAPI backend. Used by client and server-side components. | `https://assetflow-backend.onrender.com` |
| `ENV_MODE` | **Render** | Dictates cookie security. Set to `production` to activate Secure/SameSite cookies. | `production` |
| `CORS_ORIGINS` | **Render** | Comma-separated list of allowed frontend origins to permit cross-site requests. | `https://assetflow-frontend.vercel.app` |
| `JWT_SECRET` | **Render** | Secret key used to sign and verify user JWT sessions. | *Any secure random string* |
| `DATABASE_URL` | **Render** | Relational Database URI. Defaults to local SQLite if omitted. | `postgresql://user:pass@host/db?sslmode=require` |
| `SMTP_HOST` | **Render** | (Optional) Hostname of your SMTP server for sending emails. | `smtp.gmail.com` |
| `SMTP_PORT` | **Render** | (Optional) Port of SMTP server. | `587` |
| `SMTP_USER` | **Render** | (Optional) Username/email for email service auth. | `your-email@gmail.com` |
| `SMTP_PASSWORD`| **Render** | (Optional) App password / email credential. | `your-app-password` |
