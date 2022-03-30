import { Config } from '@stencil/core';
import { sass } from '@stencil/sass';
import * as dotenv from "dotenv";

// Use the environmental variables from the .env file in root directory (local)
if (!process.env.UI_DASHBOARD_PORT && !process.env.API_PORT)
  dotenv.config({ path: "../.env" });

export const config: Config = {
  globalStyle: 'src/global/app.css',
  globalScript: 'src/global/app.ts',
  taskQueue: 'async',
  outputTargets: [
    {
      type: 'www',
      serviceWorker: null
    },
  ],
  devServer: {
    logRequests: true,
    port: parseInt(process.env.UI_DASHBOARD_PORT)
  },
  plugins: [
    sass()
  ],
  env: {
    API_PORT: process.env.API_PORT
  },
  testing: {
    "automock": false,
    "setupFiles": [
      "./setupJest.ts"
    ]
  }
};
