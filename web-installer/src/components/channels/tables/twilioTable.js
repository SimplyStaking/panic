import React from 'react';
import PropTypes from 'prop-types';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  List,
  ListItem,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CancelIcon from '@material-ui/icons/Cancel';

const TwilioTable = ({ twilios, removeTwilioDetails }) => {
  if (twilios.allIds.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="greyBackground" aria-label="twilios table">
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
              <TableCell align="center">
                {twilios.byId[twilio].channel_name}
              </TableCell>
              <TableCell align="center">
                {twilios.byId[twilio].account_sid}
              </TableCell>
              <TableCell align="center">
                {twilios.byId[twilio].auth_token}
              </TableCell>
              <TableCell align="center">
                {twilios.byId[twilio].twilio_phone_no}
              </TableCell>
              <TableCell align="center">
                <div style={{ maxHeight: 70, overflow: 'auto' }}>
                  <List>
                    {twilios.byId[twilio].twilio_phone_numbers_to_dial_valid.map(
                      (number) => (
                        <ListItem key={number}>{number}</ListItem>
                      ),
                    )}
                  </List>
                </div>
              </TableCell>
              <TableCell align="center">
                <Button
                  onClick={() => {
                    removeTwilioDetails(twilios.byId[twilio]);
                  }}
                >
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

TwilioTable.propTypes = {
  twilios: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
      account_sid: PropTypes.string,
      auth_token: PropTypes.string,
      twilio_phone_no: PropTypes.string,
      twilio_phone_numbers_to_dial_valid: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeTwilioDetails: PropTypes.func.isRequired,
};

export default TwilioTable;
