/* eslint-disable react/jsx-no-bind */
import React from 'react';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import { CHANNELS_PAGE } from 'constants/constants';
import { LoginButton, StartNewButton } from 'utils/buttons';
import LoadConfig from 'containers/global/loadConfig';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import Data from 'data/welcome';

const StartDialog = ({
  values,
  errors,
  pageChanger,
  authenticate,
  checkForConfigs,
  loadUsersFromMongo,
  addUserRedux,
}) => {
  const [open, setOpen] = React.useState(false);

  // If authentication is accepted by the backend, change the page
  // to the channels setup and set authenticated.
  async function setAuthentication(authenticated) {
    if (authenticated) {
      authenticate(authenticated);
      // Load users from mongo into redux
      loadUsersFromMongo(addUserRedux);
      // Since it's authenticated we should check for configs
      const configResult = await checkForConfigs();
      if (configResult) {
        setOpen(true);
      } else {
        pageChanger({ page: CHANNELS_PAGE });
      }
    }
  }

  const handleClose = () => {
    setOpen(false);
    pageChanger({ page: CHANNELS_PAGE });
  };

  return (
    <div>
      <LoginButton
        username={values.username}
        password={values.password}
        disabled={Object.keys(errors).length !== 0}
        setAuthentication={setAuthentication}
      />
      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">{Data.dialog_title}</DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            {Data.dialog_description}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <StartNewButton onClick={handleClose} />
          <LoadConfig handleClose={handleClose} />
        </DialogActions>
      </Dialog>
    </div>
  );
};

StartDialog.propTypes = forbidExtraProps({
  checkForConfigs: PropTypes.func.isRequired,
  loadUsersFromMongo: PropTypes.func.isRequired,
  addUserRedux: PropTypes.func.isRequired,
  errors: PropTypes.shape({
    username: PropTypes.string,
    password: PropTypes.string,
  }).isRequired,
  values: PropTypes.shape({
    username: PropTypes.string.isRequired,
    password: PropTypes.string.isRequired,
  }).isRequired,
  pageChanger: PropTypes.func.isRequired,
  authenticate: PropTypes.func.isRequired,
});

export default StartDialog;
