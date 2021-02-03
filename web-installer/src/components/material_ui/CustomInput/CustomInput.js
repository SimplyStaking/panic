import React from "react";
// nodejs library to set properties for components
import PropTypes from "prop-types";
// nodejs library that concatenates classes
import classNames from "classnames";
// @material-ui/core components
import FormControl from "@material-ui/core/FormControl";
import TextField from "@material-ui/core/TextField";
import useStyles from "assets/jss/material-kit-react/components/customInputStyle";

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

  var formControlClasses;
  if (formControlProps !== undefined) {
    formControlClasses = classNames(
      formControlProps.className,
      classes.formControl
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
        autoComplete='off'
        fullWidth
        InputProps={inputProps}
        FormHelperTextProps={{
          className: classes.helperText
        }}
      />
    </FormControl>
  );
}

CustomInput.propTypes = {
  labelText: PropTypes.node,
  labelProps: PropTypes.object,
  id: PropTypes.string,
  value: PropTypes.string,
  placeHolder: PropTypes.string,
  helperText: PropTypes.string,
  handleChange: PropTypes.func,
  inputProps: PropTypes.object,
  formControlProps: PropTypes.object,
  inputRootCustomClasses: PropTypes.string,
  error: PropTypes.bool,
  success: PropTypes.bool,
  white: PropTypes.bool
};
