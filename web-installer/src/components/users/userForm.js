import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Button, Box, Typography, Grid,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const UserForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    values,
    handleSubmit,
    handleChange,
  } = props;

  return (
    <div>
      <form onSubmit={handleSubmit} className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={2}>
            <Typography> Username: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.username !== true}
              value={values.username}
              type="text"
              name="username"
              placeholder="panic_user_main"
              helperText={errors.username ? errors.username : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Password: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.password !== true}
              value={values.password}
              type="password"
              name="password"
              placeholder="*****************"
              helperText={errors.password ? errors.password : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={4}>
            <Grid container direction="row" justify="flex-end" alignItems="center">
              <Box px={2}>
                <Button
                  variant="outlined"
                  size="large"
                  disabled={!(Object.keys(errors).length === 0)}
                  type="submit"
                >
                  <Box px={2}>
                    Add
                  </Box>
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Grid>
      </form>
    </div>
  );
};

UserForm.propTypes = {
  errors: PropTypes.shape({
    username: PropTypes.string,
    password: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    username: PropTypes.string.isRequired,
    password: PropTypes.string.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
};

export default UserForm;
