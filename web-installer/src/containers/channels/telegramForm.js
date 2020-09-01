import React, { Component } from 'react';
import TextField from '@material-ui/core/TextField';
import { withFormik } from 'formik';
import { connect } from 'react-redux';
import { addTelegram } from '../../redux/actions/channelActions';

class TelegramForm extends Component {
  render() {
    const {
      errors,
      handleSubmit,
      values,
      handleChange,
      handleBlur,
    } = this.props

    return (
      <div>
        <div>
          <form onSubmit={handleSubmit}>
            <TextField
              value={values.botToken}
              type="text"
              name="botToken"
              label="Bot Token"
              placeholder="123456789:ABCDEF-1234abcd5678efgh12345_abc123"
              onChange={handleChange}
              onBlur={handleBlur}
              fullWidth
            />
            <TextField
              value={values.chatID}
              type="text"
              name="chatID"
              label="Chat ID"
              placeholder="-123456789"
              onChange={handleChange}
              onBlur={handleBlur}
              fullWidth
            />
            <button type="submit" disabled={!errors}>
              Submit
            </button>
          </form>
        </div>
      </div>
    )
  }
}

const Form = withFormik({

  mapPropsToValues: () => ({ botToken: '', chatID: '' }),

  validate: values => {
    const errors = {}

    if (!values.botToken) {
      errors.botToken = 'Required'
    }
    if(!values.chatID) {
      // Validate if chat ID is numeric
      errors.chatID = 'Required'
    }
    console.log(errors);
    return errors;
  },

  handleSubmit: (values, { props }) => {
    const { saveTelegramDetails } = props
    const payload = { 
      botToken: values.botToken,
      chatID: values.chatID,
    }

    saveTelegramDetails(payload)
  },
})(TelegramForm)

function mapDispatchToProps(dispatch) {
  return {
    saveTelegramDetails: (details) => dispatch(addTelegram(details)),
  };
}

export default connect(null, mapDispatchToProps)(Form);