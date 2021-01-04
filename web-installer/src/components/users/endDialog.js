import React from 'react';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import { SaveConfigButton, BackButton } from 'utils/buttons';
import SaveConfig from 'containers/global/saveConfig';
import Data from 'data/users';

const EndDialog = () => {
  const [open, setOpen] = React.useState(false);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <div>
      <SaveConfigButton onClick={handleOpen} />
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
          <BackButton onClick={handleClose} />
          <SaveConfig />
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default EndDialog;
