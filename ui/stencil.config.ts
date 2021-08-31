import { Config } from '@stencil/core';
import { readFileSync } from 'fs';

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
};
