import React from 'react';
import { makeStyles } from "@material-ui/core/styles";
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { TextField, Typography, Grid, Switch, FormControlLabel, Box } from '@material-ui/core';
import styles from "assets/jss/material-kit-react/views/landingPageSections/productStyle.js";
import InputAdornment from '@material-ui/core/InputAdornment';
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import Divider from '@material-ui/core/Divider';
import Data from 'data/general';

const useStyles = makeStyles(styles);

const PeriodicForm = ({values, periodic, savePeriodicDetails}) => {
  const classes = useStyles();

  return (
    <div>
      <div className={classes.subsection}>
        <GridContainer justify="center">
          <GridItem xs={12} sm={12} md={8}>
            <h1 className={classes.title}>
              {Data.periodic.title}
            </h1>
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
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={12} />
          <Grid item xs={2}>
            <Typography> Interval Seconds </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              value={periodic.time}
              autoComplete='off'
              type="text"
              name="time"
              placeholder="0"
              onChange={(event) => {
                savePeriodicDetails({
                  time: event.target.value,
                  enabled: periodic.enabled,
                });
              }}
              inputProps={{min: 0, style: { textAlign: 'right' }}}
                InputProps={{
                  endAdornment:
                    <InputAdornment position="end">
                      Seconds
                    </InputAdornment>,
                }}
              inputProps={{min: 0, style: { textAlign: 'right' }}}
              autoComplete='off'
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
