/* eslint-disable react/jsx-props-no-spreading */
/* eslint-disable react/require-default-props */
/* eslint-disable react/forbid-prop-types */
import React from 'react';
import {
  Grid, AppBar, Tabs, Tab, Box,
} from '@material-ui/core';
import PropTypes from 'prop-types';
import {
  TelegramFormContainer,
  TelegramTableContainer,
} from 'containers/channels/telegramContainer';
import { SlackFormContainer, SlackTableContainer } from 'containers/channels/slackContainer';
import { TwilioFormContainer, TwilioTableContainer } from 'containers/channels/twilioContainer';
import { EmailFormContainer, EmailTableContainer } from 'containers/channels/emailContainer';
import {
  PagerDutyFormContainer,
  PagerDutyTableContainer,
} from 'containers/channels/pagerDutyContainer';
import {
  OpsGenieFormContainer,
  OpsGenieTableContainer,
} from 'containers/channels/opsGenieContainer';
import NavigationButtonContainer from 'containers/global/navigationButtonContainer';
import { CHAINS_PAGE, NEXT } from 'constants/constants';
import Data from 'data/channels';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import Card from 'components/material_ui/Card/Card';
import CardBody from 'components/material_ui/Card/CardBody';
import useStyles from 'assets/jss/material-kit-react/views/componentsSections/channelsStyle';
import Parallax from 'components/material_ui/Parallax/Parallax';
import DescriptionSection from 'components/channels/descriptionSection';
import CustomParticles from 'components/material_ui/Particles/ChannelParticles';

function TabPanel(props) {
  const {
    children, value, index, ...other
  } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box p={3}>
          {children}
        </Box>
      )}
    </div>
  );
}

TabPanel.propTypes = {
  children: PropTypes.node,
  index: PropTypes.any.isRequired,
  value: PropTypes.any.isRequired,
};

function a11yProps(index) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`,
  };
}

function ChannelsPage() {
  const classes = useStyles();
  // Internal state to keep track of clicked tabs
  const [value, setValue] = React.useState(0);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <div>
      <Parallax>
        <CustomParticles />
        <div
          style={{
            position: 'absolute',
            display: 'block',
            width: '100%',
            height: '100%',
            background: 'black',
            opacity: '0.8',
            top: '0',
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
          }}
        >
          <div className={classes.container}>
            <GridContainer>
              <GridItem>
                <div className={classes.brand}>
                  <h1 className={classes.title}>{Data.channels.title}</h1>
                </div>
              </GridItem>
            </GridContainer>
          </div>
        </div>
      </Parallax>
      <div className={classes.mainRaised}>
        <Card>
          <CardBody>
            <div className={classes.container}>
              <DescriptionSection />
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <div>
                    <AppBar
                      style={{
                        backgroundColor: '#363946',
                        borderRadius: '5px',
                        color: 'white',
                      }}
                      position="static"
                    >
                      <Tabs
                        value={value}
                        onChange={handleChange}
                        aria-label="simple tabs example"
                        centered
                        TabIndicatorProps={{
                          style: {
                            backgroundColor: 'white',
                          },
                        }}
                      >
                        <Tab label="Telegram" {...a11yProps(0)} />
                        <Tab label="Slack" {...a11yProps(1)} />
                        <Tab label="Email" {...a11yProps(2)} />
                        <Tab label="OpsGenie" {...a11yProps(3)} />
                        <Tab label="PagerDuty" {...a11yProps(4)} />
                        <Tab label="Twilio" {...a11yProps(5)} />
                      </Tabs>
                    </AppBar>
                    <TabPanel value={value} index={0}>
                      <TelegramFormContainer />
                      <TelegramTableContainer />
                    </TabPanel>
                    <TabPanel value={value} index={1}>
                      <SlackFormContainer />
                      <SlackTableContainer />
                    </TabPanel>
                    <TabPanel value={value} index={2}>
                      <EmailFormContainer />
                      <EmailTableContainer />
                    </TabPanel>
                    <TabPanel value={value} index={3}>
                      <OpsGenieFormContainer />
                      <OpsGenieTableContainer />
                    </TabPanel>
                    <TabPanel value={value} index={4}>
                      <PagerDutyFormContainer />
                      <PagerDutyTableContainer />
                    </TabPanel>
                    <TabPanel value={value} index={5}>
                      <TwilioFormContainer />
                      <TwilioTableContainer />
                    </TabPanel>
                  </div>
                </Grid>
                <Grid item xs={12} />
                <Grid item xs={5} />
                <Grid item xs={2}>
                  <NavigationButtonContainer text={NEXT} navigation={CHAINS_PAGE} />
                </Grid>
                <Grid item xs={5} />
                <Grid item xs={12} />
              </Grid>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default ChannelsPage;
