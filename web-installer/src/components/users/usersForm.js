import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { Grid } from '@material-ui/core';
import { AddAccount } from 'utils/buttons';
import CssTextField from 'assets/jss/custom-jss/CssTextField';

const UsersForm = ({
  errors, values, handleSubmit, handleChange, saveUserDetails,
}) => (
  <div>
    <form onSubmit={handleSubmit} className="root">
      <Grid container spacing={3} justify="center" alignItems="center">
        <Grid item xs={12}>
          <CssTextField
            id="user-name-outlined-full-width"
            error={errors.username}
            value={values.username}
            label="Username"
            type="text"
            style={{ margin: 8 }}
            name="username"
            placeholder="PANIC Admin"
            helperText={errors.username ? errors.username : ''}
            onChange={handleChange}
            fullWidth
            margin="normal"
            InputLabelProps={{
              shrink: true,
            }}
            variant="outlined"
            autoComplete="off"
          />
        </Grid>
        <Grid item xs={12}>
          <CssTextField
            id="password-name-outlined-full-width"
            error={errors.password}
            value={values.password}
            label="Password"
            type="password"
            style={{ margin: 8 }}
            name="password"
            placeholder="*****************"
            helperText={errors.password ? errors.password : ''}
            onChange={handleChange}
            fullWidth
            margin="normal"
            InputLabelProps={{
              shrink: true,
            }}
            variant="outlined"
            autoComplete="off"
          />
        </Grid>
        <Grid item xs={8} />
        <Grid item xs={4}>
          <Grid
            container
            direction="row"
            justify="flex-end"
            alignItems="center"
          >
            <AddAccount
              disabled={Object.keys(errors).length !== 0}
              username={values.username}
              password={values.password}
              saveUserDetails={saveUserDetails}
            />
          </Grid>
        </Grid>
      </Grid>
    </form>
  </div>
);

UsersForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    username: PropTypes.string,
    password: PropTypes.string,
  }).isRequired,
  saveUserDetails: PropTypes.func.isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    username: PropTypes.string.isRequired,
    password: PropTypes.string.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
});

export default UsersForm;
