import { Config } from '@stencil/core';
import { readFileSync } from 'fs';
import { sass } from '@stencil/sass';
import * as dotenv from "dotenv";

// Use the environmental variables from the .env file
dotenv.config({ path: "../.env" });

export const config: Config = {
  globalStyle: 'src/global/app.css',
  globalScript: 'src/global/app.ts',
  taskQueue: 'async',
  outputTargets: [
    {
      type: 'www',
      serviceWorker: null,
      baseUrl: 'https://localhost:3333',
      copy: [
        {
          src: "lib", warn: true
        }
      ]
    },
  ],
  devServer: {
    openBrowser: false,
    https: {
      cert: readFileSync('../certificates/cert.pem', 'utf8'),
      key: readFileSync('../certificates/key.pem', 'utf8')
    },
    logRequests: true
  },
  plugins: [
    sass()
  ],
  env: {
    API_IP: process.env.API_IP,
    API_PORT: process.env.API_PORT
  }
};
