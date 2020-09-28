import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Typography, Box, Grid, Tooltip,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { makeStyles, createMuiTheme, MuiThemeProvider } from '@material-ui/core/styles';
import {
  NEXT, NODES_STEP, BACK, CHAINS_PAGE,
} from '../../../../constants/constants';
import NavigationButton from '../../../global/navigationButton';
import Data from '../../../../data/chains';

const defaultTheme = createMuiTheme();
const theme = createMuiTheme({
  overrides: {
    MuiTooltip: {
      tooltip: {
        fontSize: '1em',
        color: 'white',
        backgroundColor: 'black',
      },
    },
  },
});

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const ChainNameForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    handleChange,
    values,
  } = props;

  // NextStep function will save the chain name, step changer
  function nextStep(step) {
    const {
      stepChanger, saveChainDetails, currentChain, updateChainDetails,
    } = props;
    // If there is a current chain assigned already, overwrite the value
    // Otherwise add a new chain name.
    if (currentChain) {
      // Create a payload with the old ID but new chain name
      const payload = {
        id: currentChain,
        chainName: values.chainName,
      };
      // Update the global State
      updateChainDetails(payload);
    } else {
      // Create a payload with a new chain name, the unique ID will be set in
      // the action.
      const payload = {
        chainName: values.chainName,
      };
      // Update the global state
      saveChainDetails(payload);
    }
    // Update the step in the form which is being shown
    stepChanger({ step });
  }

  // Next page is infact returning back to the Chains Setings Page
  // but keeping the name the same for consistency
  function nextPage(page) {
    const { pageChanger, clearChainId } = props;
    // Clear the current chain, id we are working on.
    clearChainId();
    // Change page
    pageChanger({ page });
  }

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{Data.chainName.description}</p>
          </Box>
        </Typography>
        <Divider />
        <Box py={4}>
          <form onSubmit={(e) => { e.preventDefault(); }} className={classes.root}>
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> Chain Name: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={!errors.chainName !== true}
                  value={values.chainName}
                  type="text"
                  name="chainName"
                  placeholder="polkadot"
                  helperText={errors.chainName ? errors.chainName : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.chainName.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Box px={2}>
                  <NavigationButton
                    disabled={false}
                    nextPage={nextPage}
                    buttonText={BACK}
                    navigation={CHAINS_PAGE}
                  />
                </Box>
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={2}>
                <Box px={2}>
                  <NavigationButton
                    disabled={!(Object.keys(errors).length === 0)}
                    nextPage={nextStep}
                    buttonText={NEXT}
                    navigation={NODES_STEP}
                  />
                </Box>
              </Grid>
            </Grid>
          </form>
        </Box>
      </div>
    </MuiThemeProvider>
  );
};

ChainNameForm.propTypes = {
  errors: PropTypes.shape({
    chainName: PropTypes.string,
  }).isRequired,
  values: PropTypes.shape({
    chainName: PropTypes.string.isRequired,
  }).isRequired,
  currentChain: PropTypes.string.isRequired,
  saveChainDetails: PropTypes.func.isRequired,
  stepChanger: PropTypes.func.isRequired,
  updateChainDetails: PropTypes.func.isRequired,
  handleChange: PropTypes.func.isRequired,
  pageChanger: PropTypes.func.isRequired,
  clearChainId: PropTypes.func.isRequired,
};

export default ChainNameForm;
