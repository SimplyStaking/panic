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
import StepButtonContainer from '../../../../containers/chains/cosmos/stepButtonContainer';
import NavigationButtonContainer from '../../../../containers/global/navigationButtonContainer';
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
    handleSubmit,
    handleChange,
    values,
  } = props;

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
          <form onChange={handleSubmit} className={classes.root}>
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
                  placeholder="cosmos"
                  helperText={errors.chainName ? errors.chainName : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center" alignItems="right">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.chainName.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Box px={2}>
                  <NavigationButtonContainer
                    text={BACK}
                    navigation={CHAINS_PAGE}
                  />
                </Box>
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={!(Object.keys(errors).length === 0)}
                    text={NEXT}
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
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    chainName: PropTypes.string.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
};

export default ChainNameForm;
