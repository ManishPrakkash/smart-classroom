# Smart Classroom - Quick Start Guide

## Running the Application

### Start Backend (Terminal 1)
```bash
cd backend
python app.py
```

### Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

### Access the UI
Open your browser: `http://localhost:3000`

## Features

- **Individual Device Control**: Toggle any light or fan
- **Group Controls**: Control all lights, all fans, or all devices at once
- **Mobile-Responsive**: Works perfectly on phones, tablets, and desktops
- **Modern Design**: Dark theme with glassmorphism and smooth animations

## Next Steps

1. Test the UI on mobile viewport (Chrome DevTools)
2. Try toggling devices and group controls
3. Configure for network access to test on actual mobile devices
4. Consider wrapping with Capacitor/React Native for native app

## Raspberry Pi Deployment

Deploying to Raspberry Pi 3, 4, or 5? See **[RASPI_SETUP.md](RASPI_SETUP.md)** for:
- Automatic hardware detection (Pi model, Camera Module)
- GPIO configuration (lgpio for RPi 5, pigpio for older models)
- Camera Module 3 support
- Troubleshooting slow networks and piwheels timeouts

**Quick deploy:**
```bash
cd backend
chmod +x start_backend.sh
./start_backend.sh
```

Enjoy your Smart Classroom automation system! 🚀
