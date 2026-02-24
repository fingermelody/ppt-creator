import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    // 构建配置
    build: {
      outDir: 'dist',
      sourcemap: mode !== 'production',
      // 静态资源基础路径（SCF 部署时使用 CDN 地址）
      // 生产环境可通过环境变量 VITE_CDN_URL 配置
    },
    // 环境变量前缀
    envPrefix: 'VITE_',
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
        '/ws': {
          target: env.VITE_WS_URL || 'ws://localhost:8000',
          ws: true,
        },
      },
    },
  };
});
