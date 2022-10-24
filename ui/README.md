# PANIC UI Documentation
PANIC UI is developed on top of 
[Simply VC UI](https://www.npmjs.com/package/@simply-vc/uikit) and uses
[Stencil](https://stenciljs.com/) as a web component compiler. 

An overview of what the UI consists of can be seen [here](#pages).

## Running the UI for production
Docker is used to run the UI for production.
If you have already installed all the pre-requisites from the 
[main README](../README.md), you can run the UI by typing the following 
command from PANIC's root directory:

```bash
docker-compose up --build -d ui
```

**Note**: If you have already built and ran PANIC using `docker-compose up --build -d`, then the UI is already running.

## Running the UI for development
Running the UI in a development server triggers a rebuild when the src files are
updated. To run the UI in this mode, you need to perform the following steps:

1. Update `DEV_MODE` to `true` in the `.env` file.
2. Navigate to the PANIC root directory and do `docker-compose up --build -d 
   api` to run the API service. This will enable the UI service to successfully 
   obtain data.
3. `cd ui`
4. `npm install`
5. `npm start`

This will start the development server at `http://localhost:{API_PORT}`.

**Note**: Make sure to change back `DEV_MODE` to `false` in the `.env` file before
running PANIC in production.

## Running tests
Stencil uses [Jest](https://jestjs.io/) (a general Javascript testing framework)
to handle unit tests, while Jest+[Puppeteer](https://pptr.dev/) (a Node library 
which provide a high-level API to control Chromium) is used for E2E tests.

If you want to run the tests, navigate to the `/ui` directory and do the
following:

```bash
npm install           # Install project dependencies
npm test              # Run E2E and unit tests
```

The following commands can be used to run the E2E tests or the 
unit tests separately:

```bash
npm run test.spec     # Run unit tests
npm run test.e2e      # Run E2E tests
```

Additionally, the following command can be used to run the tests in watch mode, 
which watches files for changes and rerun all tests when something changes:

```bash
npm run test.watch    # Run E2E and unit tests in watch mode
```

## Pages
The latest version of PANIC UI is able to detect whether PANIC has been set up or not.
If the node operator did not set up PANIC yet, the installer will be fired up.
This will enable the node operator to set up PANIC.

![](../docs/images/UI/installer.png)

When not in installation mode, the UI consists of three pages: the [Home Page](#home-page),
[Systems Overview Pages](#systems-overview) and the [Settings Pages](#settings-pages).

### Home Page
This page can be accessed at `https://{UI_ACCESS_IP}:UI_PORT`, where both `UI_ACCESS_IP`
and `UI_PORT` are values that can be obtained from the `.env` file. Note that `UI_PORT` is `3333` 
by default.

The homepage consists of two sections: [Dashboard Overview](#dashboard-overview)
and [Alerts Overview](#alerts-overview).

#### Dashboard Overview
This section depicts an overview of all current problems in the node 
operator's set-up being monitored by PANIC. A pie chart is displayed for each 
base chain (Cosmos, Substrate, Chainlink, General), showing the denomination of 
all problems for every sub-chain (ex. Polkadot, Regen, Binance Smart Chain) by 
severity. Problems in PANIC can be of three different severities; Critical, 
Warning and Error, thus the problems being displayed in this section have one of
these three severities. In addition to a pie chart, a table is displayed to show
more details about the current problems. Such details consist of a timestamp, 
description and severity.

![](../docs/images/UI/dashboard-overview-1.png)

For easier querying, the current problems can be filtered by sub-chains and 
severities, and sorted by severity, timestamp or description.

![](../docs/images/UI/dashboard-overview-2.png)

#### Alerts Overview
This section displays all the alerts that have been raised by PANIC so far in a 
table. Each entry in the table consists of the alert severity, timestamp and 
message. The alerts can also be filtered by sub-chains, severities, sources and 
date-time, and sorted by severity, timestamp or message.

![](../docs/images/UI/alerts-overview.png)

### Systems Overview
The aim of this page is to show the system metrics (CPU usage, storage usage and
more) of a particular base chain in a tabular way. Each metric value has the 
following colour coding:

- Green: If the metric value is not problematic
- Red: If the metric value is in a critical state
- Yellow: If the metric value is in a warning state

In addition to this, the node operator can also sort by the metric values.

![](../docs/images/UI/systems-overview.png)

This page can be accessed by clicking the `Networks` option found on the 
right-hand side of the PANIC UI header, and choosing the desired base chain.

### Settings Pages

The aim of the settings pages is to provide functionality for modifying the 
configurations which are set during the installation procedure. PANIC UI consists
of two settings pages, one for [Channels](#channels-settings-page) and one 
for the [Chains](#chains-settings-page).

#### Channels Settings Page

The channels settings page provides the following functionalities to the user:

1. The addition of new channels
2. The removal of already added channels
3. The modification of already added channels
4. The ability to map a channel to various subchains

The addition, removal and modification of channels can be done from this section:

![](../docs/images/UI/channels-settings-page-1.png)

The mapping procedure can be done from this section:

![](../docs/images/UI/channels-settings-page-2.png)

This page can be accessed by clicking the `Settings > Channels` option found on the 
right-hand side of the PANIC UI header.

#### Chains Settings Page

The chains settings page provides the following functionalities to the user:

1. The addition of new chains
2. The removal of already added chains
3. The modification of already added chains

![](../docs/images/UI/chains-settings-page.png)

This page can be accessed by clicking the `Settings > Chains` option found on the 
right-hand side of the PANIC UI header.

## Known Issues
- Because of a known bug in the Firefox Browser, when accessing PANIC UI from 
  Firefox you must accept the certificates on both `https://{UI_ACCESS_IP}:UI_PORT` and
  `https://{UI_ACCESS_IP}:API_PORT`. More information regarding this issue can be found 
  [here](https://stackoverflow.com/questions/51831652/cors-request-across-different-ports-did-not-succeed-on-firefox-but-works-on-chro).
- Similarly to the above, certificate validation cannot be bypassed in some cases when accessing
  PANIC UI from Chromium-based browsers. To bypass this check, click anywhere on the screen and 
  type `thisisunsafe`. More information regarding this issue can be found 
  [here](https://stackoverflow.com/questions/58802767/no-proceed-anyway-option-on-neterr-cert-invalid-in-chrome-on-macos).
- Due to an unavailable arm64 chromium binary used by puppeteer, by default, we 
  set the `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD` ENV variable to `true` in the 
  Dockerfile for PANIC UI. This should be set to `false` for UI development on
  non-ARM systems while chromium should be manually installed on ARM systems.

---
[Back to front page](../README.md)