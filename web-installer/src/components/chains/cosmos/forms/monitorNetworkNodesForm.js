import React from 'react';
import PropTypes from 'prop-types';
import {
  Typography,
  Box,
  Grid,
  Switch,
  FormControlLabel,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { defaultTheme } from 'components/theme/default';

const MonitorNetworkNodesForm = ({
  values,
  data,
  toggleMonitorNetworkNodes,
  setFieldValue,
  chainConfig,
  currentChain,
}) => (chainConfig.byId[currentChain].nodes.length !== 0
  ? (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <div className="greyBackground">
          <Typography variant="subtitle1" gutterBottom>
            <Box m={2} pt={3} px={3}>
              <p
                style={{
                  fontWeight: '350',
                  fontSize: '1.2rem',
                }}
              >
                {data.monitorNodesForm.description.replace('<chain_name>', chainConfig.byId[currentChain].chain_name)}
              </p>
            </Box>
          </Typography>
          <Divider />
          <Box m={2} p={3}>
            <form className="root">
              <Grid container spacing={3} justify="center" alignItems="center">
                <Grid item xs={3}>
                  <Typography> Monitor Network </Typography>
                </Grid>
                <Grid item xs={1}>
                  <FormControlLabel
                    control={(
                      <Switch
                        checked={values.monitor_network}
                        onClick={() => {
                          setFieldValue('monitor_network', !values.monitor_network);
                          const payload = {
                            parent_id: currentChain,
                            monitor_network: !values.monitor_network,
                          };
                          toggleMonitorNetworkNodes(payload);
                        }}
                        name="monitor_network"
                        color="primary"
                      />
                      )}
                    label=""
                  />
                </Grid>
              </Grid>
            </form>
          </Box>
        </div>
      </div>
    </MuiThemeProvider>
  )
  : '');

MonitorNetworkNodesForm.propTypes = {
  chainConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      nodes: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
  }).isRequired,
  currentChain: PropTypes.string.isRequired,
  values: PropTypes.shape({
    monitor_network: PropTypes.bool.isRequired,
  }).isRequired,
  toggleMonitorNetworkNodes: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  data: PropTypes.shape({
    monitorNodesForm: PropTypes.shape({
      description: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

export default MonitorNetworkNodesForm;
