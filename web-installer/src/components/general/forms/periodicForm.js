import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  TextField,
  Typography,
  Grid,
  Switch,
  FormControlLabel,
  Box,
} from '@material-ui/core';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import InputAdornment from '@material-ui/core/InputAdornment';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import Divider from '@material-ui/core/Divider';
import Data from 'data/general';

const PeriodicForm = ({ periodic, savePeriodicDetails }) => {
  const classes = useStyles();
  return (
    <div>
      <div className={classes.subsection}>
        <GridContainer justifyContent="center">
          <GridItem xs={12} sm={12} md={8}>
            <h1 className={classes.title}>{Data.periodic.title}</h1>
          </GridItem>
        </GridContainer>
      </div>
      <Typography variant="subtitle1" gutterBottom className="greyBackground">
        <Box m={2} p={3}>
          <p>{Data.periodic.description}</p>
        </Box>
      </Typography>
      <Divider />
      <Box py={4}>
        <form className="root">
          <Grid container spacing={3} justifyContent="center" alignItems="center">
            <Grid item xs={12} />
            <Grid item xs={2}>
              <Typography> Interval Seconds </Typography>
            </Grid>
            <Grid item xs={10}>
              <TextField
                value={periodic.time}
                autoComplete="off"
                type="text"
                name="time"
                placeholder="0"
                onChange={(event) => {
                  savePeriodicDetails({
                    time: event.target.value,
                    enabled: periodic.enabled,
                  });
                }}
                inputProps={{ min: 0, style: { textAlign: 'right' } }}
                /* eslint-disable-next-line react/jsx-no-duplicate-props */
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">Seconds</InputAdornment>
                  ),
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={2}>
              <Typography> Enabled </Typography>
            </Grid>
            <Grid item xs={1}>
              <FormControlLabel
                control={(
                  <Switch
                    checked={periodic.enabled}
                    onClick={() => {
                      savePeriodicDetails({
                        time: periodic.time,
                        enabled: !periodic.enabled,
                      });
                    }}
                    name="enabled"
                    color="primary"
                  />
                )}
                label=""
              />
            </Grid>
            <Grid item xs={9} />
          </Grid>
        </form>
      </Box>
    </div>
  );
};

PeriodicForm.propTypes = forbidExtraProps({
  periodic: PropTypes.shape({
    time: PropTypes.string,
    enabled: PropTypes.bool,
  }).isRequired,
  values: PropTypes.shape({
    time: PropTypes.string,
    enabled: PropTypes.bool,
  }).isRequired,
  savePeriodicDetails: PropTypes.func.isRequired,
});

export default PeriodicForm;
