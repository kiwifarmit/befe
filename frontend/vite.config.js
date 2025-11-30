import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://backend:8000',
        changeOrigin: true,
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/tests/setup.js'],
    coverage: {
      provider: 'v8',
      // Note: Coverage may have Node.js compatibility issues in some environments
      // Run tests with: npm test (coverage disabled)
      // To enable coverage, use: npm run test:coverage (may require Node.js update)
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'src/tests/',
        '**/*.config.js',
        '**/*.config.ts',
        'dist/',
        'coverage/',
        '*.{test,spec}.{js,ts}',
        'src/main.js',
        'src/router.js',
        'src/style.css',
      ],
            thresholds: {
              statements: 80,
              branches: 75,
              functions: 80,
              lines: 80,
            },
    },
  },
})
