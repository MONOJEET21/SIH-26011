// 🔴 CRITICAL — Cesium + Vite configuration

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'
import fs from 'node:fs'
import path from 'node:path'

const cesiumBuildPath = fileURLToPath(
  new URL(
    './node_modules/cesium/Build/Cesium',
    import.meta.url
  )
)

export default defineConfig({
  plugins: [
    react(),

    {
      name: 'cesium-static-assets',

      configureServer(server) {
        server.middlewares.use(
          '/cesium',
          (req, res, next) => {
            const requestPath = decodeURIComponent(
              req.url || '/'
            )

            const relativePath =
              requestPath.replace(/^\/+/, '')

            const filePath = path.join(
              cesiumBuildPath,
              relativePath
            )

            if (
              fs.existsSync(filePath) &&
              fs.statSync(filePath).isFile()
            ) {
              const ext =
                path.extname(filePath).toLowerCase()

              const contentTypes: Record<
                string,
                string
              > = {
                '.js': 'application/javascript',
                '.json': 'application/json',
                '.css': 'text/css',
                '.wasm': 'application/wasm',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.svg': 'image/svg+xml',
                '.gif': 'image/gif',
                '.bin':
                  'application/octet-stream',
              }

              res.setHeader(
                'Content-Type',
                contentTypes[ext] ||
                  'application/octet-stream'
              )

              fs.createReadStream(
                filePath
              ).pipe(res)

              return
            }

            next()
          }
        )
      },

      generateBundle() {
        const outputDir = path.resolve(
          'dist',
          'cesium'
        )

        fs.mkdirSync(
          outputDir,
          {
            recursive: true,
          }
        )

        fs.cpSync(
          cesiumBuildPath,
          outputDir,
          {
            recursive: true,
          }
        )
      },
    },
  ],

  define: {
    CESIUM_BASE_URL:
      JSON.stringify('/cesium'),
  },

  server: {
    port: 5173,
  },

  optimizeDeps: {
    include: ['cesium'],
  },
})