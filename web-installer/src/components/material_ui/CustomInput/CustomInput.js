/* eslint-disable react/jsx-props-no-spreading */
/* eslint-disable react/forbid-prop-types */
import React from 'react';
// nodejs library to set properties for components
import PropTypes from 'prop-types';
// nodejs library that concatenates classes
import classNames from 'classnames';
// @material-ui/core components
import FormControl from '@material-ui/core/FormControl';
import TextField from '@material-ui/core/TextField';
import useStyles from 'assets/jss/material-kit-react/components/customInputStyle';

export default function CustomInput(props) {
  const classes = useStyles();
  const {
    formControlProps,
    inputProps,
    placeHolder,
    error,
    value,
    helperText,
    handleChange,
    type,
    name,
  } = props;

  let formControlClasses;
  if (formControlProps !== undefined) {
    formControlClasses = classNames(
      formControlProps.className,
      classes.formControl,
    );
  } else {
    formControlClasses = classes.formControl;
  }
  return (
    <FormControl {...formControlProps} className={formControlClasses}>
      <TextField
        error={error}
        value={value}
        type={type}
        name={name}
        placeholder={placeHolder}
        helperText={helperText}
        onChange={handleChange}
        autoComplete="off"
        fullWidth
        InputProps={inputProps}
        FormHelperTextProps={{
          className: classes.helperText,
        }}
      />
    </FormControl>
  );
}

CustomInput.propTypes = {
  labelText: PropTypes.node.isRequired,
  labelProps: PropTypes.object.isRequired,
  id: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  placeHolder: PropTypes.string.isRequired,
  helperText: PropTypes.string.isRequired,
  handleChange: PropTypes.func.isRequired,
  inputProps: PropTypes.object.isRequired,
  formControlProps: PropTypes.object.isRequired,
  inputRootCustomClasses: PropTypes.string.isRequired,
  error: PropTypes.bool.isRequired,
  success: PropTypes.bool.isRequired,
  white: PropTypes.bool.isRequired,
  type: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
};
