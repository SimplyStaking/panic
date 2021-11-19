/* eslint-disable react/prop-types */
/* eslint-disable no-unused-vars */

import React, { useState, useEffect } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import {
  Typography,
  Box,
  Grid,
  Switch,
  FormControlLabel,
  Tooltip,
  MenuItem,
  Select,
  InputLabel,
  InputAdornment,
} from '@material-ui/core';
import IconButton from '@material-ui/core/IconButton';
import AddCircleIcon from '@material-ui/icons/AddCircle';
import CancelIcon from '@material-ui/icons/Cancel';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { defaultTheme, theme } from 'components/theme/default';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import CssTextField from 'assets/jss/custom-jss/CssTextField';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import { toggleDirty } from 'redux/actions/pageActions';

const WeiWatchersForm = ({
  saveWeiWatchersDetails,
  data,
  currentChain,
  chainConfig,
}) => {
  const classes = useStyles();
  const [weiWatchersList, setList] = useState([]);
  const [name, setName] = useState('');
  const [weiWatchersUrl, setWeiWatchersUrl] = useState('');
  const [monitorContracts, setMonitorContracts] = useState(false);
  const [customWeiWatchersNetworkInput, setcustomWeiWatchersNetworkInput] = useState('');
  const [customWeiWatchersURLInput, setcustomWeiWatchersURLInput] = useState('');
  const [customWeiWatchersInput, setCustomWeiWatchersInputActive] = useState(false);

  const createSendPayload = () => {
    const payload = {
      parent_id: currentChain,
      name,
      weiwatchers_url: weiWatchersUrl,
      monitor_contracts: monitorContracts,
    };
    saveWeiWatchersDetails(payload);
  };

  const handleNameChange = (event) => {
    setName(event.target.value);
    setCustomWeiWatchersInputActive(false);
  };

  const handleCustomWeiWatchersNetworkChange = (event) => {
    setcustomWeiWatchersNetworkInput(event.target.value);
  };

  const handleCustomWeiWatchersURLChange = (event) => {
    setcustomWeiWatchersURLInput(event.target.value);
  };

  const handleSetMonitor = (monitorContract) => {
    setMonitorContracts(monitorContract);
  };

  useEffect(() => {
    createSendPayload();
  }, [weiWatchersUrl, monitorContracts]);

  useEffect(() => {
    // weiWatchersUrlTemp is needed as setWeiWatchersUrl will call a state reloading
    // changing the array breaking the loop.
    let weiWatchersUrlTemp = '';
    for (let i = 0; i < weiWatchersList.length; i += 1) {
      if (weiWatchersList[i].network === name) {
        weiWatchersUrlTemp = weiWatchersList[i].url;
      }
    }
    setWeiWatchersUrl(weiWatchersUrlTemp);
  }, [name]);

  useEffect(() => {
    fetch(
      'https://raw.githubusercontent.com/VitalyVolozhinov/weiwatchers_mapping/main/mapping.json',
      {
        method: 'GET',
        headers: new Headers({
          Accept: 'application/vnd.github.cloak-preview',
        }),
      },
    )
      .then((res) => res.json())
      .then((response) => {
        setList(response.urls);
        setName(chainConfig.byId[currentChain].weiWatchers.name);
        setMonitorContracts(chainConfig.byId[currentChain].weiWatchers.monitor_contracts);
      })
      // eslint-disable-next-line no-console
      .catch((error) => console.log(error));
  }, []);

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <div className={classes.subsection}>
          <GridContainer justifyContent="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>{data.contractForm.title}</h1>
            </GridItem>
          </GridContainer>
        </div>
        <div className="greyBackground">
          <Typography variant="subtitle1" gutterBottom>
            <Box m={2} pt={3} px={3}>
              <p
                style={{
                  fontWeight: '350',
                  fontSize: '1.2rem',
                }}
              >
                {data.contractForm.description}
              </p>
            </Box>
          </Typography>
          <Divider />
          <Box m={2} p={3}>
            <form className="root">
              <Grid container spacing={3} justifyContent="flex-end">
                <Grid container item xs={12} spacing={3} justifyContent="flex-start">
                  <InputLabel id="network-select-label">Network Name</InputLabel>
                </Grid>
                <Grid item xs={customWeiWatchersInput ? 12 : 11}>
                  <Select
                    labelId="network-select-label"
                    id="network-names-customized-select"
                    fullWidth
                    style={{ margin: 6 }}
                    variant="outlined"
                    value={name}
                    onChange={handleNameChange}
                    inputProps={{
                      name: data.contractForm.nameHolder,
                      id: 'outlined-age-native-simple',
                    }}
                  >
                    <MenuItem value="">No Network</MenuItem>
                    {weiWatchersList.map((item, _) => (
                      <MenuItem key={item.network} value={item.network}>
                        {item.network}
                      </MenuItem>
                    ))}
                  </Select>
                </Grid>
                {!customWeiWatchersInput
                  ? (
                    <Grid container item xs={1} alignContent="center" justifyContent="center">
                      <IconButton
                        onClick={() => {
                          setCustomWeiWatchersInputActive(!customWeiWatchersInput);
                        }}
                      >
                        <AddCircleIcon />
                      </IconButton>
                    </Grid>
                  )
                  : ''}
                {!customWeiWatchersInput
                  ? (
                    <Grid item xs={12}>
                      <CssTextField
                        id="wei-watchers-url-outlined-full-width"
                        value={weiWatchersUrl}
                        disabled
                        label="WeiWatchers URL"
                        type="text"
                        style={{ margin: 8 }}
                        name="weiwatchers_url"
                        placeholder={data.contractForm.weiWatchersHolder}
                        fullWidth
                        margin="normal"
                        InputLabelProps={{
                          shrink: true,
                        }}
                        variant="outlined"
                        autoComplete="off"
                      />
                    </Grid>
                  )
                  : (
                    <Grid container spacing={1} xs={12} alignContent="center">
                      <Grid item xs={5}>
                        <CssTextField
                          id="custom-wei-watchers-network-outlined-full-width"
                          value={customWeiWatchersNetworkInput}
                          label="Custom Network Name"
                          type="text"
                          style={{ margin: 8 }}
                          name="customWeiWatchersNetworkInput"
                          placeholder="Enter custom network name."
                          onChange={handleCustomWeiWatchersNetworkChange}
                          fullWidth
                          margin="normal"
                          InputLabelProps={{
                            shrink: true,
                          }}
                          variant="outlined"
                          autoComplete="off"
                          InputProps={{
                            endAdornment: (
                              <InputAdornment position="end">
                                <MuiThemeProvider theme={theme}>
                                  <Tooltip title={data.contractForm.nameTip} placement="left">
                                    <InfoIcon />
                                  </Tooltip>
                                </MuiThemeProvider>
                              </InputAdornment>
                            ),
                          }}
                        />
                      </Grid>
                      <Grid item xs={5}>
                        <CssTextField
                          id="custom-wei-watchers-url-outlined-full-width"
                          value={customWeiWatchersURLInput}
                          label="Custom Network URL"
                          type="text"
                          style={{ margin: 8 }}
                          name="customWeiWatchersURLInput"
                          placeholder="Enter custom network URL."
                          onChange={handleCustomWeiWatchersURLChange}
                          fullWidth
                          margin="normal"
                          InputLabelProps={{
                            shrink: true,
                          }}
                          variant="outlined"
                          autoComplete="off"
                          InputProps={{
                            endAdornment: (
                              <InputAdornment position="end">
                                <MuiThemeProvider theme={theme}>
                                  <Tooltip title={data.contractForm.urlTip} placement="left">
                                    <InfoIcon />
                                  </Tooltip>
                                </MuiThemeProvider>
                              </InputAdornment>
                            ),
                          }}
                        />
                      </Grid>
                      <Grid container xs={1} alignContent="center" justifyContent="flex-end">
                        <Grid item alignContent="center" justifyContent="flex-end">
                          <IconButton
                            disabled={customWeiWatchersNetworkInput === '' || customWeiWatchersURLInput === ''}
                            onClick={() => {
                              if (customWeiWatchersNetworkInput !== '') {
                                setList(weiWatchersList.concat([{
                                  network: customWeiWatchersNetworkInput,
                                  url: customWeiWatchersURLInput,
                                }]));
                                setName(customWeiWatchersNetworkInput);
                                setCustomWeiWatchersInputActive(!customWeiWatchersInput);
                                setcustomWeiWatchersNetworkInput('');
                                setcustomWeiWatchersURLInput('');
                              }
                            }}
                          >
                            <AddCircleIcon />
                          </IconButton>

                        </Grid>
                      </Grid>
                      <Grid container xs={1} alignContent="center" justifyContent="center">
                        <Grid item alignContent="center">
                          <IconButton
                            onClick={() => {
                              setCustomWeiWatchersInputActive(!customWeiWatchersInput);
                            }}
                          >
                            <CancelIcon />
                          </IconButton>
                        </Grid>
                      </Grid>
                    </Grid>
                  )}
                <Grid container alignContent="flex-start" justifyContent="flex-start">
                  <Grid container item xs={3} alignContent="center" justifyContent="center">
                    <Typography> Enable Contract Monitoring </Typography>
                  </Grid>
                  <Grid item xs={1}>
                    <FormControlLabel
                      control={(
                        <Switch
                          checked={monitorContracts}
                          onClick={() => {
                            handleSetMonitor(!monitorContracts);
                          }}
                          name="monitor_contracts"
                          color="primary"
                        />
                      )}
                      label=""
                    />
                  </Grid>
                  <Grid container item xs={1} alignContent="center" justifyContent="flex-start">
                    <MuiThemeProvider theme={theme}>
                      <Tooltip title={data.contractForm.monitorContractTip} placement="left">
                        <InfoIcon />
                      </Tooltip>
                    </MuiThemeProvider>
                  </Grid>
                </Grid>
              </Grid>
            </form>
          </Box>
        </div>
      </div>
    </MuiThemeProvider>
  );
};

WeiWatchersForm.propTypes = {
  values: PropTypes.shape({
    name: PropTypes.string.isRequired,
    weiwatchers_url: PropTypes.string.isRequired,
    monitor_contracts: PropTypes.bool.isRequired,
    customWeiWatchersNetworkInput: PropTypes.string.isRequired,
  }).isRequired,
  data: PropTypes.shape({
    contractForm: PropTypes.shape({
      title: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      nameHolder: PropTypes.string.isRequired,
      nameTip: PropTypes.string.isRequired,
      weiWatchersUrlHolder: PropTypes.string.isRequired,
      monitorContractTip: PropTypes.string.isRequired,
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

export default WeiWatchersForm;
