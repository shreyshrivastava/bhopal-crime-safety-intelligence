# 🚀 Streamlit Deployment Guide

This guide walks you through deploying the **Bhopal Crime & Safety Intelligence Dashboard** to **Streamlit Community Cloud** (recommended, free, and instant) or self-hosting via **Docker**.

---

## ⚡ Option 1: Streamlit Community Cloud (1-Click Deployment)

You can deploy directly to Streamlit Community Cloud using your GitHub repository:

### Direct Deploy Link:
👉 **[Click Here to Deploy on Streamlit Community Cloud](https://share.streamlit.io/deploy?repository=shreyshrivastava/bhopal-crime-safety-intelligence&branch=main&mainModule=app.py)**

### Manual Steps:
1. Sign in to **[share.streamlit.io](https://share.streamlit.io)** using your GitHub account (`shreyshrivastava`).
2. Click **New app**.
3. Fill in the repository details:
   - **Repository:** `shreyshrivastava/bhopal-crime-safety-intelligence`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Under **Advanced settings**:
   - **Python version:** Select `3.11` or `3.12`.
5. Click **Deploy!**

Your dashboard will automatically build and become accessible at a public URL (e.g. `https://bhopal-crime-safety.streamlit.app`). Any future commits pushed to the `main` branch will automatically trigger a zero-downtime redeploy!

---

## 🐳 Option 2: Docker Container Deployment (Self-Hosted / Cloud Run / AWS / VPS)

### 1. Build the Docker Image
```bash
docker build -t bhopal-crime-dashboard .
```

### 2. Run the Container
```bash
docker run -d -p 8501:8501 --name bhopal-dashboard bhopal-crime-dashboard
```

Access the app at `http://localhost:8501`.

---

## ⚙️ Configuration Files Included in This Repo

- **`.streamlit/config.toml`**: Configures server settings (headless mode, custom port, security flags) and theme colors.
- **`requirements.txt`**: Specifies all required Python libraries with pinned versions.
- **`Dockerfile`**: Self-contained multi-stage container build for Linux production hosts.
