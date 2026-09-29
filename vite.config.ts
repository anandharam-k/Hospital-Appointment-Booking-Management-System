import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  return {
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    build: {
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, 'index.html'),
          index: path.resolve(__dirname, 'frontend/index.html'),
          login: path.resolve(__dirname, 'frontend/login.html'),
          register: path.resolve(__dirname, 'frontend/register.html'),
          doctors: path.resolve(__dirname, 'frontend/doctors.html'),
          booking: path.resolve(__dirname, 'frontend/booking.html'),
          confirmation: path.resolve(__dirname, 'frontend/confirmation.html'),
          appointments: path.resolve(__dirname, 'frontend/appointments.html'),
          history: path.resolve(__dirname, 'frontend/history.html'),
          admin_login: path.resolve(__dirname, 'frontend/admin-login.html'),
          admin_dashboard: path.resolve(__dirname, 'frontend/admin-dashboard.html'),
          admin_appointments: path.resolve(__dirname, 'frontend/admin-appointments.html'),
          doctors_management: path.resolve(__dirname, 'frontend/doctors-management.html'),
          availability: path.resolve(__dirname, 'frontend/availability.html'),
        },
      },
    },
    server: {
      port: 3000,
      host: '0.0.0.0',
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      // Do not modify—file watching is disabled to prevent flickering during agent edits.
      hmr: process.env.DISABLE_HMR !== 'true',
      // Disable file watching when DISABLE_HMR is true to save CPU during agent edits.
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
    },
  };
});
