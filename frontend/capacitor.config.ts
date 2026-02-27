import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.smartclassroom.app',
  appName: 'Smart Classroom',
  webDir: 'dist',
  server: {
    cleartext: true,
    androidScheme: 'http',   // prevent mixed-content blocks when fetching http://PI_IP:PORT
  }
};

export default config;
