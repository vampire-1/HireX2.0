# HireX Backend - Render Deployment Guide

## ✅ Pre-Deployment Checklist

### 1. **Dependencies Fixed**
- ✅ Removed duplicate `pydantic-settings` entries (was causing installation conflicts)
- ✅ Added `passlib[bcrypt]==1.7.4` for secure password hashing
- ✅ Added `python-jose[cryptography]==3.3.0` for JWT token handling
- ✅ All Python files compile successfully without syntax errors

### 2. **Docker Configuration**
- ✅ Dockerfile includes all system dependencies (gcc, g++, make, libffi-dev, libssl-dev)
- ✅ System dependencies for cryptography compilation (bcrypt, jose)
- ✅ OCR dependencies (tesseract-ocr, poppler-utils)
- ✅ Creates data directories for SQLite and file uploads
- ✅ PORT environment variable properly configured

### 3. **Environment Variables**
- ✅ `.env.example` template created for reference
- ✅ All required environment variables documented
- 📋 **You need to configure these on Render:**
  - `SECRET_KEY` - Generate a strong random string
  - `JWT_SECRET` - Generate a strong random string (or will use SECRET_KEY)
  - `FRONTEND_ORIGINS` - Your frontend URL (e.g., https://yourapp.vercel.app)
  - `SMTP_*` - Email configuration (optional, set SMTP_ENABLED=false to skip)

### 4. **Render Configuration**
- ✅ `render.yaml` created for automated deployment
- ✅ Health check endpoint configured (`/health`)
- ✅ Docker build context properly set

## 🚀 Deployment Steps on Render

### Option A: Using render.yaml (Recommended)

1. **Connect Your Repository**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Blueprint"
   - Connect your GitHub/GitLab repository
   - Render will automatically detect `render.yaml`

2. **Configure Environment Variables**
   - In the Render dashboard, go to your service settings
   - Add the following environment variables:
     ```
     SECRET_KEY=<generate-strong-random-string>
     FRONTEND_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
     SMTP_ENABLED=false
     ```
   - Optional: Configure SMTP if you want email verification

3. **Update Frontend URL**
   - Edit `render.yaml` line 16 to add your actual frontend URL
   - Or set it directly in Render dashboard under Environment Variables

4. **Deploy**
   - Render will automatically build and deploy
   - Monitor the build logs for any errors

### Option B: Manual Deployment

1. **Create New Web Service**
   - Go to Render Dashboard
   - Click "New" → "Web Service"
   - Connect your repository
   - Select the `hirex-backend` directory

2. **Configure Service**
   - **Name:** hirex-backend
   - **Region:** Choose closest to your users
   - **Branch:** main (or your default branch)
   - **Environment:** Docker
   - **Dockerfile Path:** ./Dockerfile
   - **Docker Context:** .
   - **Plan:** Free or paid

3. **Add Environment Variables** (same as Option A, step 2)

4. **Advanced Settings**
   - Health Check Path: `/health`
   - Auto-Deploy: Yes

## 🔍 Post-Deployment Verification

### 1. Check Health Endpoint
```bash
curl https://your-app.onrender.com/health
# Should return: {"status":"ok"}
```

### 2. Test API Documentation
Visit: `https://your-app.onrender.com/docs`
- You should see the FastAPI interactive documentation

### 3. Test Authentication Endpoints
```bash
# Register a new user
curl -X POST https://your-app.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}'

# Should return a transaction_id
```

### 4. Monitor Logs
- Check Render dashboard logs for any startup errors
- Look for:
  - ✅ "Application startup complete"
  - ✅ "Uvicorn running on 0.0.0.0:8000"
  - ❌ Any import errors or missing dependencies

## ⚠️ Common Issues & Solutions

### Issue: Build fails with "Could not build wheels for cryptography"
**Solution:** Already fixed! Dockerfile includes `libffi-dev` and `libssl-dev`

### Issue: Import errors for passlib or jose
**Solution:** Already fixed! Added to requirements.txt

### Issue: Database/FAISS index not persisting
**Solution:** 
- Free tier on Render uses ephemeral storage
- For production, consider:
  - Upgrading to a paid plan with persistent disk
  - Using external database (PostgreSQL)
  - Using external storage for FAISS index (S3, etc.)

### Issue: CORS errors from frontend
**Solution:** Update `FRONTEND_ORIGINS` environment variable with your actual frontend URL

### Issue: Email OTP not sending
**Solution:** 
- Set `SMTP_ENABLED=false` to disable email temporarily
- Configure proper SMTP credentials if needed
- Use app-specific passwords for Gmail

## 📊 Performance Notes

### Free Tier Limitations
- Service spins down after 15 minutes of inactivity
- First request after spin-down will be slow (30-60s)
- 512MB RAM limit
- SQLite database is ephemeral (resets on restart)

### Optimization Tips
1. **Keep Service Warm:** Use a cron job to ping `/health` every 14 minutes
2. **Upgrade Plan:** Consider Starter plan ($7/mo) for always-on service
3. **External Database:** Use Render PostgreSQL for persistent data
4. **Caching:** Implement Redis for session/token caching

## 🔐 Security Checklist

- ✅ Strong `SECRET_KEY` configured
- ✅ CORS origins restricted to your frontend only
- ✅ Password hashing with bcrypt
- ✅ Environment variables not committed to git
- 📋 TODO: Add rate limiting for API endpoints
- 📋 TODO: Add request logging/monitoring
- 📋 TODO: Configure HTTPS (Render provides this automatically)

## 📝 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | Auto | 8000 | Port to run the server (set by Render) |
| `SECRET_KEY` | **Yes** | - | Secret for JWT/session signing |
| `JWT_SECRET` | No | Uses SECRET_KEY | JWT token secret |
| `FRONTEND_ORIGINS` | **Yes** | localhost:3000 | Comma-separated CORS origins |
| `SMTP_ENABLED` | No | false | Enable email OTP |
| `SMTP_HOST` | No | localhost | SMTP server hostname |
| `SMTP_PORT` | No | 587 | SMTP server port |
| `SMTP_USER` | No | - | SMTP username |
| `SMTP_PASS` | No | - | SMTP password |
| `SMTP_FROM` | No | HireX <no-reply@hirex.local> | From email address |

## 🎯 Next Steps After Deployment

1. **Update Frontend:** Configure frontend to use your Render backend URL
2. **Test Full Flow:** Register → Login → Upload Resume → Search
3. **Monitor Performance:** Check Render metrics dashboard
4. **Set Up Alerts:** Configure Render notifications for downtime
5. **Plan Database Migration:** Move from SQLite to PostgreSQL for production

---

**Your backend is ready to deploy! 🚀**

For issues or questions, check:
- [Render Documentation](https://render.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- Application logs in Render dashboard
