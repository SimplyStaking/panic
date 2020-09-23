import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Button, List, ListItem,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CancelIcon from '@material-ui/icons/Cancel';

const TwilioTable = (props) => {
  const {
    twilios,
    removeTwilioDetails,
  } = props;

  if (twilios.allIds.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="greyBackground" aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Twilio Name</TableCell>
            <TableCell align="center">Account Sid</TableCell>
            <TableCell align="center">Authentication Token</TableCell>
            <TableCell align="center">Twilio Phone Number</TableCell>
            <TableCell align="center">Numbers to dial</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {Object.keys(twilios.byId).map((twilio) => (
            <TableRow key={twilios.byId[twilio].id}>
              <TableCell component="th" scope="row">
                {twilios.byId[twilio].configName}
              </TableCell>
              <TableCell align="center">{twilios.byId[twilio].accountSid}</TableCell>
              <TableCell align="center">{twilios.byId[twilio].authToken}</TableCell>
              <TableCell align="center">{twilios.byId[twilio].twilioPhoneNo}</TableCell>
              <TableCell align="center">
                <div style={{ maxHeight: 70, overflow: 'auto' }}>
                  <List>
                    {twilios.byId[twilio].twilioPhoneNumbersToDialValid.map((number) => (
                      <ListItem key={number}>
                        { number }
                      </ListItem>
                    ))}
                  </List>
                </div>
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeTwilioDetails(twilios.byId[twilio]); }}>
                  <CancelIcon />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

TwilioTable.propTypes = forbidExtraProps({
  twilios: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string.isRequired,
      configName: PropTypes.string.isRequired,
      accountSid: PropTypes.string.isRequired,
      authToken: PropTypes.string.isRequired,
      twilioPhoneNo: PropTypes.string.isRequired,
      twilioPhoneNumbersToDialValid: PropTypes.arrayOf(
        PropTypes.string.isRequired,
      ).isRequired,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeTwilioDetails: PropTypes.func.isRequired,
});

export default TwilioTable;
