import React from 'react';
import PropTypes from 'prop-types';
import {
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  List,
  ListItem,
  Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CancelIcon from '@material-ui/icons/Cancel';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';

const TwilioTable = ({ twilios, removeTwilioDetails }) => {
  if (twilios.allIds.length === 0) {
    return <div />;
  }
  return (
    <Box pt={8}>
      <TableContainer component={Paper}>
        <Table className="greyBackground" aria-label="twilio-table">
          <TableHead>
            <TableRow>
              <StyledTableCell align="center">Twilio Name</StyledTableCell>
              <StyledTableCell align="center">Account Sid</StyledTableCell>
              <StyledTableCell align="center">Authentication Token</StyledTableCell>
              <StyledTableCell align="center">Twilio Phone Number</StyledTableCell>
              <StyledTableCell align="center">Numbers to dial</StyledTableCell>
              <StyledTableCell align="center">Delete</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.keys(twilios.byId).map((twilio) => (
              <StyledTableRow key={twilios.byId[twilio].id}>
                <StyledTableCell align="center">
                  {twilios.byId[twilio].channel_name}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {twilios.byId[twilio].account_sid}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {twilios.byId[twilio].auth_token}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {twilios.byId[twilio].twilio_phone_no}
                </StyledTableCell>
                <StyledTableCell align="center">
                  <div style={{ maxHeight: 70, overflow: 'auto' }}>
                    <List>
                      {twilios.byId[twilio].twilio_phone_numbers_to_dial_valid.map(
                        (number) => (
                          <ListItem key={number}>{number}</ListItem>
                        ),
                      )}
                    </List>
                  </div>
                </StyledTableCell>
                <StyledTableCell align="center">
                  <Button
                    onClick={() => {
                      removeTwilioDetails(twilios.byId[twilio]);
                    }}
                  >
                    <CancelIcon />
                  </Button>
                </StyledTableCell>
              </StyledTableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
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
