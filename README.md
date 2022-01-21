# PANIC Monitoring and Alerting for Blockchains

**NOTE**: Substrate and Cosmos SDK blockchain monitoring and alerting are still in progress!

![PANIC Banner](./docs/images/PANIC_BANNER.png)

PANIC is an open source monitoring and alerting solution for Cosmos-SDK, Substrate and Chainlink based nodes by [Simply VC](https://simply-vc.com.mt/). The tool was built with user friendliness in mind, and comes with numerous features such as phone calls for critical alerts, a Web-UI installation process and Telegram/Slack commands for increased control over your alerter.

We are sure that PANIC will be beneficial for node operators and we look forward for feedback. Feel free to read on if you are interested in the design of the alerter, if you wish to try it out, or if you would like to support and contribute to this open source project.

## Design and Features

If you want to dive into the design and feature set of PANIC [click here](./docs/DESIGN_AND_FEATURES.md).

## Installation Guide

We will now guide you through the steps required to get PANIC up and running. We recommend that PANIC is installed on a Linux system and that everything needed in the [Requirements](#requirements) section is done before the installation procedure is started.

As you will notice below, PANIC supports many alerting channels. It is recommended that at least one of the alerting channels mentioned in the requirements section is set-up.

### Requirements
- **Git** command line tools. [Click here](#git-installation) if you want a guide to set it up.
- **Docker** and **Docker Compose**: This installation guide uses Docker and Docker Compose to run PANIC, these will need to be installed. [Click here](#docker-and-docker-compose-installation) if you want a guide to set it up.

#### Optional
- **Node Exporter**, this will be used to monitor the systems on which the nodes are running. If you want your nodes' systems to be monitored this step is no longer optional. Node Exporter must also be installed on each machine that you want to monitor. [Click here](#node-exporter-setup) if you want a guide to set it up.
- **Telegram account and bots**, for Telegram alerts and commands. [Click here](#telegram-setup) if you want a guide to set it up.
- **Slack account and app**, for Slack alerts and commands. [Click here](#slack-setup) if you want a guide to set it up.
- **Twilio account**, for phone call alerts. [Click here](#twilio-setup) if you want a guide to set it up.
- **PagerDuty account**, for notifications and phone call alerts. [Click here](#pagerduty-setup) if you want a guide to set it up.
- **OpsGenie account**, for notifications and phone call alerts. [Click here](#opsgenie-setup) if you want a guide to set it up.

### Installation

**TIP**: If your terminal is telling you that you do not have permissions to run a command try adding `sudo` to your command e.g, `sudo docker --version` this will run your command as root. If you have any issues during the installation procedure check out the [FAQ](./docs/FAQ.md) section.

#### Git Installation

**Note**: Skip this step if Git is already installed.

Firstly we will install and verify your Git installation.

```bash
# Install Git
sudo apt install git

# Verify that git is now installed
git --version
```

This should give you the current version of git that has been installed.

#### Docker and Docker Compose Installation

**Note**: Skip this step if Docker and Docker Compose is already installed.

First, install Docker and Docker Compose by running these commands on your terminal.

```bash
# Install docker and docker-compose
curl -sSL https://get.docker.com/ | sh
sudo apt install docker-compose -y

# Confirm that installation successful
docker --version
docker-compose --version
```

These should give you the current versions of the software that have been installed. At the time of writing the current working docker version is `20.10.10` while the docker-compose version is `1.25.0`. If you have a different version that doesn't allow you to run the `docker-compose.yml` file then either upgrade your versions of `docker` and `docker-compose` or change the version inside of the `docker-compose.yml` file which is currently at `3.7`.

#### Configuration Setup

```bash
# Clone the panic repository and navigate into it
git clone https://github.com/SimplyVC/panic
cd panic
```

Now that you're in inside the PANIC directory, open up the .env file and change the fields of `INSTALLER_USERNAME` and `INSTALLER_PASSWORD` to your preferred but secure choice. This is to ensure that when configuring PANIC through the web-installer no one else can access it.

```bash
# This will access the .env file on your terminal
nano .env
```

Once inside change `admin` and `password` to different values. Here is an example:

```ini
INSTALLER_USERNAME=panic_operator
INSTALLER_PASSWORD=wowthisisasecurepassword
```

Then to exit hit the following keys:
 1. To exit your .env file: <kbd>CTRL</kbd> + <kbd>X</kbd>
 2. To select yes to save your modified file: <kbd>Y</kbd>
 3. To confirm the file name and exit: <kbd>ENTER</kbd>

**Running PANIC**

Once you have everything setup, you can start PANIC by running the below command:

```bash
docker-compose up -d --build
```

**NOTE** If build fails run these commands to clean your `docker` images and try again. Please be aware that these commands will also stop other `docker` images that you might have running on your system.

```bash
docker-compose kill
docker system prune -a --volumes
docker-compose up -d --build
```

Now you will have to configure PANIC to monitor your nodes and systems as well as give it the channels to alert you through. To do this you will have to navigate to the running web-installer. This can be found on 
`https://{IP_ADDRESS}:8000`, and if you're running it locally then it can be found here `https://localhost:8000`. The installer will first ask you to enter the username and password. These are `INSTALLER_USERNAME` and `INSTALLER_PASSWORD` which you have changed previously. Make sure you type **HTTPS** if you're getting an error when accessing the installer on your browser.

After you set-up PANIC to your liking, the Web-Installer will save these details in the form of configuration files inside the `config` folder. For correct behavior, these configuration files should never be modified. If you would like to edit them at some point, we suggest to re-run the web-installer again. The web-installer will ask you if you want to start a fresh install or load your old configuration.

PANIC will automatically read these configuration files and begin monitoring the data sources. To check that this is the case we suggest running the command `docker-compose logs -f alerter` and `docker-compose logs -f health-checker`. By this you can see the different components starting up. If you have set-up telegram/slack commands we suggest that you enter the command `/status` to check that all PANIC components are running. If you really want to check that PANIC is up and running, we suggest that you check that all the logs inside `panic/alerter/logs` have no errors.

Congratulations you should have PANIC up and running!

### Optional Installations

#### Node Exporter Setup

**Note**: This needs to be done on every host machine that you want the system metrics monitored and alerted on.

[Github](https://github.com/prometheus/node_exporter) link to most recent version of Node Exporter we support.

##### Create a Node Exporter user for running the exporter:

```bash
sudo useradd --no-create-home --shell /bin/false node_exporter
```

##### Download and extract the latest version of Node Exporter:

```bash
wget https://github.com/prometheus/node_exporter/releases/download/v0.18.1/node_exporter-0.18.1.linux-amd64.tar.gz
tar -xzvf node_exporter-0.18.1.linux-amd64.tar.gz
```

##### Send the executable to /usr/local/bin:

```bash
sudo cp node_exporter-0.18.1.linux-amd64/node_exporter /usr/local/bin/
```

##### Give the Node Exporter user ownership of the executable:

```bash
sudo chown node_exporter:node_exporter /usr/local/bin/node_exporter
```

##### Perform some cleanup and create and save a Node Exporter service with the below contents:

```bash
sudo rm node_exporter-0.18.1.linux-amd64 -rf
sudo nano /etc/systemd/system/node_exporter.service
```
```ini
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter
 
[Install]
WantedBy=multi-user.target
```

##### Reload systemctl services list, start the service and enable it to have it start on system restart:

```bash
sudo systemctl daemon-reload
sudo systemctl start node_exporter
sudo systemctl enable node_exporter
sudo systemctl status node_exporter
```

Check if the installation was successful by checking if {NODE_IP}:{PORT}/metrics is accessible from a web browser.

[Back to the Requirements](#requirements)

### Telegram Setup

1. To create a free **Telegram account**, download the [app for Android / iPhone](https://telegram.org) and sign up using your phone number. 
2. To create a **Telegram bot**, add [@BotFather](https://telegram.me/BotFather) on Telegram, press Start, and follow the below steps:
    1. Send a `/newbot` command and fill in the requested details, including a bot name and username.
    2. Take a note of the API token, which looks something like `111111:AAA-AAA111111-aaaaa11111`.
    3. Access the link `t.me/<username>` to your new bot given by BotFather and press Start.
    4. Access the link `api.telegram.org/bot<token>/getUpdates`, replacing `<token>` with the bot's API token. This gives a list of the bot's activity, including messages sent to the bot.
    5. The result section should contain at least one message, due to us pressing the Start button. If not, sending a `/start` command to the bot should do the trick. Take a note of the `"id"` number in the `"chat"` section of this message.
    6. One bot is enough for now. You can repeat these steps to create more bots.

**At the end, you should have:**
1. A Telegram account
2. A Telegram bot *(at least one)*
3. The Telegram bot's API token *(at least one)*
4. The chat ID of your chat with the bot *(at least one)*

[Back to the Requirements](#requirements)

### Slack Setup

1. [Login](https://slack.com/signin) to Slack using an existing account or [sign up](https://slack.com/get-started) for a **Slack account**.
2. If you are not in a workspace, join a workspace from an invite or [create](https://slack.com/create) a workspace.
3. Create a channel within the workspace which will be used to receive notifications and interact with the Slack Bot.
3. To create a **Slack app**, visit the [slack apps page](https://api.slack.com/apps) and press `Create New App`. The steps below are to be used to set-up the app, which includes gathering the app-level token, the bot token, and the channel ID:
    1. Click the `From an app manifest` option in the pop-up window.
    2. Select the `workspace` which contains the target channel.
    3. Copy the [YAML app manifest](./slack_manifest.yaml) provided within the PANIC repository and overwrite the default YAML provided by Slack.
    4. Click `Next` followed by `Create`.
    5. Scroll down to the `App-Level Tokens` section and click `Generate Token and Scopes`.
    6. Enter a `Token Name` (this is just a reference to the token which can be set to anything), add the `connections:write` scope, and click `Generate`.
    7. Take note of the Token generated, this is the App-Level Token.
    8. Go to the 'Install App' setting (left pane) and click `Install to Workspace`, followed by `Allow`.
    9. Go to the 'OAuth & Permissions' feature (left pane) and take note of the `Bot User OAuth Token`.
    10. Add the newly created `PANIC Notifications` app to the target channel by typing `/add` within the channel and selecting `Add apps to this channel`.
4. Go to the Slack client, right click the name of the target slack channel within the list of channels (left pane), click `Open channel details`, and take note of the Channel ID *(found at the bottom)*.

**At the end, you should have:**
1. Access to a Slack workspace
2. A Slack account, app, and channel
3. The Slack app's Bot User Token and App-Level Token
4. The ID of the target slack channel

[Back to the Requirements](#requirements)

### Twilio Setup

- To create a free trial **Twilio account**, head to the [try-twilio page](https://www.twilio.com/try-twilio) and sign up using your details.
- Next, three important pieces of information have to be obtained:
    1. Navigate to the [account dashboard page](https://www.twilio.com/console).
    2. Click the 'Get a Trial Number' button in the dashboard to generate a unique number.
    3. Take a note of the (i) Twilio phone number.
    4. Take a note of the (ii) account SID and (iii) auth token.
- All that remains now is to add a number that Twilio is able to call:
    1. Navigate to the [Verified Caller IDs page](https://www.twilio.com/console/phone-numbers/verified).
    2. Press the red **+** to add a new personal number and follow the verification steps.
    3. One number is enough for now. You can repeat these steps to verify more than one number.

**At the end, you should have:**
1. A Twilio phone number.
2. The account SID, available in the account dashboard.
3. The auth token, available in the account dashboard.
4. A verified personal phone number *(at least one)*

If you wish to explore more advanced features, PANIC also supports configurable [TwiML](https://www.twilio.com/docs/voice/twiml); instructions which can re-program Twilio to do more than just call numbers. By default, the TwiML is set to [reject calls](https://www.twilio.com/docs/voice/twiml/reject) as soon as the recipient picks up, without any charges. This can be re-configured from the twilio section of the `.env` file to either a URL or raw TwiML instructions.

[Back to Requirements](#requirements)

### PagerDuty Setup

- It is assumed that a user has previously used **PagerDuty** and has a **PagerDuty Account**, if not head to the [PagerDuty sign-up page](https://www.pagerduty.com/sign-up/) and sign up using your details.
- First you need to add a service, and get two important pieces of information.
  - Firstly the integration key:
    1. Navigate to the `+ Add new services` button on the right side of the page
      1. Name your service and give it a description
      2. In the `Integration Settings` select `Use our API directly` and choose `Events API v2`,
      3. The rest can be configured to your preferences.
      4. Click `Add Service`
    2. You will be taken to a new page, where you need to navigate to the `Integrations` tab and take note of the (i)`Integration Key`.
  - Secondly the API Token
    1. Navigate to `https:/{YOUR_SUBDOMAIN}.pagerduty.com/api_keys`.
    2. Click `Create New API Key`
    3. Give it a description (This can be anything you want)
    4. Click `Create Key` and take note of (ii)`API Key` value.

**At the end, you should have:**
1. The Integration Key
2. The API token

These will be used later in the Web-Installer to be saved in the configuration files.

**Note** You can also install an app for Android / iPhone as well as setup your phone number to receive alerts.

[Back to Requirements](#requirements)

### Opsgenie Setup

- It is assumed that a user has previously used **Opsgenie** and has an **Opsgenie Account**, if not head to the [Opsgenie sign-up page](https://www.atlassian.com/software/opsgenie/try) and sign up using your details.
- Let's go through the process of setting up your API.
    1. Click on `Integrate with Jira and your monitoring tools` on your home page.
    2. Make sure `API` integration is selected
    3. Click `Save integrations`
    4. Click `Now, go to the integrations page and explore`
    5. Navigate to the API you just set up and take note of `API Key`.

**At the end, you should have:**
1. The API token

These will be used later in the Web-Installer to be saved in the configuration files.

**Note** You can also install the Opsgenie app for Android / iPhone as well as setup your phone number to receive calls.

[Back to Requirements](#requirements)

### Replacing SSL certificates (recommended)

Apply your own SSL certificate signed by a certificate authority. The SSL certificate (cert.pem) and the key (key.pem) should be placed in the `panic/certificates` folder, and they should replace the existing dummy files. Note that these dummy files were given just for convenience as the Installer server won't start without them, however, for maximum security these must be replaced.

We suggest reading [this](https://nodejs.org/en/knowledge/HTTP/servers/how-to-create-a-HTTPS-server/) for more details on SSL certificates, and how to generate a self signed certificate in case you do not want to obtain a certificate signed by a certificate authority. However, for maximum security, the self signed certificate option is not recommended.

### Running the PANIC test suite
If you want to run the tests for PANIC do the following:
```bash
docker-compose kill  # To stop any running containers (to avoid conflicts)
docker-compose -p panic-tests -f docker-compose-tests.yml up --build -d  # To build the tests container
docker-compose -p panic-tests -f docker-compose-tests.yml logs test-suite  # To see the result of the tests
docker-compose -p panic-tests -f docker-compose-tests.yml kill  # To remove test environment
```

## Support and Contribution

On top of the additional work that we will put in ourselves to improve and maintain the tool, any support from the community through development will be greatly appreciated. 

## Who We Are

Simply VC runs highly reliable and secure infrastructure in our own datacentre in Malta, built with the aim of supporting the growth of the blockchain ecosystem. Read more about us on our website and Twitter:

- Simply VC website: <https://simply-vc.com.mt/>
- Simply VC Twitter: <https://twitter.com/Simply_VC>

---
